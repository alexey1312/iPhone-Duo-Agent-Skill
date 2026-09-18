# API availability

The iPhone Duo talks target **Xcode 27.1 and the iOS 27.1 SDK**, which shipped as a
beta on 2026-09-18.
Several APIs they show do not exist in earlier SDKs,
and at least one code sample does not match the SDK spelling.
Before writing code against any API from a talk:

```bash
python3 scripts/sdk_api_check.py                     # default iPhone Duo symbol list
python3 scripts/sdk_api_check.py --symbol axisBehavior --symbol reservedRegions
python3 scripts/sdk_api_check.py --format json       # includes declaration line and availability
```

The script reads the selected SDK's public headers and Swift interfaces (the files
the compiler uses) and reports which symbols exist. It changes nothing.

## Rules

1. **The SDK is the ground truth.** A talk's code sample is a snapshot. If the
   sample and the SDK disagree, write what the SDK declares and tell the developer
   about the mismatch.
2. **A symbol missing from the SDK does not compile**, and `if #available` cannot
   rescue it — availability checks need the declaration to exist. Do not write
   such code. Record the item in the plan as *blocked on Xcode 27.1* (or whichever
   SDK first declares it) and move on.
   Hiding guessed calls behind `#if compiler(>=…)`, `#if canImport` or a custom flag
   is the same mistake in disguise: nobody can compile or test that branch today, so it
   ships as unverified code whose signature may not match the real SDK. Offer the
   blocked item as a plan entry instead.
3. **Say which toolchain you checked.** Report `xcodebuild -version` and the SDK
   version next to any availability claim.
4. **Deployment target still matters.** A symbol present in the SDK but introduced
   in iOS 27.1 needs `if #available(iOS 27.1, *)` (SwiftUI modifiers: an
   availability-gated `ViewModifier`) when the deployment target is lower.
   With the 27.1 SDK installed, *blocked* is no longer the default answer —
   the default answer is *available, and here is the gate it needs*.
5. **"Found in the SDK" is not "spelled that way in Swift."** A framework that ships
   a `.swiftinterface` (UIKit, SwiftUI) carries its Swift names as text.
   AVFoundation does not: its Swift names are synthesized by the Objective-C
   importer and appear in no file on disk, so searching for
   `builtInOuterUltraWideCamera` finds nothing while the API compiles fine.
   The checker carries both spellings for those symbols and says which one matched.

## What each linked SDK gets on iPhone Duo

Apps run on iPhone Duo without a rebuild; the SDK they link decides how much screen
they get (Tech Talk 111461, 0:30–1:11; *Preparing your app for iPhone Duo* ›
Overview):

| Linked SDK | Closed (outer display) | Open (inner display) | Bars |
| --- | --- | --- | --- |
| Before iOS 27 | The space to the left of the status bar and camera | A familiar size and aspect ratio | Horizontal |
| iOS 27 | Same | Extends to the left of the status bar area | Horizontal |
| iOS 27.1 | Edge to edge | Edge to edge | Standard navigation and toolbar buttons lay out vertically under the status bar |

Resizing behavior follows the same split (TN3192; Tech Talk 111461, 4:37): built with
the iOS 27 SDK and without `UIRequiresFullScreen`, the scene resizes continuously;
with the key, or with an older SDK, it resizes discretely when the drag ends. iPhone
Duo honors the key but still resizes the app when the device opens or closes, and
scales it on the inner display, including in Split View multitasking.
`UIRequiresFullScreenIgnoredStartingWithVersion` keeps the old behavior on earlier
iOS versions while the app adapts.

iPhone Duo ships **October 23** on iOS 27.1.
From **April 2027**, apps uploaded to App Store Connect must be built with the
iOS 27 SDK or later. Calendar: `sources.md`.

## Measured snapshot

Measured on **Xcode 27.1 (27A9269), iPhoneOS 27.1 SDK (version 27.1, build 24A94403)**,
Swift 6.4, on 2026-09-19, by `scripts/sdk_api_check.py` across 4574 interface files.
Re-run the script; this table ages.

**Every symbol below is present in the 27.1 SDK**, with one deliberate exception
(`barMinimizationBehavior`, which exists in no SDK — see the mismatch section).
The category *documented but not measured*, which this file carried while the 27.1
SDK was unreleased, no longer exists.

