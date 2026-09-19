#!/usr/bin/env python3
"""Read-only iPhone Duo readiness scanner for Swift and Objective-C projects.

The scanner never modifies files. It reports legacy patterns that break on the
inner display of iPhone Duo and in other resizable environments (iPhone
Mirroring, iPhone apps on iPad), plus an inventory of the containers and APIs a
project already uses, so an agent can reason over structured JSON instead of ad
hoc grep output.

Every rule cites the Apple session it comes from. Matches are heuristics: the
agent must read the surrounding code before recommending a change.
"""

from __future__ import annotations

import argparse
import json
import plistlib
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

VERSION = "1.2.1"

SEVERITIES = ["critical", "high", "medium", "low", "info"]
SOURCE_EXTENSIONS = {".swift", ".m", ".mm", ".h"}
BUILD_SETTING_EXTENSIONS = {".pbxproj", ".xcconfig"}
EXCLUDED_DIRS = {
    ".git",
    ".build",
    ".swiftpm",
    ".derived-data",
    "DerivedData",
    "build",
    "node_modules",
    "xcuserdata",
}
DEPENDENCY_DIRS = {"Pods", "Carthage", "checkouts", "SourcePackages", "vendor", "Vendor"}

S_PREPARE = "Tech Talk 111461 Prepare your app for iPhone Duo"
S_BARS = "Tech Talk 111462 Raise the bar with iPhone Duo"
S_POSE = "Tech Talk 111463 Strike a pose with adaptive layouts on iPhone Duo"
S_SCENES = "Tech Talk 111464 Leverage multiple displays and scenes on iPhone Duo"
S_MODERNIZE = "WWDC26 278 Modernize your UIKit app"
S_SPEC = "Apple iPhone Duo tech specs"


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    severity: str
    skill: str
    source: str
    advice: str
    pattern: str
    supersedes: tuple[str, ...] = ()
    # Regex naming the API that handles this case. A logical line that matches it is
    # not reported; in a file that matches it elsewhere, findings are reported at
    # `low` severity so the reader confirms the branch instead of hunting for it.
    already_handled: str = ""


