#!/usr/bin/env python3
"""Check which iPhone Duo and iOS 27 APIs the selected SDK actually declares.

Session code samples are a snapshot of what Apple presented; SDK headers and
Swift interfaces are the ground truth the compiler uses. Run this before writing
code against an API from a talk, and trust the SDK when they disagree.
Read-only: it only reads SDK files.
"""

from __future__ import annotations

import argparse
import bisect
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

VERSION = "1.2.2"


@dataclass(frozen=True)
class Symbol:
    """One API name to look for, plus any other spelling that proves it exists.

    `also` carries alternate spellings of the same declaration. A symbol whose
    Swift name is synthesized by the Objective-C importer never appears as text
    in any file the compiler ships, so searching for it alone reports a symbol
    that compiles fine as missing. List the Objective-C constant there.
    """

    name: str
    area: str
    announced: str
    note: str = ""
    also: tuple[str, ...] = ()


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
    # Measured against the iOS 27.1 SDK (Xcode 27.1, 27A9269) on 2026-09-19;
    # every entry below is present. See api-availability.md for the full run.
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
    # Measured on the iOS 27.1 SDK 2026-09-19: declared there, absent from the 27.0 SDK.
    # Arrangements, beyond the entry points above.
    Symbol("AutomaticArrangementViewStyle", "layout", "iOS 27.1", "SwiftUI .automatic arrangement style"),
    Symbol("ArrangementViewStyleConfiguration", "layout", "iOS 27.1", "primary / secondary content of a custom arrangement style"),
    Symbol("splitArrangementFixedLayoutSize", "layout", "iOS 27.1"),
    Symbol("UISplitArrangementDimension", "layout", "iOS 27.1", "automatic / intrinsic / fractional / absolute"),
    Symbol("UISplitArrangementDimensionRange", "layout", "iOS 27.1", "minimum / preferred / maximum"),
    Symbol("UISplitArrangementViewProperties", "layout", "iOS 27.1", "width, height, layoutPriority"),
    Symbol("UIOverlayArrangementViewProperties", "layout", "iOS 27.1", "edge the view takes when the overlay goes side by side"),
    Symbol("UIArrangementViewState", "layout", "iOS 27.1", "zIndex, splitAxis, isHidden"),
    Symbol("arrangementViewController", "layout", "iOS 27.1", "UIViewController property: nearest ancestor arrangement"),
    Symbol("UIViewReservedRegionKind", "layout", "iOS 27.1", "occlusionRegionKind / divisionRegionKind"),
    Symbol("ContentMarginGuide", "layout", "iOS 27.1", "the 27.1 overloads are contentMargins(for:edges:alignment:) and GeometryProxy.contentMargins(for:edges:); bare contentMargins(_:_:for:) is iOS 17 and would always match"),
    # Vertical bars, beyond the entry points above.
    Symbol("systemTraitsAffectingVerticalBarEdge", "bars", "iOS 27.1", "verticalBarEdge is derived and has no UITrait class; register for these traits to observe it"),
    Symbol("childForPreferredVerticalBarBehavior", "bars", "iOS 27.1", also=("childViewControllerForPreferredVerticalBarBehavior",)),
    Symbol("setNeedsUpdateOfVerticalBarConfiguration", "bars", "iOS 27.1"),
    Symbol("layoutRegionForBarOnEdge", "bars", "iOS 27.1", "Swift: UIView.LayoutRegion.bar(onEdge:extent:)"),
    Symbol("windowCameraCaptureAccessory", "displays", "iOS 27.1", "accessory scene session role", also=("UIWindowSceneSessionRoleCameraCaptureAccessory",)),
    # Present in the 27.0 SDK, relevant to multiple windows and resizing.
    Symbol("UISceneClosureConfirmation", "displays", "iOS 27.0", "UIWindowScene.closureConfirmation"),
    Symbol("UITraitSystemPrefersReducedResourceUsage", "adaptivity", "iOS 27.0"),
    # Cameras (Tech Talk 111465; AVKit article "Choosing a camera by the direction it faces").
    Symbol("AVCaptureDeviceDirectionCoordinator", "cameras", "iOS 27.1", "AVKit"),
    Symbol("AVCaptureDeviceDescriptor", "cameras", "iOS 27.1", "AVKit"),
    Symbol("AVCaptureDeviceDirectionMap", "cameras", "iOS 27.1", "AVKit; forwardFacingDeviceDescriptors / backwardFacingDeviceDescriptors"),
    Symbol(
        "builtInOuterUltraWideCamera",
        "cameras",
        "iOS 27.1",
        "discoverable only through AVCaptureDevice.DiscoverySession; AVFoundation ships no Swift interface, so only the Objective-C constant appears as text",
        also=("AVCaptureDeviceTypeBuiltInOuterUltraWideCamera",),
    ),
    Symbol(
        "builtInInnerUltraWideCamera",
        "cameras",
        "iOS 27.1",
        "discoverable only through AVCaptureDevice.DiscoverySession; AVFoundation ships no Swift interface, so only the Objective-C constant appears as text",
        also=("AVCaptureDeviceTypeBuiltInInnerUltraWideCamera",),
    ),
    Symbol("dynamicAspectRatio", "cameras", "iOS 26"),
    Symbol("RotationCoordinator", "cameras", "iOS 17", "AVCaptureDevice.RotationCoordinator; recreate per device"),
    # Device capabilities.
    Symbol("biometryType", "adaptivity", "iOS 11", "LocalAuthentication; iPhone Duo reports .touchID"),
]