| Area | Needs 27.1 | Already in the 27.0 SDK |
| --- | --- | --- |
| Adaptivity | — | `effectiveGeometry`, `registerForTraitChanges`, `deviceMotionBody`, `headingBody`, `UITraitSystemPrefersReducedResourceUsage` |
| Corners | — | `ConcentricRectangle`, `UICornerConfiguration` (both iOS 26) |
| Navigation | — | `defaultTabBarPlacement`, `prominentTabIdentifier`, `navigationBarMinimization`, `toolbarMinimizationBehavior`, `preferredImageVisibility` |
| Bars | `axisBehavior`, `ToolbarItemAxisBehavior`, `UIBarButtonItem.axisBehavior`, `toolbarVerticalEdge`, `verticalBarEdge`, `UIVerticalBarEdge`, `systemTraitsAffectingVerticalBarEdge`, `toolbarVerticalBehavior`, `ToolbarVerticalBehavior`, `preferredVerticalBarBehavior`, `UIVerticalBarBehavior`, `childForPreferredVerticalBarBehavior`, `setNeedsUpdateOfVerticalBarConfiguration`, `toolbarVerticalCompressionBehavior`, `verticalBarCompressionBehavior`, `layoutRegionForBarOnEdge` | `topBarPinnedTrailing`, `pinnedTrailingGroup`, `leftItemsSupplementBackButton`, `additionalOverflowItems`, `ToolbarOverflowMenu`, `visibilityPriority`, `presentationPlacement`, `preferredPlacement`, `backgroundExtensionEffect` and `UIBackgroundExtensionView` (iOS 26) |
| Layout | `reservedRegions`, `ReservedRegion`, `UIViewReservedRegion`, `UIViewReservedRegionKind`, `ArrangementView`, `arrangementViewStyle`, `ArrangementViewStyleConfiguration`, `AutomaticArrangementViewStyle`, `UIArrangementViewController`, `UIArrangementViewState`, `arrangementViewController`, `UISplitArrangement`, `UISplitArrangementDimension`, `UISplitArrangementDimensionRange`, `UISplitArrangementViewProperties`, `UIOverlayArrangement`, `UIOverlayArrangementViewProperties`, `splitArrangementAxis`, `splitArrangementLayoutRatio`, `splitArrangementLayoutSize`, `splitArrangementFixedLayoutSize`, `overlayArrangementEdge`, `overlayArrangementZIndex`, `ContentMarginGuide` | — |
| Displays | `onHingeChange`, `UIHinge`, `UIHingeInteraction`, `CameraCaptureAccessory`, `windowCameraCaptureAccessory` | `sceneAccessory`, `onAvailabilityChange`, `UISceneAccessory`, `registerSceneAccessory`, `UISceneAccessoryRegistration`, `UISceneClosureConfirmation`, `UIWindowSceneActivationAction` (Swift: `UIWindowScene.ActivationAction`) |
| Cameras | `AVCaptureDeviceDirectionCoordinator`, `AVCaptureDeviceDescriptor`, `AVCaptureDeviceDirectionMap`, `builtInOuterUltraWideCamera`, `builtInInnerUltraWideCamera` | `dynamicAspectRatio` (iOS 26), `RotationCoordinator` (iOS 17) |
| Device | — | `LAContext.biometryType` (iOS 11) |

The **"Already in the 27.0 SDK"** column is *derived*, not measured a second time:
the 27.0 SDK is no longer installed on this machine, so it cannot be re-run.
The derivation is sound because a symbol annotated `ios(27.0)` or earlier is by
definition declared by the 27.0 SDK.
It is corroborated by the earlier run of this script on 2026-09-13 against
**Xcode 27.0 beta 6 (27A5252f)**: every symbol reported absent then is annotated
`ios(27.1)` today, and every symbol reported present then is annotated `ios(27.0)`
or earlier.
Two measured exceptions to the neat split:
`barMinimizationBehavior` is in neither SDK,
and `UISceneAccessory` is `ios(27.0)` while its camera-capture factory
`cameraCapture(sceneConfiguration:userInfo:)` is `ios(27.1)`.

### What to do with each toolchain

| If you build with | Write | Gate with |
| --- | --- | --- |
| Xcode 27.0 / iOS 27.0 SDK | everything in the right-hand column | nothing; 27.1 symbols do not exist, so record them as *blocked on Xcode 27.1* |
| Xcode 27.1 / iOS 27.1 SDK | everything in the table | `if #available(iOS 27.1, *)` when the deployment target is below 27.1 |

So with Xcode 27.0 you can already: remove legacy screen/orientation/idiom code,
adopt scene lifecycle, fix asymmetric safe-area math, move items into container
bars, give every item a title and symbol, set `visibilityPriority`, consolidate
overflow into `ToolbarOverflowMenu`, place close/prominent items correctly, branch
biometric copy on `LAContext.biometryType`, and ship a widget or Live Activity for
StandBy. Vertical-bar axis tuning, reserved regions, arrangements, the hinge, the
camera capture accessory and the camera direction coordinator need the 27.1 SDK —
which is now installable, so on Xcode 27.1 they are a deployment-target question,
not a blocked one.

## Platform reach