RULES: list[Rule] = [
    Rule(
        id="DUO001",
        title="Main screen reference",
        severity="high",
        skill="iphone-duo-adaptivity-audit",
        source=f"{S_PREPARE} 3:57; {S_MODERNIZE} 2:51",
        advice=(
            "The main screen is ambiguous on a two-display device and deprecated. "
            "Use traitCollection.displayScale (SwiftUI: @Environment(\\.displayScale)) "
            "for scale, view.window?.windowScene?.screen for the screen, or pass a "
            "screen reference in."
        ),
        pattern=r"\bUIScreen\s*\.\s*main\b|\[\s*UIScreen\s+mainScreen\s*\]",
    ),
    Rule(
        id="DUO002",
        title="Screen bounds used as available space",
        severity="high",
        skill="iphone-duo-adaptivity-audit",
        source=f"{S_MODERNIZE} 5:19; {S_PREPARE} 3:57",
        advice=(
            "A scene rarely owns the whole screen. Use view.bounds or the superview "
            "size (SwiftUI: GeometryReader, onGeometryChange, containerRelativeFrame), "
            "or windowScene.effectiveGeometry with "
            "windowScene(_:didUpdateEffectiveGeometry:) for scene-level space."
        ),
        pattern=(
            r"\bUIScreen\s*\.\s*main\s*\.\s*(?:bounds|nativeBounds)\b"
            r"|\[\s*UIScreen\s+mainScreen\s*\]\s*(?:\.\s*|\s+)(?:bounds|nativeBounds)\b"
            r"|\.\s*screen\s*\??\s*\.\s*(?:bounds|nativeBounds)\b"
        ),
        supersedes=("DUO001",),
    ),
    Rule(
        id="DUO003",
        title="User interface idiom check",
        severity="medium",
        skill="iphone-duo-adaptivity-audit",
        source=f"{S_PREPARE} 1:33; {S_MODERNIZE} 6:17",
        advice=(
            "The idiom says nothing about available space: an iPhone app stays in the "
            "phone idiom while fully resizable. Replace layout decisions with size "
            "classes or the container size; keep idiom checks only for non-layout "
            "behavior and say why."
        ),
        pattern=r"\buserInterfaceIdiom\b|\bUI_USER_INTERFACE_IDIOM\s*\(",
    ),
    Rule(
        id="DUO004",
        title="Interface or device orientation used for layout",
        severity="high",
        skill="iphone-duo-adaptivity-audit",
        source=f"{S_PREPARE} 2:46; {S_MODERNIZE} 6:50",
        advice=(
            "The inner display ignores supported interface orientations, and iPhone "
            "Mirroring always reports portrait. Use size classes or the view's aspect "
            "ratio. For sensors, set motionManager.deviceMotionBody / "
            "locationManager.headingBody to the view instead. A documented physical "
            "question no geometry answers (which end holds a cutout) may stay."
        ),
        pattern=(
            r"\binterfaceOrientation\b|\bstatusBarOrientation\b"
            r"|\bUIDevice\s*\.\s*current\s*\.\s*orientation\b"
            r"|\[\s*\[\s*UIDevice\s+currentDevice\s*\]\s+orientation\s*\]"
            r"|\borientationDidChangeNotification\b|\bUIDeviceOrientationDidChangeNotification\b"
            r"|\bUI(?:Interface|Device)OrientationIs(?:Landscape|Portrait)\s*\("
            r"|\.\s*isLandscape\b|\.\s*isPortrait\b"
        ),
    ),
    Rule(
        id="DUO006",
        title="Symmetric safe-area or margin arithmetic",
        severity="medium",
        skill="iphone-duo-layout",
        source=f"{S_PREPARE} 6:06",
        advice=(
            "Safe areas and layout margins are often asymmetric on iPhone Duo. Handle "
            "each edge independently, e.g. view.bounds.inset(by: view.safeAreaInsets)."
        ),
        pattern=(
            r"(?:safeAreaInsets|layoutMargins|directionalLayoutMargins)\s*\.\s*"
            r"(?:left|right|top|bottom|leading|trailing)\s*\*\s*2(?:\.0)?\b"
            r"|\b2(?:\.0)?\s*\*\s*[\w.?]*(?:safeAreaInsets|layoutMargins|directionalLayoutMargins)"
            r"\s*\.\s*(?:left|right|top|bottom|leading|trailing)\b"
            # One side copied into a local first: `let inset = safeAreaInsets.left` … `inset * 2`
            r"|\b[a-z]\w*(?:[Ii]nset|[Mm]argin)\s*\*\s*2(?:\.0)?\b"
            r"|\b2(?:\.0)?\s*\*\s*[a-z]\w*(?:[Ii]nset|[Mm]argin)\b(?!s?\s*\.)"
            r"|\b(?:inset|margin)\s*\*\s*2(?:\.0)?\b"
        ),
    ),
    Rule(
        id="DUO007",
        title="Standalone bar instance",
        severity="medium",
        skill="iphone-duo-bars",
        source=f"{S_BARS} 2:00",
        advice=(
            "Content of custom UIToolbar, UINavigationBar and UITabBar instances is not "
            "considered for vertical bars. Move items to UINavigationController / "
            "UITabBarController (SwiftUI: .toolbar inside NavigationStack or "
            "NavigationSplitView)."
        ),
        pattern=(
            r"\b(?:UIToolbar|UINavigationBar|UITabBar)\s*\("
            r"|\[\s*\[\s*(?:UIToolbar|UINavigationBar|UITabBar)\s+alloc\s*\]"
            r"|\[\s*(?:UIToolbar|UINavigationBar|UITabBar)\s+new\s*\]"
        ),
    ),
    Rule(
        id="DUO008",
        title="Deprecated NavigationView",
        severity="low",
        skill="iphone-duo-layout",
        source=f"{S_PREPARE} 5:01; {S_BARS} 2:00",
        advice=(
            "Use NavigationStack or NavigationSplitView: they adapt across every pose "
            "and provide the bars that move to the vertical axis."
        ),
        pattern=r"\bNavigationView\s*[{(]",
    ),
    Rule(
        id="DUO009",
        title="Global window or status bar state",
        severity="medium",
        skill="iphone-duo-adaptivity-audit",
        source=f"{S_SCENES} 3:38; {S_MODERNIZE} 2:51",
        advice=(
            "iPhone Duo runs several scenes and displays at once, so an app-wide window "
            "is ambiguous and connectedScenes.first is an arbitrary one. Reach the window, "
            "scene and status bar through the view (view.window, view.window?.windowScene)."
        ),
        pattern=(
            r"\bUIApplication\s*\.\s*shared\s*\.\s*(?:windows|keyWindow)\b"
            r"|sharedApplication\s*\]\s*(?:\.\s*|\s+)(?:windows|keyWindow)\b"
            r"|\bstatusBarFrame\b"
            r"|\bconnectedScenes\b[^\n]*\.\s*first\b"
        ),
    ),
    Rule(
        id="DUO010",
        title="Scene activation without error handling",
        severity="medium",
        skill="iphone-duo-displays",
        source=f"{S_SCENES} 3:38",
        advice=(
            "New windows cannot be created on the outer display. Handle the error, or "
            "use UIWindowScene.ActivationAction, which hides itself when new windows "
            "aren't available."
        ),
        pattern=r"\b(?:requestSceneSessionActivation|activateSceneSession)\b[^\n]*errorHandler\s*:\s*nil\b",
    ),
    Rule(
        id="DUO011",
        title="Custom ellipsis overflow button",
        severity="low",
        skill="iphone-duo-bars",
        source=f"{S_BARS} 11:40",
        advice=(
            "Reserve the ellipsis for the system overflow menu. Consolidate custom "
            "overflow into ToolbarOverflowMenu (UIKit: navigationItem.additionalOverflowItems)."
        ),
        pattern=r"systemName\s*:\s*\"ellipsis(?:\.circle)?(?:\.fill)?\"|systemImageNamed\s*:\s*@\"ellipsis(?:\.circle)?(?:\.fill)?\"",
    ),
    Rule(
        id="DUO013",
        title="Hard-coded Face ID copy or symbol",
        severity="medium",
        skill="iphone-duo-adaptivity-audit",
        source=f"{S_PREPARE} 2:34; {S_SPEC} (Touch ID)",
        advice=(
            "iPhone Duo unlocks with Touch ID in the side button and has no Face ID, so "
            "copy, symbols and onboarding that name Face ID are wrong on it. Branch on "
            "LAContext.biometryType (.faceID, .touchID, .none) after canEvaluatePolicy "
            "for strings and SF Symbols (faceid / touchid). Keep NSFaceIDUsageDescription "
            "for Face ID devices. Localizable .strings and .xcstrings files are not scanned; "
            "grep them too."
        ),
        # "face id" / "Face-ID" with a separator can only occur inside a string once
        # comments are stripped (multi-line literals included); the joined spelling is
        # matched inside a single-line literal only, so `.faceID` enum cases stay clean.
        pattern=r"(?i:\bface[ -]id\b)|\"[^\"\n]*(?i:\bfaceid\b)[^\"\n]*\"",
        already_handled=r"\bbiometryType\b|\bLABiometryType\b",
    ),
]

