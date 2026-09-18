# Readiness checks

Automated rules run by `scripts/duo_scan.py`, followed by the manual checks each skill
performs. Session abbreviations: **111461** Prepare your app for iPhone Duo, **111462**
Raise the bar, **111463** Strike a pose, **111464** Leverage multiple displays and
scenes, **111465** Build a great camera experience for iPhone Duo, **111466** Design
for iPhone Duo, **278** Modernize your UIKit app (WWDC26), **HIG** Designing for iPhone
Duo (Human Interface Guidelines, cited by section), **PREP** Preparing your app for
iPhone Duo (Apple documentation, cited by section), **TN3192** the `UIRequiresFullScreen`
technote, **Spec** iPhone Duo tech specs, **Newsroom** Apple's iPhone Duo announcement.

## Automated rules

| Rule | Severity | Detects | Skill | Source |
| --- | --- | --- | --- | --- |
| DUO001 | high | `UIScreen.main`, `[UIScreen mainScreen]` | adaptivity-audit | 111461 3:57; 278 2:51 |
| DUO002 | high | Main or scene screen `bounds` / `nativeBounds` used as space (supersedes DUO001 on the line) | adaptivity-audit | 278 5:19; 111461 3:57 |
| DUO003 | medium | `userInterfaceIdiom`, `UI_USER_INTERFACE_IDIOM()` | adaptivity-audit | 111461 1:33; 278 6:17 |
| DUO004 | high | `interfaceOrientation`, `statusBarOrientation`, `UIDevice` orientation, orientation notifications, `isLandscape` / `isPortrait` | adaptivity-audit | 111461 2:46; 278 6:50 |
| DUO005 | critical | App delegate with no SwiftUI `App`, scene delegate or scene manifest | adaptivity-audit | 278 2:10 |
| DUO006 | medium | Safe-area or margin inset on one side multiplied by 2 | layout | 111461 6:06 |
| DUO007 | medium | Standalone `UIToolbar`, `UINavigationBar`, `UITabBar` instances | bars | 111462 2:00 |
| DUO008 | low | `NavigationView` | layout | 111461 5:01; 111462 2:00 |
| DUO009 | medium | `UIApplication.shared.keyWindow` / `windows`, `statusBarFrame`, `connectedScenes…first` | adaptivity-audit | 111464 3:38; 278 2:51 |
| DUO010 | medium | Scene activation with `errorHandler: nil` | displays | 111464 3:38 |
| DUO011 | low | Custom `ellipsis` symbol buttons | bars | 111462 11:40 |
| DUO012 | low | Scene delegate but no scene manifest found | adaptivity-audit | 278 2:10 |
| DUO013 | medium | "Face ID" in any case, with a space or hyphen, in single- or multi-line string literals, or the `faceid` symbol; `low` in files that read `biometryType` elsewhere, skipped on the line that reads it | adaptivity-audit | 111461 2:34; Spec |
| DUO020 | info | `UIRequiresFullScreen` in Info.plist or build settings | adaptivity-audit | 278 5:46; 111461 4:37 |
| DUO021 | info | Portrait-only supported orientations | layout | 111461 2:46; 278 6:50 |

Limits: logical-line matching (Swift member chains that continue on a line starting with
`.` are joined; other expressions split across lines can be missed), no macro or
build-time generated sources, no Tuist/XcodeGen manifest parsing, no `#if 0` awareness,
no `.strings` / `.xcstrings` catalogs (grep them for Face ID copy). Every finding needs
the code read before it becomes a recommendation.

## Manual checks

### Build and tooling

- Build with the latest SDK; report Xcode and SDK versions. (111461 0:30)
- Run `sdk_api_check.py` before proposing 27.1 APIs; report the availability annotation it
  found, mark missing ones *blocked*, and give present ones the `#available` gate they
  need when the deployment target is below 27.1.
- Look for Xcode's exported modernization skill — `app-resizability` in Xcode 27.1. (111461 9:12; 278 14:07)
- Mac Catalyst targets still build after adopting 27.1 APIs. (Xcode 27.1 known issues 185924957, 187046347)

### Adaptivity

- Layout decisions use size classes or container size, never idiom or orientation. (111461 2:46)
- No cached screen-derived values survive a display change. (111461 3:57)
- Sensor data uses `deviceMotionBody` / `headingBody`. (278 7:55)
- Games relying on `UIRequiresFullScreen` understand discrete resizing, and that iPhone Duo still resizes them on open and close. (278 5:46; 111461 4:37; TN3192)
- Biometric copy, symbols and onboarding branch on `LAContext.biometryType`; nothing assumes Face ID. (111461 2:34; Spec)

### Bars