The iPhone Duo family is **not iPhone-only**. Hinge (`UIHinge`, `UIHingeInteraction`),
arrangements (`UIArrangementViewController`, `UISplitArrangement`, `UIOverlayArrangement`)
and reserved regions (`UIViewReservedRegion`) are all declared
`API_AVAILABLE(ios(27.1), tvos(27.1), visionos(27.1))` with `API_UNAVAILABLE(watchos)`,
so wrapping them in `#if os(iOS)` hides them from a tvOS or visionOS target that
could compile them.

The vertical-bar APIs are the one place to read the annotation carefully rather than
assume. In `UIVerticalBarEdge.h` the *type* and the trait are
`ios(27.1), tvos(27.1), visionos(27.1)`, but the two cases that carry the meaning —
`UIVerticalBarEdgeLeading` and `UIVerticalBarEdgeTrailing` — are `API_AVAILABLE(ios(27.1))`
with `API_UNAVAILABLE(visionos)` and `API_UNAVAILABLE(watchos, tvos)`. So a tvOS or
visionOS target can name the type but cannot name a side.
The camera capture accessory is the exception, and only partly:
`+[UISceneAccessory cameraCaptureSceneAccessoryWithConfiguration:]` is
`API_AVAILABLE(ios(27.1))` with `API_UNAVAILABLE(macCatalyst, tvos, visionos, watchos)`,
so the factory really is iOS-only — but the session role it produces,
`UIWindowSceneSessionRoleCameraCaptureAccessory`, is
`API_AVAILABLE(ios(27.1), tvos(27.1), visionos(27.1))` like the rest of the family.
Gate the factory, not the role.

## Xcode 27.1 known issues that change what you can verify

From the Xcode 27.1 beta release notes, cited by radar number:

- **187708663** — StandBy is unavailable in the iPhone Duo Simulator runtime.
  The StandBy readiness check cannot be satisfied there.
- **187708767** — most app extensions cannot be run or debugged in that runtime,
  which includes widgets and Live Activities — the very things the StandBy check
  depends on. Verify them on another simulator or a device and report the iPhone Duo
  pose as *not run*.
- **187708500** — first launch of the runtime can take several minutes. Not a hang.
- **185924957** — a project using iOS 27.1 APIs fails to compile for Mac Catalyst
  ("undeclared identifier", "has no member"). Workaround:
  `#if !targetEnvironment(macCatalyst)`.
- **187046347** — a project targeting iOS 27.1 gets no Mac Catalyst run destination.
  Workaround: give the Catalyst target a 27.0 minimum deployment.

The last two matter for planning: an app that ships Mac Catalyst will break its Mac
build the moment it adopts a 27.1 API. Treat it as a Tier 1 risk, not a detail.

Xcode 27.1 beta also adds a **Display** group to the Previews canvas overrides
picker (182598534), for previewing on a device's alternative display.

## Negative results

Searched across the whole 27.1 SDK and found nothing. Recorded so the absence is not
rediscovered:

- No `posture`, `crease`, `halfOpen`, or `fold`/`folded`/`foldable` in the
  device sense — anywhere in any framework.
- **No fold or posture `UITraitCollection` trait.** Fold state reaches you only
  through `UIHingeInteraction` (UIKit) or `onHingeChange` (SwiftUI): there is no
  notification, no trait and no `UIDevice` property.
- No `UIDevice` or `UIScreen` additions in iOS 26 or 27.
- No Companion, Secondary or Auxiliary display API.
- No new `UIWindowSceneGeometry` or `UISceneSession` API in 27.x.
- No new `Info.plist` key documented in any 27.x header.
- `UIHingeMagicPose`, `UIHingeStateAvailability` and `DeviceHinge.ID` appear in the
  `.tbd` export lists but have no public declaration. They are private. Never use them.

`verticalBarEdge` is a derived property with **no `UITrait` class**, so the
`registerForTraitChanges(UITraitVerticalBarEdge.self)` an agent would guess does not
exist. Register for `UITraitCollection.systemTraitsAffectingVerticalBarEdge` instead.

## Known talk-versus-SDK mismatch

*Modernize your UIKit app* (11:30) shows:

```swift
navigationItem.barMinimizationBehavior = .always
navigationItem.barMinimizationSafeAreaAdjustment = .never
```

The SDK declares instead a `UIBarMinimization` configuration value:

```swift
// UIKit (iOS 27.0 and 27.1 SDKs)
var minimization = navigationItem.navigationBarMinimization
minimization.minimizationBehavior = .onScrollDown   // .automatic, .never, .onScrollDown, .onScrollUp
minimization.safeAreaAdjustment = .disabled         // .automatic, .enabled, .disabled
navigationItem.navigationBarMinimization = minimization

// SwiftUI
.toolbarMinimizationBehavior(_:for:)
.toolbarMinimizationSafeAreaAdjustment(_:for:)
```