INVENTORY_PATTERNS: dict[str, str] = {
    # Containers that adapt for free.
    "NavigationStack": r"\bNavigationStack\b",
    "NavigationSplitView": r"\bNavigationSplitView\b",
    "TabView": r"\bTabView\b",
    "UINavigationController": r"\bUINavigationController\b",
    "UISplitViewController": r"\bUISplitViewController\b",
    "UITabBarController": r"\bUITabBarController\b",
    # Bars.
    "toolbar modifier": r"\.\s*toolbar\s*[{(]",
    "ToolbarItem": r"\bToolbarItem(?:Group)?\s*\(",
    "UIBarButtonItem": r"\bUIBarButtonItem\b",
    "custom view bar item": r"\bUIBarButtonItem\s*\(\s*customView\s*:|initWithCustomView\s*:",
    # Layout.
    "size class reads": r"\b(?:horizontalSizeClass|verticalSizeClass)\b",
    "GeometryReader": r"\bGeometryReader\b",
    "onGeometryChange": r"\bonGeometryChange\b",
    "ignoresSafeArea": r"\bignoresSafeArea\b",
    "safeAreaInsets": r"\bsafeAreaInsets\b",
    "Concentricity APIs": r"\b(?:ConcentricRectangle|UICornerConfiguration)\b",
    # Scenes and displays.
    "multiple scene requests": r"\b(?:requestSceneSessionActivation|activateSceneSession|openWindow)\b",
    "camera capture session": r"\bAVCaptureSession\b",
    "front camera discovery": r"position\s*:\s*\.front\b",
    "video mirroring": r"\bisVideoMirrored\b|\bautomaticallyAdjustsVideoMirroring\b",
    "rotation coordinator": r"\bRotationCoordinator\b",
    "direction coordinator": r"\bAVCaptureDeviceDirectionCoordinator\b",
    # Device capabilities and presence on the outer display.
    "biometryType reads": r"\bbiometryType\b",
    "WidgetKit": r"\bimport\s+WidgetKit\b|\bWidgetConfiguration\b|\bStaticConfiguration\b|\bAppIntentConfiguration\b",
    "Live Activities": r"\bimport\s+ActivityKit\b|\bActivityAttributes\b|\bActivityConfiguration\b",
    # iPhone Duo APIs already adopted. Measured present in the iOS 27.1 SDK
    # (Xcode 27.1, 27A9269) on 2026-09-19; see references/api-availability.md for
    # which of these need 27.1 and which are older -- `additionalOverflowItems` is
    # iOS 16 and `ToolbarOverflowMenu` and `visibilityPriority` are iOS 27.0, so a
    # hit here is evidence of adoption, not evidence of a 27.1 deployment target.
    "axisBehavior": r"\baxisBehavior\b",
    "visibilityPriority": r"\bvisibilityPriority\b",
    "vertical bar behavior": r"\b(?:toolbarVerticalBehavior|preferredVerticalBarBehavior|toolbarVerticalEdge|verticalBarEdge)\b",
    "vertical bar compression": r"\b(?:toolbarVerticalCompressionBehavior|verticalBarCompressionBehavior)\b",
    "overflow menu": r"\b(?:ToolbarOverflowMenu|additionalOverflowItems)\b",
    "reservedRegions": r"\b(?:reservedRegions|ReservedRegion|UIViewReservedRegion)\b",
    "arrangements": r"\b(?:ArrangementView|UIArrangementViewController|UISplitArrangement\w*|UIOverlayArrangement\w*|UIArrangementViewState)\b",
    "arrangement tuning": r"\b(?:arrangementViewStyle|splitArrangementLayoutRatio|splitArrangementLayoutSize|splitArrangementFixedLayoutSize|overlayArrangementEdge|splitArrangementAxis|overlayArrangementZIndex)\b",
    "hinge": r"\b(?:onHingeChange|UIHingeInteraction|UIHinge|DeviceHinge)\b",
    "scene accessories": r"\b(?:sceneAccessory|CameraCaptureAccessory)\b",
    "container content margins": r"\bContentMarginGuide\b|\bcontentMargins\s*\(\s*for\s*:",
    # Recommended by READINESS-CHECKS and the bars skill, so adoption has to count.
    "vertical bar trait observation": r"\bsystemTraitsAffectingVerticalBarEdge\b",
    "bar layout region": r"\bUIViewLayoutRegion\b|\blayoutRegionForBarOn(?:Directional)?Edge\b|\bLayoutRegion\s*\.\s*bar\s*\(",
}