- All bar items live in container bars. (111462 2:00)
- Close/back first, prominent actions next. (111462 4:29)
- Every item has a title and, where possible, a symbol. (111462 5:56)
- Text-plus-symbol items become symbol plus badge unless the text carries information. (111462 9:00)
- Axis behavior set for items that change shape and for custom views with a vertical form. (111462 8:00)
- Custom bar views fit the fixed width or adapt via `toolbarVerticalEdge` / `verticalBarEdge`; UIKit observes it with `registerForTraitChanges(UITraitCollection.systemTraitsAffectingVerticalBarEdge)`, because there is no `UITrait` class for it. (111462 10:07; `UIVerticalBarEdge.h`)
- One overflow menu; ellipsis only for overflow. (111462 11:40)
- Compression behavior matches the app's focus. (111462 12:23)
- Visibility priority on groups, then items. (111462 13:10)
- Opt-out only for bottom-heavy single-page apps and single-control sheets. (111462 14:21)
- Outer display: content offset by the safe area so side controls don't hide it. (111466 6:33; HIG Vertical controls)
- Related items grouped with `ToolbarItemGroup` / `UIBarButtonItemGroup`, no manual spacing; controls stay next to the content they affect. (HIG Vertical controls)
- Sheets: vertical bar disabled only for single-control sheets on the outer display; placement on the inner display chosen with `presentationPlacement` / `preferredPlacement`. (PREP Optimize bars for vertical presentation; 111466 8:36)
- Hero or background images extend under the vertical bar with `backgroundExtensionEffect` / `UIBackgroundExtensionView`. (PREP Optimize bars for vertical presentation)
- Keyboard accessory bars stay with the keyboard; segmented controls and text buttons stay horizontal. (111462 10:00; 111466 5:07)

### Layout

- No fixed phone-width column on the inner display. (111461 1:33)
- Standard navigation containers; sidebar placement considered for the inner display. (111461 5:01)
- Foreground inside safe area, backgrounds past it, insets handled per edge. (111461 6:06)
- Custom edge-to-edge UI uses reserved regions. (111461 8:08)
- Nothing important spans the fold; displacement chosen per element; scrolling content not displaced. (111463 1:29–5:12)
- Top manually laid out controls query division and occlusion regions. (111463 6:39–7:50)
- Custom two-view layouts considered for split or overlay arrangements, not nested in scroll views or around navigation containers. (111463 9:20–16:09)
- Same functionality and state on both displays; an extra hierarchy level on the inner display where it fits. (HIG Best practices; 111466 7:34)
- Small adjustments, not rearrangement, while folding. (HIG Reserved regions)
- Games playable in every pose, changing aspect ratio rather than letterboxing or pillarboxing. (HIG Best practices)
- Manually positioned content around reserved regions respects right-to-left mirroring (regions mirror by default; `layoutDirectionBehavior: .fixed` only for deliberate absolute placement). (Apple documentation, `ReservedRegion`)
- Video players design the letterbox area on the inner display rather than leaving it black; landscape supported because people set the device down like a tent. (111461 3:30; `device-geometry.md` aspect consequences, derived)

### Displays and scenes

- Hinge effects filter partially open and reset otherwise; never essential. (111464 1:18)
- Split View multitasking works at every width, including the stacked video layout. (111464 2:59)
- Scene requests handle failure on the outer display. (111464 3:38)
- Scene accessories observe availability; camera capture accessory registered on the camera view, and tested on a device — Simulator has no camera. (111464 4:22–6:25; Apple documentation, Registering a camera capture accessory)
- Camera apps keep streaming from a forward-facing camera as the device opens and closes: virtual front camera, or a direction coordinator per preview view with descriptors handed to the session actor. (111465 1:01–6:16)
- Preview mirroring follows the direction a camera faces, not its position; a new rotation coordinator per device; sensor-orientation compensation disabled after adopting it. (111465 6:34–8:44)
- The app has a widget or Live Activity, so it exists in StandBy on the outer display — **not verifiable in the iPhone Duo simulator** (Xcode 27.1 known issues 187708663, 187708767); check the widget elsewhere and report the pose as *not run*. (Newsroom; HIG Live Activities)
- Apps that set `UIApplicationSupportsMultipleScenes` to false have a reason that still holds now that iPhone shows multiple windows. (111464 3:38)

### Verification

- Pose matrix P1–P15 run or reported as not run. Xcode 27.1 ships the iPhone Duo simulator, so use it; on Xcode 27.0, resize mode at the simulator-measured shapes 669 × 951, 951 × 669, 466 × 678 and 678 × 466 pt. (111461 1:17, 7:44; 278 8:19)
- App Store screenshots for both displays planned (sizes in `device-geometry.md`). (App Store Connect)
