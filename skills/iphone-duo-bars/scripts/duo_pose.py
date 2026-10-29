#!/usr/bin/env python3
"""Put a booted iPhone Duo simulator into a pose and screenshot it.

Apple ships no command that sets a pose: `simctl` has no hinge or rotation
subcommand, and `xcrun devicectl device orientation set` prints the new
orientation, exits 0 and changes nothing on an iPhone Duo. This script drives the
third-party `hinge` CLI (https://github.com/artemnovichkov/hinge, MIT, 0.3.0 or
later), which posts the private events Device Hub's hinge slider and rotate
control send, and wraps it with the checks it lacks:

- it acts on an iPhone Duo simulator only, chosen by device type and always
  passed to `hinge` with `-d`;
- it moves the hinge in a short sweep, never a jump: duoctl
  (https://github.com/skarol/duoctl) reports that a jump straight between closed
  and open can stop the iOS 27.1 runtime from switching displays until the
  simulator is recreated;
- after each move it waits until `hinge posture` reports the angle and the
  rotation of the display that hosts the app. The angle comes from CoreMotion,
  because the `devicectl` of Xcode 27.2 has no `motion` subcommand;
- `shoot` captures both displays by screen ID — the default display is not
  stable — records which one hosts the app, and puts the hinge and the
  orientation back where it found them.

This changes simulator state. Run it in the verification phase, after the
developer has approved it, never during a read-only scan.

    python3 scripts/duo_pose.py status
    python3 scripts/duo_pose.py set tabletop
    python3 scripts/duo_pose.py shoot /tmp/poses --poses closed,flat,flat-portrait
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

DUO_TYPE_MARKER = "iPhone-Duo"


@dataclass(frozen=True)
class Pose:
    angle: float
    orientation: str | None  # the device orientation `hinge orient` takes; None keeps the current one
    rotation: str | None  # what the display that hosts the app then reports
    row: str  # the row in references/pose-test-matrix.md


# Measured 2026-10-29 on Xcode 27.1 (27A9269), iOS 27.1 runtime, with an app that supports
# portrait and both landscapes. The inner display sits a quarter turn from the outer one,
# so one device orientation rotates them differently: device portrait gives the inner
# display a landscape interface (rot90), device landscape-left a portrait one (rot0).
POSES = {
    "closed": Pose(0.0, "portrait", "rot0", "P1"),
    "closed-landscape": Pose(0.0, "landscape-left", "rot270", "P2"),  # vertical bar on the leading edge
    "closed-landscape-flipped": Pose(0.0, "landscape-right", "rot90", "P2"),  # vertical bar trailing
    "flat": Pose(180.0, "portrait", "rot90", "P3"),
    "flat-portrait": Pose(180.0, "landscape-left", "rot0", "P4"),
    "book": Pose(90.0, "portrait", "rot90", "P5"),
    "tabletop": Pose(90.0, "landscape-left", "rot0", "P6"),
}
DEFAULT_SHOTS = "closed,closed-landscape,closed-landscape-flipped,flat,book,tabletop,flat-portrait"
# The simulator reports a smoothed, quantised angle (179° came back as 174.1°),
# so "reached" means within this many degrees of the request.
DEFAULT_TOLERANCE = 6.0
DEFAULT_SWEEP = 0.6
# Screen IDs from the iPhone Duo device profile (`simctl io <udid> enumerate`). Always name
# the display: without --display, simctl picked the inner display one run and the outer
# the next.
DISPLAYS = {"inner": ["--display=3"], "outer": ["--display=1"]}
MIN_HINGE = (0, 3, 0)
INSTALL_HINT = "brew install artemnovichkov/tap/hinge   (or set HINGE_BIN to a checkout's bin/hinge)"


class PoseError(Exception):
    """A precondition failed; the message says what to do."""


@dataclass(frozen=True)
class Device:
    udid: str
    name: str
    booted: bool


@dataclass(frozen=True)
class Posture:
    angle: float | None
    orientation: str | None
    display: str | None  # "outer" or "inner": the display that hosts the app
    rotation: str | None  # that display's rotation


def duo_devices(simctl_json: dict) -> list[Device]:
    """Every iPhone Duo simulator in `simctl list devices --json` output."""
    found = []
    for devices in simctl_json.get("devices", {}).values():
        for device in devices:
            if DUO_TYPE_MARKER in device.get("deviceTypeIdentifier", ""):
                found.append(Device(device["udid"], device["name"], device.get("state") == "Booted"))
    return found


def pick_device(devices: list[Device], wanted: str | None) -> Device:
    """The iPhone Duo to act on: the one named, or the only booted one."""
    if wanted:
        matches = [d for d in devices if wanted in (d.udid, d.name)]
        if not matches:
            raise PoseError(f"no iPhone Duo simulator matches {wanted!r}")
        booted = [d for d in matches if d.booted]
        if not booted:
            raise PoseError(f"{matches[0].name} is not booted: xcrun simctl boot {matches[0].udid}")
        return booted[0]
    booted = [d for d in devices if d.booted]
    if not booted:
        if not devices:
            raise PoseError("no iPhone Duo simulator exists; it needs Xcode 27.1 and the iOS 27.1 runtime")
        raise PoseError(f"no iPhone Duo simulator is booted: xcrun simctl boot {devices[0].udid}")
    if len(booted) > 1:
        names = ", ".join(f"{d.name} ({d.udid})" for d in booted)
        raise PoseError(f"several iPhone Duo simulators are booted, pick one with --device: {names}")
    return booted[0]


def parse_posture(text: str) -> Posture:
    """The state `hinge posture --json` printed."""
    data = json.loads(text)
    active = next((d for d in data.get("displays", []) if d.get("active")), None)
    return Posture(
        angle=data.get("angle"),
        orientation=data.get("orientation"),
        display=None if active is None else ("outer" if active.get("primary") else "inner"),
        rotation=None if active is None else active.get("rotation"),
    )


def parse_version(text: str) -> tuple[int, ...] | None:
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", text)
    return tuple(int(part) for part in match.groups()) if match else None


def pose_for(name: str) -> Pose:
    """The pose for a name, or a bare angle from 0 to 180 that keeps the orientation."""
    if name in POSES:
        return POSES[name]
    try:
        degrees = float(name)
    except ValueError:
        raise PoseError(f"unknown pose {name!r}: use {', '.join(POSES)} or 0–180") from None
    if not 0 <= degrees <= 180:
        raise PoseError(f"angle {degrees} is outside 0–180")
    return Pose(degrees, None, None, "")


def reached(target: float, actual: float | None, tolerance: float = DEFAULT_TOLERANCE) -> bool:
    return actual is not None and abs(actual - target) <= tolerance


def in_pose(pose: Pose, posture: Posture | None, tolerance: float = DEFAULT_TOLERANCE) -> bool:
    if posture is None or not reached(pose.angle, posture.angle, tolerance):
        return False
    return pose.rotation is None or posture.rotation == pose.rotation


class Simulator:
    """The commands this script runs. Kept in one place so tests can see them."""

    def __init__(self, hinge: str, udid: str, sweep: float = DEFAULT_SWEEP):
        self.hinge = hinge
        self.udid = udid
        self.sweep = sweep

    def posture(self) -> Posture | None:
        result = run([self.hinge, "-d", self.udid, "posture", "--json"], check=False)
        if result.returncode != 0:
            return None
        try:
            return parse_posture(result.stdout)
        except ValueError:
            return None

    def move_hinge(self, degrees: float, current: float | None) -> None:
        if current is None:
            run([self.hinge, "-d", self.udid, "set", f"{degrees:g}"])
        elif abs(current - degrees) > 0.5:
            run([self.hinge, "-d", self.udid, "sweep", f"{current:g}", f"{degrees:g}", f"{self.sweep:g}"])

    def orient(self, orientation: str) -> None:
        run([self.hinge, "-d", self.udid, "orient", orientation])

    def wait_for(self, pose: Pose, timeout: float, tolerance: float) -> Posture | None:
        deadline = time.monotonic() + timeout
        posture = None
        while time.monotonic() < deadline:
            posture = self.posture()
            if in_pose(pose, posture, tolerance):
                return posture
            time.sleep(0.5)
        return posture

    def screenshot(self, display: str, path: Path) -> None:
        run(["xcrun", "simctl", "io", self.udid, "screenshot", *DISPLAYS[display], str(path)])

    def relaunch(self, bundle_id: str) -> None:
        run(["xcrun", "simctl", "terminate", self.udid, bundle_id], check=False)
        run(["xcrun", "simctl", "launch", self.udid, bundle_id])


def run(command: list[str], check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(command, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise PoseError(f"{' '.join(command)} failed: {(result.stderr or result.stdout).strip()}")
    return result


def find_hinge(explicit: str | None) -> str:
    candidate = explicit or os.environ.get("HINGE_BIN") or shutil.which("hinge")
    if not candidate or not Path(candidate).exists():
        raise PoseError(f"the hinge CLI is not installed: {INSTALL_HINT}")
    version = parse_version(run([candidate, "--version"], check=False).stdout)
    if version is None or version < MIN_HINGE:
        found = ".".join(map(str, version)) if version else "an unknown version"
        raise PoseError(f"hinge {found} has no posture or orient command; 0.3.0 or later is needed: "
                        "brew upgrade artemnovichkov/tap/hinge")
    return candidate


def resolve(args: argparse.Namespace) -> Device:
    listing = run(["xcrun", "simctl", "list", "devices", "--json"])
    return pick_device(duo_devices(json.loads(listing.stdout)), args.device)


def move(sim: Simulator, pose: Pose, args: argparse.Namespace) -> dict:
    before = sim.posture()
    sim.move_hinge(pose.angle, before.angle if before else None)
    if pose.orientation and (before is None or before.orientation != pose.orientation):
        sim.orient(pose.orientation)
    after = sim.wait_for(pose, args.timeout, args.tolerance)
    time.sleep(args.settle)  # let the app finish its layout passes after the hinge stops
    return {
        "row": pose.row,
        "requested": {"angle": pose.angle, "orientation": pose.orientation, "rotation": pose.rotation},
        "reported": None if after is None else after.__dict__,
        "reached": in_pose(pose, after, args.tolerance),
    }


def command_status(args: argparse.Namespace) -> dict:
    listing = run(["xcrun", "simctl", "list", "devices", "--json"])
    devices = duo_devices(json.loads(listing.stdout))
    hinge = args.hinge or os.environ.get("HINGE_BIN") or shutil.which("hinge")
    report: dict = {"devices": [d.__dict__ for d in devices], "hinge": hinge}
    if hinge:
        report["hinge_version"] = run([hinge, "--version"], check=False).stdout.strip() or None
    booted = [d for d in devices if d.booted]
    if hinge and len(booted) == 1:
        posture = Simulator(hinge, booted[0].udid).posture()
        report["posture"] = None if posture is None else posture.__dict__
    return report


def command_set(args: argparse.Namespace) -> dict:
    device = resolve(args)
    sim = Simulator(find_hinge(args.hinge), device.udid, args.sweep)
    return {"device": device.__dict__, "pose": args.pose, **move(sim, pose_for(args.pose), args)}


def command_shoot(args: argparse.Namespace) -> dict:
    device = resolve(args)
    sim = Simulator(find_hinge(args.hinge), device.udid, args.sweep)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    start = sim.posture()
    shots = []
    try:
        for name in (part.strip() for part in args.poses.split(",")):
            step = move(sim, pose_for(name), args)
            if args.relaunch:
                sim.relaunch(args.relaunch)
                time.sleep(args.launch_wait)  # a relaunched app needs longer than a re-layout
            files = {}
            for display in DISPLAYS:
                path = out / f"{name}-{display}.png"
                sim.screenshot(display, path)
                files[display] = str(path)
            shots.append({"pose": name, **step, "files": files})
    finally:
        if start is not None and start.angle is not None and not args.keep:
            move(sim, Pose(start.angle, start.orientation, None, ""), args)
    restored = None if args.keep or start is None else {"angle": start.angle, "orientation": start.orientation}
    return {"device": device.__dict__, "restored_to": restored, "shots": shots}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--device", help="UDID or name of the iPhone Duo simulator (default: the only booted one)")
    parser.add_argument("--hinge", help="path to the hinge CLI (default: $HINGE_BIN, then PATH)")
    parser.add_argument("--timeout", type=float, default=12, help="seconds to wait for the pose to be reported")
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE, help="degrees that count as reached")
    parser.add_argument("--settle", type=float, default=1.0, help="seconds to wait after the hinge stops")
    parser.add_argument("--sweep", type=float, default=DEFAULT_SWEEP, help="seconds each hinge move takes")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="list iPhone Duo simulators, the hinge CLI and the current posture")
    set_parser = sub.add_parser("set", help="move the device to a pose and wait for it")
    set_parser.add_argument("pose", help=f"{', '.join(POSES)}, or degrees 0–180")
    shoot = sub.add_parser("shoot", help="screenshot both displays in each pose, then restore the posture")
    shoot.add_argument("out", help="directory for <pose>-inner.png and <pose>-outer.png")
    shoot.add_argument("--poses", default=DEFAULT_SHOTS, help=f"comma-separated poses (default: {DEFAULT_SHOTS})")
    shoot.add_argument("--relaunch", metavar="BUNDLE_ID", help="relaunch this app before each screenshot")
    shoot.add_argument("--launch-wait", type=float, default=3.0,
                       help="seconds to wait after a relaunch before the screenshot (default: 3)")
    shoot.add_argument("--keep", action="store_true", help="leave the device in the last pose")
    args = parser.parse_args(argv)

    handlers = {"status": command_status, "set": command_set, "shoot": command_shoot}
    try:
        report = handlers[args.command](args)
    except PoseError as error:
        print(f"duo_pose: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    if args.command in ("set", "shoot"):
        steps = [report] if args.command == "set" else report["shots"]
        if not all(step["reached"] for step in steps):
            print("duo_pose: a pose was not reached. On the outer display, an app that does not support "
                  "the orientation does not rotate; otherwise the private protocol may have changed in "
                  "this Xcode", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