PORTRAIT_ORIENTATIONS = {"UIInterfaceOrientationPortrait", "UIInterfaceOrientationPortraitUpsideDown"}


@dataclass
class Finding:
    id: str
    rule: str
    title: str
    severity: str
    skill: str
    file: str
    line: int
    snippet: str
    source: str
    advice: str


def strip_comments(text: str, nested_block_comments: bool = True) -> str:
    """Blank out comments while keeping string literals and line numbers intact."""
    out: list[str] = []
    i, n = 0, len(text)
    depth = 0
    in_string = False
    multiline = False
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if depth:
            if ch == "*" and nxt == "/":
                depth -= 1
                out.append("  ")
                i += 2
            elif nested_block_comments and ch == "/" and nxt == "*":
                depth += 1
                out.append("  ")
                i += 2
            else:
                out.append("\n" if ch == "\n" else " ")
                i += 1
            continue
        if in_string:
            if ch == "\\" and i + 1 < n:
                out.append(text[i : i + 2])
                i += 2
                continue
            if multiline and text.startswith('"""', i):
                in_string = multiline = False
                out.append('"""')
                i += 3
                continue
            if not multiline and ch in '"\n':
                in_string = False
            out.append(ch)
            i += 1
            continue
        if ch == "/" and nxt == "/":
            end = text.find("\n", i)
            end = n if end == -1 else end
            out.append(" " * (end - i))
            i = end
            continue
        if ch == "/" and nxt == "*":
            depth = 1
            out.append("  ")
            i += 2
            continue
        if text.startswith('"""', i):
            in_string = multiline = True
            out.append('"""')
            i += 3
            continue
        if ch == '"':
            in_string = True
        out.append(ch)
        i += 1
    return "".join(out)


