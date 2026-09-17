# API availability

The iPhone Duo talks target **Xcode 27.1 and the iOS 27.1 SDK**. Several APIs they
show do not exist in earlier SDKs, and at least one code sample does not match the
SDK spelling. Before writing code against any API from a talk:

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

Status on 2026-09-17: Xcode 27 (27A266a) shipped on September 14 with the iOS 27.0
SDK; the Xcode 27.1 beta is "coming later this month". *Preparing your app for iPhone
Duo* is already published. Calendar: `sources.md`.

## Measured snapshot

Checked on **Xcode 27.0 beta 6 (27A5252f), iPhoneOS 27.0 SDK**. Re-run the script;
this table ages.

| Area | Present in 27.0 SDK | Absent from 27.0 SDK (announced for 27.1) |
| --- | --- | --- |
| Adaptivity | `effectiveGeometry`, `registerForTraitChanges`, `deviceMotionBody`, `headingBody` | — |
| Corners | `ConcentricRectangle`, `UICornerConfiguration` | — |
| Navigation | `defaultTabBarPlacement`, `prominentTabIdentifier`, `navigationBarMinimization`, `toolbarMinimizationBehavior`, `preferredImageVisibility` | `barMinimizationBehavior` (see below) |
| Bars | `topBarPinnedTrailing`, `pinnedTrailingGroup`, `leftItemsSupplementBackButton`, `additionalOverflowItems`, `ToolbarOverflowMenu`, `visibilityPriority` | `axisBehavior`, `toolbarVerticalEdge`, `verticalBarEdge`, `toolbarVerticalCompressionBehavior`, `verticalBarCompressionBehavior`, `toolbarVerticalBehavior`, `preferredVerticalBarBehavior` |
| Layout | — | `reservedRegions`, `ReservedRegion`, `UIViewReservedRegion`, `ArrangementView`, `arrangementViewStyle`, `UIArrangementViewController`, `overlayArrangementZIndex` |
| Displays | `sceneAccessory`, `onAvailabilityChange`, `UIWindowSceneActivationAction` (Swift: `UIWindowScene.ActivationAction`) | `onHingeChange`, `UIHingeInteraction`, `CameraCaptureAccessory` |

So with Xcode 27.0 you can already: remove legacy screen/orientation/idiom code,
adopt scene lifecycle, fix asymmetric safe-area math, move items into container
bars, give every item a title and symbol, set `visibilityPriority`, consolidate
overflow into `ToolbarOverflowMenu`, place close/prominent items correctly, branch
biometric copy on `LAContext.biometryType`, and ship a widget or Live Activity for
StandBy. Vertical-bar axis tuning, reserved regions, arrangements, the hinge, the
camera capture accessory and the camera direction coordinator wait for the 27.1 SDK.

**Documented, not yet measured** (added 2026-09-17 from Apple's documentation pages;
`sdk_api_check.py` checks every name below, but nobody has run it against a 27.1 SDK
yet):

| Area | Symbol | Documented availability |
| --- | --- | --- |
| Bars | `ToolbarItemAxisBehavior`, `ToolbarVerticalBehavior`, `UIVerticalBarBehavior`, `UIVerticalBarEdge` | iOS 27.1 |
| Bars | `presentationPlacement` (SwiftUI), `UISheetPresentationController.preferredPlacement` | iOS 27.0 |
| Bars | `backgroundExtensionEffect`, `UIBackgroundExtensionView` | iOS 26 |
| Layout | `splitArrangementAxis`, `overlayArrangementEdge`, `splitArrangementLayoutRatio`, `splitArrangementLayoutSize`, `UISplitArrangement`, `UIOverlayArrangement` | iOS 27.1 |
| Displays | `UIHinge` (its update type is `UIHingeInteraction.Update`) | iOS 27.1 |
| Displays | `UISceneAccessory`, `registerSceneAccessory`, `UISceneAccessoryRegistration` | iOS 27.0 |
| Cameras | `AVCaptureDeviceDirectionCoordinator`, `AVCaptureDeviceDirectionMap`, `AVCaptureDeviceDescriptor` (AVKit), `builtInOuterUltraWideCamera`, `builtInInnerUltraWideCamera` | iOS 27.1 (Tech Talk 111465; the device types are annotated 27.1 beta) |
| Cameras | `dynamicAspectRatio`, `AVCaptureDevice.RotationCoordinator` | iOS 26 / iOS 17 |
| Adaptivity | `LAContext.biometryType` (LocalAuthentication) | iOS 11 |

## Known talk-versus-SDK mismatch

*Modernize your UIKit app* (11:30) shows:

```swift
navigationItem.barMinimizationBehavior = .always
navigationItem.barMinimizationSafeAreaAdjustment = .never
```

The iOS 27.0 SDK declares instead a `UIBarMinimization` configuration value:

```swift
// UIKit (iOS 27.0 SDK)
var minimization = navigationItem.navigationBarMinimization
minimization.minimizationBehavior = .onScrollDown   // .automatic, .never, .onScrollDown, .onScrollUp
minimization.safeAreaAdjustment = .disabled         // .automatic, .enabled, .disabled
navigationItem.navigationBarMinimization = minimization

// SwiftUI (iOS 27.0 SDK)
.toolbarMinimizationBehavior(_:for:)
.toolbarMinimizationSafeAreaAdjustment(_:for:)
```

There is no `.always` in that SDK. Verify against the SDK you build with before
using either spelling; a later SDK may differ again. The same caution applies to
every sample in `sources.md`.

## Swift spellings of Objective-C names

Talks and headers often use Objective-C class names. Swift may nest them:
`UIWindowSceneActivationAction` is `UIWindowScene.ActivationAction`,
`UIWindowSceneActivationConfiguration` is `UIWindowScene.ActivationConfiguration`,
and the `UIViewReservedRegion` the first Tech Talk names is documented as
`UIView.ReservedRegion` (with `UIView.ReservedRegion.Kind` and `.QueryOptions`); the
hinge update type is `UIHingeInteraction.Update`. The flat names fail with "has been
renamed". `sdk_api_check.py` searches both headers and Swift interfaces, so a symbol
can be *found* under its Objective-C name; the compiler is the final word on the
Swift spelling.

## Typechecked samples

The skills' code samples that use iOS 26/27.0 APIs were typechecked with
`xcrun --sdk iphonesimulator swiftc -typecheck` against the iOS 27.0 SDK: adaptivity
replacements, bar placements, badges, `visibilityPriority`, `ToolbarOverflowMenu`,
`additionalOverflowItems`, `navigationBarMinimization`, sidebar placement,
`prominentTabIdentifier`, safe-area insets, `ConcentricRectangle`, scene activation.
Samples using 27.1 APIs could not be checked and are reproduced from the session pages
or from Apple's documentation (each sample says which).
