---
name: iphone-duo-adaptivity-audit
description: >-
  Find and fix legacy screen, orientation, idiom and lifecycle code that breaks on
  iPhone Duo's inner display and in other iOS 27 resizable environments (iPhone
  Mirroring, iPhone apps on iPad, Split View). Use when a developer asks about
  UIScreen.main or mainScreen, screen bounds or scale, interfaceOrientation or
  UIDevice orientation checks, userInterfaceIdiom layout forks, keyWindow or
  connectedScenes.first, migrating from app lifecycle to UIScene lifecycle
  (required with the latest SDK), UIRequiresFullScreen, portrait-only apps, or
  hard-coded Face ID strings and symbols (iPhone Duo has Touch ID; branch on
  LAContext.biometryType). Covers SwiftUI and UIKit, ships a read-only scanner, and delegates bulk UIKit
  rewrites to Xcode's own modernization skill when available. Not for app features
  that merely touch UIScreen or orientation, such as screen brightness,
  deliberately locking a game to one orientation, or camera and sensor setup.
---

# iPhone Duo adaptivity audit

The foundation for everything else: an app that decides layout from the screen, the
orientation or the idiom is wrong on iPhone Duo before any foldable-specific work
begins.

## Facts this skill relies on

- The **outer display** behaves like other iPhones; the **inner display** is regular
  width × regular height. (Tech Talk 111461, 2:46)
- The inner display **does not honor supported interface orientations**; in iOS 27
  supported orientations are a preference ignored in resizable environments, and
  iPhone Mirroring always reports portrait. (111461 2:46; WWDC26 278 6:50)
- Referencing the **main screen is ambiguous on a two-display device** and deprecated
  (the iOS 27 SDK header marks `mainScreen` deprecated). (111461 3:57; 278 2:51)
- The **user interface idiom is not meaningful for layout**: an iPhone app stays in the
  phone idiom while fully resizable. (111461 1:33; 278 6:17)
- **UIScene lifecycle is required** when building with the latest SDKs; without it
  the app no longer launches. (278 2:10)
- `UIRequiresFullScreen` no longer opts an app out of resizing from iOS 27: it gives
  discrete resizing, and iPhone Duo still resizes the app when it opens or closes and
  scales it on the inner display, including in Split View — meant for games.
  `UIRequiresFullScreenIgnoredStartingWithVersion` keeps the old behavior on earlier
  iOS. (278 5:46; 111461 4:37; TN3192)
- **iPhone Duo has Touch ID in the side button and no Face ID** (Apple tech specs;
  `references/device-geometry.md`). Adaptive apps make no assumptions about device
  capabilities (111461 2:34): copy, symbols and onboarding that name Face ID are
  wrong on it.

## Workflow

1. **Scan** (read-only):
   ```bash
   python3 scripts/duo_scan.py <root> --format markdown
   python3 scripts/duo_scan.py <root> --format json   # for exact IDs
   ```
   Rules owned here: `DUO001` main screen, `DUO002` screen bounds, `DUO003` idiom,
   `DUO004` orientation, `DUO005` app lifecycle, `DUO009` global window state,
   `DUO012` scene delegate without manifest, `DUO013` Face ID copy, `DUO020`
   `UIRequiresFullScreen`.
   Member chains split across lines (`connectedScenes` … `.first`) are joined before
   matching; other multi-line expressions, macros and generated code are not seen, so
   follow up with targeted searches when the inventory suggests more.
2. **Classify each match** by reading the code:
   - *Layout decision* (sizes, columns, which view to show) → replace.
   - *Rendering scale* (`scale`, pixel alignment, image sizes) → replace with trait.
   - *Physical question* no geometry answers (which end holds a cutout, sensor frame
     alignment before body protocols) → **kept** if documented; otherwise ask.
   - *Non-layout behavior* keyed off idiom (feature availability, analytics) → kept,
     with a comment naming why.
   - *Capability assumption* (Face ID in strings, `faceid` symbols, onboarding) →
     derive from `LAContext.biometryType`. `DUO013` reports `medium` where nothing in
     the file ever asked, and `low` next to an existing `biometryType` read — confirm
     those strings sit in the `.faceID` branch and mark them *kept*.
