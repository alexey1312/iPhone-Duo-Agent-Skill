#!/usr/bin/env python3
"""Check which iPhone Duo and iOS 27 APIs the selected SDK actually declares.

Session code samples are a snapshot of what Apple presented; SDK headers and
Swift interfaces are the ground truth the compiler uses. Run this before writing
code against an API from a talk, and trust the SDK when they disagree.
Read-only: it only reads SDK files.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

VERSION = "1.1.0"


@dataclass(frozen=True)
class Symbol:
    name: str
    area: str
    announced: str
    note: str = ""


DEFAULT_SYMBOLS: list[Symbol] = [
    # Adaptivity (WWDC26 278, Tech Talk 111461).
    Symbol("effectiveGeometry", "adaptivity", "iOS 26"),
    Symbol("registerForTraitChanges", "adaptivity", "iOS 17"),
    Symbol("deviceMotionBody", "adaptivity", "iOS 27.0"),
    Symbol("headingBody", "adaptivity", "iOS 27.0"),
    Symbol("ConcentricRectangle", "layout", "iOS 26"),
    Symbol("UICornerConfiguration", "layout", "iOS 26"),
    # Tab bars, sidebars and bar minimization (WWDC26 278).
    Symbol("defaultTabBarPlacement", "navigation", "iOS 27.0"),
    Symbol("prominentTabIdentifier", "navigation", "iOS 27.0"),
    Symbol("navigationBarMinimization", "navigation", "iOS 27.0", "SDK spelling of bar minimization"),
    Symbol("barMinimizationBehavior", "navigation", "iOS 27.0", "spelling shown in the WWDC26 278 code sample"),
    Symbol("toolbarMinimizationBehavior", "navigation", "iOS 27.0", "SwiftUI"),
    Symbol("preferredImageVisibility", "navigation", "iOS 27.0"),
    Symbol("UIWindowSceneActivationAction", "scenes", "iOS 17", "Objective-C name; Swift spells it UIWindowScene.ActivationAction"),
    # Vertical bars (Tech Talk 111462).
    Symbol("topBarPinnedTrailing", "bars", "existing"),
    Symbol("pinnedTrailingGroup", "bars", "existing"),
    Symbol("leftItemsSupplementBackButton", "bars", "existing"),
    Symbol("additionalOverflowItems", "bars", "existing"),
    Symbol("ToolbarOverflowMenu", "bars", "iOS 27"),
    Symbol("visibilityPriority", "bars", "iOS 27"),
    Symbol("axisBehavior", "bars", "iOS 27.1"),
    Symbol("toolbarVerticalEdge", "bars", "iOS 27.1"),
    Symbol("verticalBarEdge", "bars", "iOS 27.1"),
    Symbol("toolbarVerticalCompressionBehavior", "bars", "iOS 27.1"),
    Symbol("verticalBarCompressionBehavior", "bars", "iOS 27.1"),
    Symbol("toolbarVerticalBehavior", "bars", "iOS 27.1"),
    Symbol("preferredVerticalBarBehavior", "bars", "iOS 27.1"),
    # Reserved regions and arrangements (Tech Talks 111461, 111463).
    Symbol("reservedRegions", "layout", "iOS 27.1"),
    Symbol("ReservedRegion", "layout", "iOS 27.1"),
    Symbol("UIViewReservedRegion", "layout", "iOS 27.1"),
    Symbol("ArrangementView", "layout", "iOS 27.1"),
    Symbol("arrangementViewStyle", "layout", "iOS 27.1"),
    Symbol("UIArrangementViewController", "layout", "iOS 27.1"),
    Symbol("overlayArrangementZIndex", "layout", "iOS 27.1"),
    # Hinge and scene accessories (Tech Talk 111464).
    Symbol("onHingeChange", "displays", "iOS 27.1"),
    Symbol("UIHingeInteraction", "displays", "iOS 27.1"),
    Symbol("sceneAccessory", "displays", "iOS 27"),
    Symbol("CameraCaptureAccessory", "displays", "iOS 27.1"),
    Symbol("onAvailabilityChange", "displays", "iOS 27"),
    # Added 2026-09-17 from Apple's documentation pages (see api-availability.md);
    # documented availability, not yet measured against a 27.1 SDK.
    Symbol("ToolbarItemAxisBehavior", "bars", "iOS 27.1"),
    Symbol("ToolbarVerticalBehavior", "bars", "iOS 27.1"),
    Symbol("UIVerticalBarBehavior", "bars", "iOS 27.1"),
    Symbol("UIVerticalBarEdge", "bars", "iOS 27.1"),
    Symbol("presentationPlacement", "bars", "iOS 27.0", "SwiftUI sheet placement; UIKit: UISheetPresentationController.preferredPlacement"),
    Symbol("preferredPlacement", "bars", "iOS 27.0", "UISheetPresentationController; the name also exists on UITabBarController.Sidebar (iOS 18), so a hit needs the declaration line checked"),
    Symbol("backgroundExtensionEffect", "bars", "iOS 26", "extend a background under a vertical bar"),
    Symbol("UIBackgroundExtensionView", "bars", "iOS 26"),
    Symbol("splitArrangementAxis", "layout", "iOS 27.1"),
    Symbol("overlayArrangementEdge", "layout", "iOS 27.1"),
    Symbol("splitArrangementLayoutRatio", "layout", "iOS 27.1"),
    Symbol("splitArrangementLayoutSize", "layout", "iOS 27.1"),
    Symbol("UISplitArrangement", "layout", "iOS 27.1"),
    Symbol("UIOverlayArrangement", "layout", "iOS 27.1"),
    Symbol("UIHinge", "displays", "iOS 27.1", "angle in radians; status closed / partiallyOpen / fullyOpen / unknown"),
    Symbol("UISceneAccessory", "displays", "iOS 27.0", "UIKit scene accessories; cameraCapture(sceneConfiguration:userInfo:)"),
    Symbol("registerSceneAccessory", "displays", "iOS 27.0"),
    Symbol("UISceneAccessoryRegistration", "displays", "iOS 27.0", "isAvailable (observable), isEnabled"),
    # Cameras (Tech Talk 111465; AVKit article "Choosing a camera by the direction it faces").
    Symbol("AVCaptureDeviceDirectionCoordinator", "cameras", "iOS 27.1", "AVKit"),
    Symbol("AVCaptureDeviceDescriptor", "cameras", "iOS 27.1", "AVKit"),
    Symbol("AVCaptureDeviceDirectionMap", "cameras", "iOS 27.1", "AVKit; forwardFacingDeviceDescriptors / backwardFacingDeviceDescriptors"),
    Symbol("builtInOuterUltraWideCamera", "cameras", "iOS 27.1", "discoverable only through AVCaptureDevice.DiscoverySession"),
    Symbol("builtInInnerUltraWideCamera", "cameras", "iOS 27.1", "discoverable only through AVCaptureDevice.DiscoverySession"),
    Symbol("dynamicAspectRatio", "cameras", "iOS 26"),
    Symbol("RotationCoordinator", "cameras", "iOS 17", "AVCaptureDevice.RotationCoordinator; recreate per device"),
    # Device capabilities.
    Symbol("biometryType", "adaptivity", "iOS 11", "LocalAuthentication; iPhone Duo reports .touchID"),
]

AVAILABILITY = re.compile(r"(API_AVAILABLE\([^)]*\)|API_DEPRECATED\([^)]*\)|@available\([^)]*\))")


def run(command: list[str]) -> str | None:
    try:
        return subprocess.run(command, check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def interface_files(sdk: Path) -> list[Path]:
    """Public headers plus one Swift interface per framework module."""
    frameworks = sdk / "System" / "Library" / "Frameworks"
    files: list[Path] = []
    for framework in sorted(frameworks.glob("*.framework")):
        files.extend(sorted((framework / "Headers").rglob("*.h")))
        modules = framework / "Modules"
        if not modules.is_dir():
            continue
        for swiftmodule in sorted(modules.glob("*.swiftmodule")):
            candidates = sorted(swiftmodule.glob("*.swiftinterface"))
            preferred = [c for c in candidates if c.name in ("arm64-apple-ios.swiftinterface", "arm64e-apple-ios.swiftinterface")]
            public = [c for c in candidates if "private" not in c.name and "macabi" not in c.name]
            chosen = preferred[:1] or public[:1]
            files.extend(chosen)
    return files


def check(sdk: Path, symbols: list[Symbol]) -> dict:
    combined = re.compile(r"\b(" + "|".join(re.escape(symbol.name) for symbol in symbols) + r")\b")
    results = {symbol.name: {"frameworks": set(), "declaration": None} for symbol in symbols}
    files = interface_files(sdk)
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        framework = next((part[: -len(".framework")] for part in path.parts if part.endswith(".framework")), path.name)
        seen: set[str] = set()
        for match in combined.finditer(text):
            name = match.group(1)
            if name in seen:
                continue
            seen.add(name)
            entry = results[name]
            entry["frameworks"].add(framework)
            if entry["declaration"] is not None:
                continue
            start = text.rfind("\n", 0, match.start()) + 1
            end = text.find("\n", match.end())
            end = len(text) if end == -1 else end
            line = text[start:end].strip()
            if line.startswith(("*", "//", "/*", "#")):
                # Documentation mentions the symbol; keep looking for the declaration.
                seen.discard(name)
                continue
            previous = text[:start].splitlines()[-3:]
            availability = AVAILABILITY.findall(line) or AVAILABILITY.findall("\n".join(previous))
            entry["declaration"] = {
                "file": str(path.relative_to(sdk)),
                "line": line[:240],
                "availability": availability[-1] if availability else None,
            }
    rows = []
    for symbol in symbols:
        entry = results[symbol.name]
        rows.append(
            {
                "symbol": symbol.name,
                "area": symbol.area,
                "announced": symbol.announced,
                "note": symbol.note,
                "found": bool(entry["frameworks"]),
                "frameworks": sorted(entry["frameworks"]),
                "declaration": entry["declaration"],
            }
        )
    return {"files_searched": len(files), "symbols": rows}


def render_markdown(report: dict) -> str:
    lines = [
        "# SDK API check",
        "",
        f"- SDK: `{report['sdk_path']}` (version {report['sdk_version']})",
        f"- Xcode: {report['xcode_version']}",
        f"- Interface files searched: {report['files_searched']}",
        "",
        "| Symbol | Area | Announced | In SDK | Frameworks | Note |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["symbols"]:
        found = "yes" if row["found"] else "**no**"
        lines.append(
            f"| `{row['symbol']}` | {row['area']} | {row['announced']} | {found} | "
            f"{', '.join(row['frameworks'])} | {row['note']} |"
        )
    missing = [row["symbol"] for row in report["symbols"] if not row["found"]]
    if missing:
        lines += [
            "",
            "Missing symbols do not compile with this SDK. Do not write code against them; "
            "record the work as blocked on a newer Xcode instead.",
        ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sdk", help="SDK path; defaults to `xcrun --sdk <platform> --show-sdk-path`")
    parser.add_argument("--platform", default="iphoneos", help="xcrun SDK name, default iphoneos")
    parser.add_argument("--symbol", action="append", default=[], help="Check this symbol instead of the default list (repeatable)")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args(argv)

    sdk_path = args.sdk or run(["xcrun", "--sdk", args.platform, "--show-sdk-path"])
    if not sdk_path or not Path(sdk_path).is_dir():
        parser.error("could not resolve an SDK; pass --sdk or select an Xcode with xcode-select")
    sdk = Path(sdk_path)
    symbols = [Symbol(name, "custom", "unknown") for name in args.symbol] if args.symbol else DEFAULT_SYMBOLS

    report = check(sdk, symbols)
    report = {
        "tool": "sdk_api_check",
        "version": VERSION,
        "sdk_path": str(sdk),
        "sdk_version": (run(["xcrun", "--sdk", args.platform, "--show-sdk-version"]) if not args.sdk else None) or "unknown",
        "xcode_version": (run(["xcodebuild", "-version"]) or "unknown").replace("\n", ", "),
        **report,
    }
    if args.format == "json":
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_markdown(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