AVAILABILITY = re.compile(r"(API_AVAILABLE\([^)]*\)|API_DEPRECATED\([^)]*\)|@available\([^)]*\))")

# `"`, `//` or `/*` -- the only places a comment or a string can begin.
COMMENT_OR_STRING = re.compile(r'"|//|/\*')


def comment_spans(text: str) -> list[tuple[int, int]]:
    """Half-open ranges of `text` that are comments, skipping string literals.

    A symbol that appears only in a comment is documentation, not a declaration.
    Deciding that with `rfind("/*")` is not safe: one unbalanced `/*` inside a
    `//` line or a string literal -- both of which occur in shipped SDK headers --
    marks every later match in the file as a comment, and the symbol is then
    reported as absent. For this tool that is the worst possible failure, because
    absent means "do not write this code".
    """
    spans: list[tuple[int, int]] = []
    end = len(text)
    position = 0
    while (match := COMMENT_OR_STRING.search(text, position)) is not None:
        start = match.start()
        token = match.group()
        if token == '"':
            index = start + 1
            while index < end:
                character = text[index]
                if character == "\\":
                    index += 2
                    continue
                if character == '"':
                    index += 1
                    break
                if character == "\n":  # unterminated; don't run past the line
                    break
                index += 1
            position = max(index, start + 1)
            continue
        if token == "//":
            stop = text.find("\n", start)
            stop = end if stop == -1 else stop
        else:
            stop = text.find("*/", start + 2)
            stop = end if stop == -1 else stop + 2
        spans.append((start, stop))
        position = stop
    return spans


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


def in_comment(spans: list[tuple[int, int]], position: int) -> bool:
    index = bisect.bisect_right(spans, (position, len(spans) and spans[-1][1] or 0)) - 1
    return index >= 0 and spans[index][0] <= position < spans[index][1]


def check(sdk: Path, symbols: list[Symbol]) -> dict:
    spellings: dict[str, str] = {}
    for symbol in symbols:
        for spelling in (symbol.name, *symbol.also):
            spellings[spelling] = symbol.name
    # Longest first is not what makes an Objective-C constant win over a shorter
    # name inside it -- the trailing `\b` already forces that. It only keeps the
    # alternation stable and readable.
    ordered = sorted(spellings, key=len, reverse=True)
    combined = re.compile(r"\b(" + "|".join(re.escape(s) for s in ordered) + r")\b")
    results = {
        symbol.name: {"frameworks": set(), "declaration": None, "matched": set()}
        for symbol in symbols
    }
    files = interface_files(sdk)
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        framework = next((part[: -len(".framework")] for part in path.parts if part.endswith(".framework")), path.name)
        spans = comment_spans(text)
        seen: set[str] = set()
        for match in combined.finditer(text):
            spelling = match.group(1)
            if spelling in seen:
                continue
            start = text.rfind("\n", 0, match.start()) + 1
            end = text.find("\n", match.end())
            end = len(text) if end == -1 else end
            line = text[start:end].strip()
            # A comment mention is documentation, not a declaration. HeaderDoc blocks
            # (`/*! @constant Foo ... */`) carry no leading `*`, so the prefix test
            # alone read the doc line as the declaration and then scraped availability
            # from the lines above -- which belong to the *previous* symbol. That
            # reported AVCaptureDeviceTypeBuiltInOuterUltraWideCamera, an ios(27.1)
            # API, as ios(13.0). `#` is a preprocessor directive, not a comment.
            if in_comment(spans, match.start()) or line.startswith("#"):
                # Keep looking; the declaration may be further down the same file.
                continue
            seen.add(spelling)
            name = spellings[spelling]
            entry = results[name]
            # Only a real declaration counts, so `matched` and `frameworks` can never
            # disagree about why a symbol was reported present.
            entry["frameworks"].add(framework)
            entry["matched"].add(spelling)
            if entry["declaration"] is not None:
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
        matched = sorted(entry["matched"])
        rows.append(
            {
                "symbol": symbol.name,
                "area": symbol.area,
                "announced": symbol.announced,
                "note": symbol.note,
                "found": bool(entry["frameworks"]),
                "frameworks": sorted(entry["frameworks"]),
                "matched_as": matched,
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
        other = [s for s in row.get("matched_as", []) if s != row["symbol"]]
        if row["found"] and row["symbol"] not in row.get("matched_as", []) and other:
            spellings = ", ".join(f"`{s}`" for s in other)
            found = f"yes (as {spellings})"
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