def iter_project_files(root: Path, include_dependencies: bool) -> list[Path]:
    excluded = set(EXCLUDED_DIRS)
    if not include_dependencies:
        excluded |= DEPENDENCY_DIRS
    files: list[Path] = []
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            entries = sorted(directory.iterdir(), key=lambda p: p.name)
        except OSError:
            continue
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if entry.name in excluded or entry.name.startswith("."):
                    continue
                if entry.suffix == ".xcodeproj":
                    pbxproj = entry / "project.pbxproj"
                    if pbxproj.is_file():
                        files.append(pbxproj)
                    continue
                stack.append(entry)
            elif entry.is_file():
                if entry.suffix in SOURCE_EXTENSIONS or entry.suffix in BUILD_SETTING_EXTENSIONS:
                    files.append(entry)
                elif entry.name.endswith("Info.plist"):
                    files.append(entry)
    return sorted(files)


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def make_finding(rule: Rule, rel: str, line: int, snippet: str, severity: str | None = None) -> Finding:
    return Finding(
        id=f"{rule.id}:{rel}:{line}",
        rule=rule.id,
        title=rule.title,
        severity=severity or rule.severity,
        skill=rule.skill,
        file=rel,
        line=line,
        snippet=snippet.strip()[:200],
        source=rule.source,
        advice=rule.advice,
    )


def logical_lines(stripped: str) -> list[tuple[int, str]]:
    """Join Swift member-chain continuations (a line starting with `.`) onto the line before.

    `UIApplication.shared.connectedScenes` followed by `.first` on a later line is one
    expression; matching physical lines alone misses it. Each logical line keeps the
    number of its first physical line.
    """
    joined: list[tuple[int, str]] = []
    for number, code in enumerate(stripped.splitlines(), start=1):
        if joined and code.lstrip().startswith(".") and not code.lstrip().startswith(".."):
            first, previous = joined[-1]
            joined[-1] = (first, previous + " " + code.strip())
        elif code.strip():
            joined.append((number, code))
    return joined