3. **Check Xcode's skill.** Export into a temporary directory — without
   `--output-dir` the command writes into the current directory:
   ```bash
   out="$(mktemp -d)" && xcrun agent skills export --output-dir "$out" >/dev/null 2>&1; ls "$out"
   ```
   If it yields `uikit-app-modernization` (Xcode 27.0) or App Resizability (27.1), use it for bulk
   UIKit rewrites: it applies deprecate-and-forward patterns, preserves guards and
   control flow, and tracks file coverage. Review its diff against the approved items.
   SwiftUI code and anything it leaves as a TODO come back here.
4. **Recommend** in the format of `references/recommendation-format.md`; wait for
   approval; apply; build; re-scan.

## Replacements

Full before/after code for SwiftUI and UIKit: `references/legacy-api-remediation.md`.

| Legacy | UIKit replacement | SwiftUI replacement |
| --- | --- | --- |
| `UIScreen.main.scale` | `traitCollection.displayScale` (auto-tracked in `layoutSubviews`, `draw(_:)`, `updateProperties`; else `registerForTraitChanges`) | `@Environment(\.displayScale)` |
| `UIScreen.main` (the screen) | `view.window?.windowScene?.screen`; pass a `UIScreen` parameter where no view is at hand | Rarely needed — ask what the screen is for |
| `UIScreen.main.bounds` for available space | `view.bounds` in `viewDidLayoutSubviews`; scene level: `windowScene.effectiveGeometry` + `windowScene(_:didUpdateEffectiveGeometry:)` | `GeometryReader`, `onGeometryChange(for:of:action:)`, `containerRelativeFrame` |
| `userInterfaceIdiom == .pad` for layout | `traitCollection.horizontalSizeClass` / container size | `@Environment(\.horizontalSizeClass)` |
| `interfaceOrientation`, `UIDevice.current.orientation` for layout | Size classes or `bounds.width > bounds.height` | Size classes or geometry aspect |
| Scene `interfaceOrientation` (deprecated in 27 SDK) where orientation is truly needed | `windowScene.effectiveGeometry.interfaceOrientation` | same, from the view's window scene |
| Orientation to align sensor data | `motionManager.deviceMotionBody = view`, `locationManager.headingBody = view` | same, on a hosting view |
| `UIApplication.shared.keyWindow` / `windows` / `connectedScenes.first` | `view.window`, `view.window?.windowScene` | the view's own context; `openWindow`/`dismissWindow` environment actions |
| App lifecycle only | `UIApplicationSceneManifest` + `UIWindowSceneDelegate`; move window setup to `scene(_:willConnectTo:options:)` | `@main struct …: App` is already scene-based |
| `"Face ID"` in copy, `faceid` symbols | A `switch context.biometryType` (`.faceID`, `.touchID`, default) after `canEvaluatePolicy`, feeding titles and `UIImage(systemName:)` | The same switch in a small model feeding `Label` / `Button(_:systemImage:)` |

## Applying changes

- **Preserve today's behavior on today's devices.** A replacement that is correct on
  iPhone Duo but turns a two-column portrait / four-column landscape grid into three
  columns on a small iPhone is a regression. State the before/after on at least one
  existing device.
- **Kept means kept.** For a documented exception, change only the deprecated call it
  uses (for example `scene.interfaceOrientation` → `effectiveGeometry.interfaceOrientation`).
  Restructuring it — new representables, observers, different data flow — is a separate
  proposal for the developer to approve, because the documentation exists precisely so
  that nobody "improves" it unasked.
- **Typecheck what you touched.** Run the project's build, or at least
  `xcrun --sdk iphonesimulator swiftc -typecheck` on the edited files at the deployment
  target, and re-run `duo_scan.py`. Report what was and was not verified.

## Pitfalls

- **A size class is not a device.** Regular × regular now includes an iPhone. Code
  that reads "regular means iPad" must become "regular means room for more columns".
- **Don't cache screen-derived values** in `init` or static storage; closing or
  opening iPhone Duo moves the scene to another display. Recompute on trait or
  geometry change.
- **Orientation replacement is not always width > height.** When left versus right
  matters (cutouts, camera side), ask before replacing.
- **Scene lifecycle migration touches app state restoration, URL handling, push
  notification routing and background tasks.** Plan it as its own item and read
  Xcode's `scene-lifecycle-task.md` reference when available.
- Leave `UIRequiresFullScreen` alone in games that need discrete resizing; for other
  apps recommend removing it and adapting instead.
- **Localization catalogs hide biometric copy.** The scanner reads Swift and
  Objective-C only; grep `.strings` and `.xcstrings` for "Face ID" and build those
  sentences from the biometry name instead. Keep `NSFaceIDUsageDescription`: Face ID
  devices still need it.