There is no `.always` in either SDK. Re-measured on the 27.1 SDK on 2026-09-19:
`barMinimizationBehavior` is **still absent**, so the mismatch is now confirmed
against two SDKs rather than one. Verify against the SDK you build with before
using either spelling; a later SDK may differ again. The same caution applies to
every sample in `sources.md`.

## Swift spellings of Objective-C names

Talks and headers often use Objective-C class names. Swift may nest them.
Measured on the 27.1 SDK:

| Header name | Swift spelling |
| --- | --- |
| `UIWindowSceneActivationAction` | `UIWindowScene.ActivationAction` |
| `UIWindowSceneActivationConfiguration` | `UIWindowScene.ActivationConfiguration` |
| `UIViewReservedRegion` | `UIView.ReservedRegion` (`.Kind`, `.QueryOptions`) |
| `UIHingeStatus` | `UIHinge.Status` |
| `UIHingeInteractionUpdate` | `UIHingeInteraction.Update` |
| `UIArrangementViewControllerViewPlacement` | `UIArrangementViewController.ViewPlacement` (`.primary` / `.secondary`) |
| `UIWindowSceneSessionRoleCameraCaptureAccessory` | `UISceneSession.Role.windowCameraCaptureAccessory` |
| `childViewControllerForPreferredVerticalBarBehavior` | `childForPreferredVerticalBarBehavior` |
| `layoutRegionForBarOnEdge:extent:` | `UIView.LayoutRegion.bar(onEdge:extent:)` |
| `AVCaptureDeviceTypeBuiltInOuterUltraWideCamera` | `AVCaptureDevice.DeviceType.builtInOuterUltraWideCamera` |

The flat names fail with "has been renamed".

The reverse problem is worse, because it produces a false *absent*. UIKit and
SwiftUI ship `.swiftinterface` files, so their Swift names exist as text and a
search finds them. **AVFoundation ships none**: its Swift names are synthesized by
the importer, so `builtInOuterUltraWideCamera` appears nowhere on disk even though
the API compiles. Searching for it alone reported an `ios(27.1)` API as missing,
which under Rule 2 would have told a developer to abandon working code.
`sdk_api_check.py` now carries the Objective-C constant alongside such symbols and
reports which spelling matched; the compiler is still the final word.

## Typechecked samples

The iOS 26 / 27.0 samples were typechecked against the iOS 27.0 SDK on 2026-09-13:
adaptivity replacements, bar placements, badges, `visibilityPriority`,
`ToolbarOverflowMenu`, `additionalOverflowItems`, `navigationBarMinimization`,
sidebar placement, `prominentTabIdentifier`, safe-area insets,
`ConcentricRectangle`, scene activation.

The 27.1 samples could not be checked until the SDK shipped. They now have been, on
2026-09-19:

```bash
xcrun --sdk iphonesimulator swiftc -typecheck -target arm64-apple-ios27.1-simulator probe.swift
```

Clean, covering every 27.1 shape these skills teach:
`proxy.reservedRegions(kind:options:)` and `view.reservedRegions(kind:options:)`
with `.frame`, `.margins` and `.isActive`;
`ArrangementView { } secondary: { }` under `.split.axes(.horizontal)` and
`.overlay`, with `splitArrangementLayoutRatio`, `overlayArrangementEdge`, and the
`splitArrangementAxis` and `overlayArrangementZIndex` environment values;
`UIArrangementViewController` with `setViewController(_:for:animated:)`,
`updateArrangement(_:animated:)`, `state(for:)`, `viewController(for:)` and
`placement(for:)`;
`onHingeChange` with `DeviceHingeContext` and `UIHingeInteraction` with
`UIHinge.Status` (including its `@unknown default`);
`axisBehavior` on toolbar items and on `UIBarButtonItem`,
`toolbarVerticalBehavior(.disabled)`,
`toolbarVerticalCompressionBehavior(.prefersTabBar)`,
`verticalBarCompressionBehavior`, `traitCollection.verticalBarEdge`,
`registerForTraitChanges(UITraitCollection.systemTraitsAffectingVerticalBarEdge)`,
`setNeedsUpdateOfVerticalBarConfiguration()`;
`contentMargins(for: .container)` on both a view and a `GeometryProxy`;
and an `AVCaptureDevice.DiscoverySession` over
`.builtInOuterUltraWideCamera` and `.builtInInnerUltraWideCamera`.

The deployment-target gate in `vertical-bars.md` was checked separately with the
*real* `axisBehavior` rather than a stand-in, at an iOS 18 deployment target against
the 27.1 SDK — it compiles:

```bash
xcrun --sdk iphonesimulator swiftc -typecheck -target arm64-apple-ios18.0-simulator gate.swift
```

Not verified: the two Mac Catalyst known issues above are reported as Apple's, by
radar number. A bare `swiftc -target arm64-apple-ios27.1-macabi` did not resolve
SwiftUI at all here, so it is not a reproduction and is not presented as one.