def scan_source(
    rel: str,
    text: str,
    stripped: str,
    compiled: list[tuple[Rule, re.Pattern[str], re.Pattern[str] | None]],
) -> list[Finding]:
    """Match line rules against the comment-stripped text; `text` supplies the snippets."""
    original_lines = text.splitlines()
    findings: list[Finding] = []
    handled_in_file = {rule.id for rule, _, handled in compiled if handled and handled.search(stripped)}
    for number, code in logical_lines(stripped):
        matched = [
            rule
            for rule, regex, handled in compiled
            if regex.search(code) and not (handled and handled.search(code))
        ]
        superseded = {rid for rule in matched for rid in rule.supersedes}
        for rule in matched:
            if rule.id in superseded:
                continue
            snippet = original_lines[number - 1] if number - 1 < len(original_lines) else code
            severity = "low" if rule.id in handled_in_file else None
            findings.append(make_finding(rule, rel, number, snippet, severity=severity))
    return findings


PROJECT_RULES = {
    "DUO005": Rule(
        id="DUO005",
        title="App lifecycle without scene lifecycle",
        severity="critical",
        skill="iphone-duo-adaptivity-audit",
        source=f"{S_MODERNIZE} 2:10",
        advice=(
            "UIScene lifecycle is required when building with the latest SDKs; without it "
            "the app no longer launches. Adopt a UIWindowSceneDelegate and a "
            "UIApplicationSceneManifest, or a SwiftUI App."
        ),
        pattern="",
    ),
    "DUO012": Rule(
        id="DUO012",
        title="Scene delegate without a scene manifest",
        severity="low",
        skill="iphone-duo-adaptivity-audit",
        source=f"{S_MODERNIZE} 2:10",
        advice=(
            "A scene delegate exists but no UIApplicationSceneManifest was found in an "
            "Info.plist or generated build settings. Confirm the scene configuration "
            "is actually wired up."
        ),
        pattern="",
    ),
    "DUO020": Rule(
        id="DUO020",
        title="UIRequiresFullScreen is set",
        severity="info",
        skill="iphone-duo-adaptivity-audit",
        source=f"{S_MODERNIZE} 5:46; {S_PREPARE} 4:37",
        advice=(
            "Starting in iOS 27 this key no longer opts an app out of resizing: the scene "
            "resizes discretely, and iPhone Duo still resizes the app when it opens or "
            "closes and scales it on the inner display, including in Split View. It is "
            "meant for games; other apps should remove the key and adapt to any size "
            "(UIRequiresFullScreenIgnoredStartingWithVersion keeps the old behavior on "
            "earlier iOS versions)."
        ),
        pattern="",
    ),
    "DUO021": Rule(
        id="DUO021",
        title="Portrait-only supported orientations",
        severity="info",
        skill="iphone-duo-layout",
        source=f"{S_PREPARE} 2:46; {S_MODERNIZE} 6:50",
        advice=(
            "Supported orientations are only a preference in iOS 27 and the inner "
            "display of iPhone Duo does not honor them. Layout must work at any aspect "
            "ratio, including wide."
        ),
        pattern="",
    ),
}

