#!/usr/bin/env python3
"""Put a booted iPhone Duo simulator into a pose and screenshot it.

Apple ships no command that sets the hinge: `simctl` has none, and
`xcrun devicectl device motion hinge-angle` only reads it. This script drives the
third-party `hinge` CLI (https://github.com/artemnovichkov/hinge, MIT), which
posts the private event Device Hub's hinge slider sends, and wraps it with the
checks it lacks:

- it acts on an iPhone Duo simulator only, chosen by device type and always
  passed to `hinge` with `-d` (bare `hinge` acts on the first booted simulator);
- after setting an angle it waits until `devicectl` reports it;
- `shoot` captures both displays by screen ID — the default display is not stable —
  because only the one in use has content, and puts the hinge back where it found it.

Rotation has no command, so inner-display portrait and tabletop are not
reachable from here: report those poses as not run.

This changes simulator state. Run it in the verification phase, after the
developer has approved it, never during a read-only scan.

    python3 scripts/duo_pose.py status
    python3 scripts/duo_pose.py set book
    python3 scripts/duo_pose.py shoot /tmp/poses --poses closed,book,flat
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
POSES = {"closed": 0.0, "book": 90.0, "flat": 180.0}
# The simulator reports a smoothed, quantised angle (179° came back as 174.1°),
# so "reached" means within this many degrees of the request.
DEFAULT_TOLERANCE = 6.0
# Screen IDs from the iPhone Duo device profile (`simctl io <udid> enumerate`). Always name
# the display: without --display, simctl picked the inner display one run and the outer
# the next.
DISPLAYS = {"inner": ["--display=3"], "outer": ["--display=1"]}
INSTALL_HINT = "brew install artemnovichkov/tap/hinge   (or set HINGE_BIN to a checkout's bin/hinge)"

ANGLE_PATTERN = re.compile(r"Angle:\s*([0-9]+(?:[.,][0-9]+)?)")


class PoseError(Exception):
    """A precondition failed; the message says what to do."""


@dataclass(frozen=True)
class Device:
    udid: str
    name: str
    booted: bool


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


def parse_angle(devicectl_output: str) -> float | None:
    """The first angle `devicectl device motion hinge-angle` printed, in degrees."""
    match = ANGLE_PATTERN.search(devicectl_output)
    return float(match.group(1).replace(",", ".")) if match else None


def pose_angle(pose: str) -> float:
    """Degrees for a pose name or a number between 0 and 180."""
    if pose in POSES:
        return POSES[pose]
    try:
        degrees = float(pose)
    except ValueError:
        raise PoseError(f"unknown pose {pose!r}: use {', '.join(POSES)} or 0–180") from None
    if not 0 <= degrees <= 180:
        raise PoseError(f"angle {degrees} is outside 0–180")
    return degrees


def reached(target: float, actual: float | None, tolerance: float = DEFAULT_TOLERANCE) -> bool:
    return actual is not None and abs(actual - target) <= tolerance


def expected_display(angle: float) -> str:
    """Where an app is for the named poses: closed shows the outer display."""
    return "outer" if angle == 0 else "inner"


class Simulator:
    """The commands this script runs. Kept in one place so tests can see them."""

    def __init__(self, hinge: str, udid: str):
        self.hinge = hinge
        self.udid = udid

    def angle(self) -> float | None:
        result = run(["xcrun", "devicectl", "device", "motion", "hinge-angle", "-d", self.udid,
                      "--session-timeout", "2", "-t", "8"], check=False)
        return parse_angle(result.stdout + result.stderr)

    def set_angle(self, degrees: float) -> None:
        run([self.hinge, "-d", self.udid, "set", f"{degrees:g}"])

    def wait_for(self, degrees: float, timeout: float, tolerance: float) -> float | None:
        deadline = time.monotonic() + timeout
        actual = None
        while time.monotonic() < deadline:
            actual = self.angle()
            if reached(degrees, actual, tolerance):
                return actual
            time.sleep(0.5)
        return actual

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
    return candidate


def resolve(args: argparse.Namespace) -> Device:
    listing = run(["xcrun", "simctl", "list", "devices", "--json"])
    return pick_device(duo_devices(json.loads(listing.stdout)), args.device)


def move(sim: Simulator, degrees: float, args: argparse.Namespace) -> dict:
    sim.set_angle(degrees)
    actual = sim.wait_for(degrees, args.timeout, args.tolerance)
    time.sleep(args.settle)  # let the app finish its layout passes after the hinge stops
    return {"requested": degrees, "reported": actual, "reached": reached(degrees, actual, args.tolerance)}


def command_status(args: argparse.Namespace) -> dict:
    listing = run(["xcrun", "simctl", "list", "devices", "--json"])
    devices = duo_devices(json.loads(listing.stdout))
    report = {"devices": [d.__dict__ for d in devices], "hinge": shutil.which("hinge") or os.environ.get("HINGE_BIN")}
    booted = [d for d in devices if d.booted]
    if len(booted) == 1:
        report["angle"] = Simulator(report["hinge"] or "hinge", booted[0].udid).angle()
    return report


def command_set(args: argparse.Namespace) -> dict:
    device = resolve(args)
    sim = Simulator(find_hinge(args.hinge), device.udid)
    return {"device": device.__dict__, **move(sim, pose_angle(args.pose), args)}


def command_shoot(args: argparse.Namespace) -> dict:
    device = resolve(args)
    sim = Simulator(find_hinge(args.hinge), device.udid)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    start = sim.angle()
    shots = []
    try:
        for pose in args.poses.split(","):
            degrees = pose_angle(pose.strip())
            step = move(sim, degrees, args)
            if args.relaunch:
                sim.relaunch(args.relaunch)
                time.sleep(args.launch_wait)  # a relaunched app needs longer than a re-layout
            files = {}
            for display in DISPLAYS:
                path = out / f"{pose.strip()}-{display}.png"
                sim.screenshot(display, path)
                files[display] = str(path)
            shots.append({"pose": pose.strip(), **step, "app_display": expected_display(degrees), "files": files})
    finally:
        if start is not None and not args.keep:
            sim.set_angle(start)
            sim.wait_for(start, args.timeout, args.tolerance)
    return {"device": device.__dict__, "restored_to": None if args.keep else start, "shots": shots,
            "not_reachable": "inner-display portrait and tabletop: rotation has no command"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--device", help="UDID or name of the iPhone Duo simulator (default: the only booted one)")
    parser.add_argument("--hinge", help="path to the hinge CLI (default: $HINGE_BIN, then PATH)")
    parser.add_argument("--timeout", type=float, default=12, help="seconds to wait for devicectl to report the angle")
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE, help="degrees that count as reached")
    parser.add_argument("--settle", type=float, default=1.0, help="seconds to wait after the hinge stops")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="list iPhone Duo simulators, the hinge CLI and the current angle")
    set_parser = sub.add_parser("set", help="move the hinge to a pose and wait for it")
    set_parser.add_argument("pose", help="closed, book, flat, or degrees 0–180")
    shoot = sub.add_parser("shoot", help="screenshot both displays in each pose, then restore the angle")
    shoot.add_argument("out", help="directory for <pose>-inner.png and <pose>-outer.png")
    shoot.add_argument("--poses", default="closed,book,flat", help="comma-separated poses (default: closed,book,flat)")
    shoot.add_argument("--relaunch", metavar="BUNDLE_ID", help="relaunch this app before each screenshot")
    shoot.add_argument("--launch-wait", type=float, default=3.0,
                       help="seconds to wait after a relaunch before the screenshot (default: 3)")
    shoot.add_argument("--keep", action="store_true", help="leave the hinge in the last pose")
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
            print("duo_pose: the hinge did not reach every requested angle; the private protocol may "
                  "have changed in this Xcode", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