SWIFTUI_APP = re.compile(r"@main\b[\s\S]{0,300}?\bstruct\s+\w+\s*:\s*(?:SwiftUI\s*\.\s*)?App\b")
SCENE_DELEGATE = re.compile(r"\bUIWindowSceneDelegate\b|\bUISceneDelegate\b|\bconfigurationForConnecting(?:SceneSession)?\b")
APP_DELEGATE = re.compile(r"\bUIApplicationDelegate\b|@UIApplicationMain\b|\bUIApplicationMain\s*\(")
SETTING_SCENE_MANIFEST = re.compile(r"INFOPLIST_KEY_UIApplicationSceneManifest_Generation\s*=\s*YES")
SETTING_FULL_SCREEN = re.compile(r"INFOPLIST_KEY_UIRequiresFullScreen\s*=\s*YES")
SETTING_IPHONE_ORIENTATIONS = re.compile(
    r"INFOPLIST_KEY_UISupportedInterfaceOrientations(?:_iPhone)?\s*=\s*\"?([^;\"\n]+)\"?"
)


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def scan(root: Path, include_dependencies: bool = False) -> dict:
    root = root.resolve()
    compiled = [
        (rule, re.compile(rule.pattern), re.compile(rule.already_handled) if rule.already_handled else None)
        for rule in RULES
    ]
    inventory_regex = {name: re.compile(pattern) for name, pattern in INVENTORY_PATTERNS.items()}
    inventory = {name: 0 for name in INVENTORY_PATTERNS}
    findings: list[Finding] = []

    swiftui_app = False
    scene_delegate_file: str | None = None
    app_delegate: tuple[str, int, str] | None = None
    scene_manifest = False
    supports_multiple_scenes: bool | None = None
    source_count = 0

    files = iter_project_files(root, include_dependencies)
    for path in files:
        rel = relative(path, root)
        if path.name.endswith("Info.plist"):
            try:
                with path.open("rb") as stream:
                    plist = plistlib.load(stream)
            except Exception:
                continue
            if not isinstance(plist, dict):
                continue
            manifest = plist.get("UIApplicationSceneManifest")
            if isinstance(manifest, dict):
                scene_manifest = True
                multiple = manifest.get("UIApplicationSupportsMultipleScenes")
                if isinstance(multiple, bool):
                    supports_multiple_scenes = bool(supports_multiple_scenes) or multiple
            for key, value in plist.items():
                if key.lower() == "uirequiresfullscreen" and value is True:
                    findings.append(make_finding(PROJECT_RULES["DUO020"], rel, 1, f"{key} = true"))
            for key in ("UISupportedInterfaceOrientations", "UISupportedInterfaceOrientations~iphone"):
                values = plist.get(key)
                if isinstance(values, list) and values and set(values) <= PORTRAIT_ORIENTATIONS:
                    findings.append(make_finding(PROJECT_RULES["DUO021"], rel, 1, f"{key} = {', '.join(values)}"))
            continue

        text = read_text(path)
        if text is None:
            continue

        if path.suffix in BUILD_SETTING_EXTENSIONS:
            if SETTING_SCENE_MANIFEST.search(text):
                scene_manifest = True
            for match in SETTING_FULL_SCREEN.finditer(text):
                findings.append(make_finding(PROJECT_RULES["DUO020"], rel, line_of(text, match.start()), match.group(0)))
            for match in SETTING_IPHONE_ORIENTATIONS.finditer(text):
                values = set(match.group(1).split())
                if values and values <= PORTRAIT_ORIENTATIONS:
                    findings.append(make_finding(PROJECT_RULES["DUO021"], rel, line_of(text, match.start()), match.group(0)))
            continue

        source_count += 1
        stripped = strip_comments(text, nested_block_comments=path.suffix == ".swift")
        if path.suffix == ".swift" and SWIFTUI_APP.search(stripped):
            swiftui_app = True
        if scene_delegate_file is None and SCENE_DELEGATE.search(stripped):
            scene_delegate_file = rel
        if app_delegate is None:
            match = APP_DELEGATE.search(stripped)
            if match:
                number = line_of(stripped, match.start())
                app_delegate = (rel, number, text.splitlines()[number - 1])
        for name, regex in inventory_regex.items():
            inventory[name] += len(regex.findall(stripped))
        findings.extend(scan_source(rel, text, stripped, compiled))

    if swiftui_app:
        lifecycle = "swiftui-app"
    elif scene_delegate_file:
        lifecycle = "scene"
        if not scene_manifest:
            findings.append(make_finding(PROJECT_RULES["DUO012"], scene_delegate_file, 1, "scene delegate without manifest"))
    elif app_delegate:
        lifecycle = "app-delegate-only"
        rel, number, snippet = app_delegate
        findings.append(make_finding(PROJECT_RULES["DUO005"], rel, number, snippet))
    else:
        lifecycle = "unknown"

    findings.sort(key=lambda f: (SEVERITIES.index(f.severity), f.rule, f.file, f.line))
    by_severity = {severity: 0 for severity in SEVERITIES}
    by_rule: dict[str, int] = {}
    by_skill: dict[str, int] = {}
    for finding in findings:
        by_severity[finding.severity] += 1
        by_rule[finding.rule] = by_rule.get(finding.rule, 0) + 1
        by_skill[finding.skill] = by_skill.get(finding.skill, 0) + 1

    return {
        "tool": "duo_scan",
        "version": VERSION,
        "root": str(root),
        "read_only": True,
        "source_files_scanned": source_count,
        "dependencies_included": include_dependencies,
        "project": {
            "lifecycle": lifecycle,
            "scene_manifest_found": scene_manifest,
            "supports_multiple_scenes": supports_multiple_scenes,
        },
        "summary": {"by_severity": by_severity, "by_rule": by_rule, "by_skill": by_skill},
        "findings": [asdict(finding) for finding in findings],
        "inventory": {name: count for name, count in inventory.items() if count},
    }


def render_markdown(report: dict, limit: int) -> str:
    lines = [
        "# iPhone Duo readiness scan",
        "",
        f"- Root: `{report['root']}`",
        f"- Source files scanned: {report['source_files_scanned']}",
        f"- Lifecycle: `{report['project']['lifecycle']}`"
        f" (scene manifest found: {report['project']['scene_manifest_found']},"
        f" multiple scenes: {report['project']['supports_multiple_scenes']})",
        "- Read-only: nothing was modified. Matches are heuristics; read the code before acting.",
        "",
        "## Summary",
        "",
        "| Severity | Count |",
        "| --- | ---: |",
    ]
    for severity, count in report["summary"]["by_severity"].items():
        lines.append(f"| {severity} | {count} |")
    lines += ["", "## Findings", ""]
    findings = report["findings"]
    if not findings:
        lines.append("No findings.")
    for finding in findings[:limit]:
        lines.append(
            f"- **{finding['rule']} {finding['title']}** ({finding['severity']}, {finding['skill']}) "
            f"`{finding['file']}:{finding['line']}`  \n  `{finding['snippet']}`"
        )
    if len(findings) > limit:
        lines.append(f"- … {len(findings) - limit} more (use --format json for all)")
    if report["inventory"]:
        lines += ["", "## Inventory", "", "| API or container | Occurrences |", "| --- | ---: |"]
        for name, count in report["inventory"].items():
            lines.append(f"| {name} | {count} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", nargs="?", default=".", help="Project or package root to scan")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--include-dependencies", action="store_true", help="Also scan Pods, Carthage, SwiftPM checkouts and vendor folders")
    parser.add_argument("--limit", type=int, default=200, help="Maximum findings listed in markdown output")
    parser.add_argument("--fail-on", choices=SEVERITIES, help="Exit with status 2 when a finding at or above this severity exists")
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        parser.error(f"not a directory: {root}")
    report = scan(root, include_dependencies=args.include_dependencies)
    if args.format == "json":
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_markdown(report, args.limit))

    if args.fail_on:
        threshold = SEVERITIES.index(args.fail_on)
        if any(SEVERITIES.index(f["severity"]) <= threshold for f in report["findings"]):
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
