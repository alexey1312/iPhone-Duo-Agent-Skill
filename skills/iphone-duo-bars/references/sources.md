# Sources

Every recommendation in these skills traces to one of the sessions or pages below.
Cite the session and chapter timestamp when you recommend a change, so the developer
can watch the exact passage. The Human Interface Guidelines and Apple's documentation
articles have no timestamps: cite the page and section (for example *HIG, Designing
for iPhone Duo › Vertical controls* or *Preparing your app for iPhone Duo › Optimize
bars for vertical presentation*). Hardware facts cite the tech specs or App Store
Connect (`device-geometry.md`).

Chapter summaries and code samples are published on each session page. When a
code sample and the SDK disagree, the SDK wins — see `api-availability.md`.

## Prepare your app for iPhone Duo — Tech Talk 111461

<https://developer.apple.com/videos/play/tech-talks/111461/>

| Time | Chapter | Takeaway |
| --- | --- | --- |
| 0:30 | Build with the latest SDK | Apps run unmodified, but screen use improves per SDK: the iOS 27 SDK extends the app left of the status bar on the inner display; the iOS 27.1 SDK reaches the screen edge and lays standard navigation and toolbar buttons out vertically. |
| 1:17 | Get started in Xcode | Xcode 27.1, iPhone Duo simulator in Device Hub, on-screen controls to open, close, rotate and fold. |
| 1:33 | Adopt flexible layouts | No assumptions about display size or device capability from the user interface idiom (the sentence at 2:34 — on iPhone Duo that includes biometrics: Touch ID, not Face ID, see `device-geometry.md`); design across a continuum of sizes. |
| 2:46 | Use size classes | Outer display behaves like other iPhones; inner display is regular × regular. The inner display does not honor supported interface orientations. |
| 3:30 | Orientation per display | The outer display rotates like any iPhone — a reason to support landscape, since people set the device down like a tent. The inner display does not honor supported interface orientations. |
| 3:57 | Avoid screen assumptions | Don't reference the main screen (ambiguous, being deprecated). Use environment, trait collection, scene bounds, `window?.windowScene?.screen`. Concentricity APIs fit the screen corners. |
| 4:37 | `UIRequiresFullScreen` | Still honored, but the app resizes anyway when the device opens or closes; supported orientations are respected, but the app scales on the inner display, including in Split View multitasking. |
| 5:01 | Adopt standard navigation | `NavigationSplitView`, `UISplitViewController`, `TabView`, `UITabBarController` adapt across every pose; sidebar placement on the inner display; sheets, popovers, context menus and alerts adapt. |
| 6:06 | Respect safe areas | Bars sit outside the safe area; interactive content inside it; backgrounds extend past it. Insets are often asymmetric — handle each side, test Split View. |
| 7:44 | Test Split View in Device Hub | Preview on the inner display, drag the app by the home indicator to one side of the screen, then to the other: vertical content can appear on either side of the app. |
| 8:08 | Use reserved regions | iOS 27.1 `ReservedRegion` (SwiftUI) / `UIViewReservedRegion` (UIKit) let custom UI claim space without colliding with system UI. |
| 9:12 | Next steps | Xcode's app modernization skill is called App Resizability in Xcode 27.1 and covers SwiftUI and iPhone Duo. Confirmed shipped: `xcrun agent skills export` yields `app-resizability` with `references/{idiom,orientation,safe-area,scene-lifecycle,uiscreen}-task.md`, whose `safe-area-task.md` already directs agents to `traitCollection.verticalBarEdge` and `@Environment(\.toolbarVerticalEdge)`. Xcode 27.1 also ships a `device-interaction` subagent skill for driving a simulator or device. |

## Raise the bar with iPhone Duo — Tech Talk 111462

<https://developer.apple.com/videos/play/tech-talks/111462/>

| Time | Chapter | Takeaway |
| --- | --- | --- |
| 0:28 | Why bars move to the side | The wide aspect ratio moves top and bottom controls to the side; consistent on the inner display in landscape; horizontal again in portrait. |
| 2:00 | Opt in to vertical bars | Rebuild with the latest SDK and use container-provided bars. Custom `UIToolbar`/`UINavigationBar`/`UITabBar` content is not considered. |
| 3:09 | Shared bar region | Navigation, toolbar and tab bar share one region. In split views only the detail column participates; inspectors get no bar; sheets differ per display; the bar is hardware-aligned and does not flip for right-to-left. |
| 4:29 | Order items | Top: back or close (`.cancellationAction`; UIKit leading group with `leftItemsSupplementBackButton = false`), then prominent actions (`.topBarPinnedTrailing` / `pinnedTrailingGroup`). |
| 5:56 | Prepare toolbar content | Fixed width, flexible height. Items with an icon go vertical, text-only items stay horizontal. Always provide a title. |
| 8:00 | Control the axis | `axisBehavior(.verticalPreferred)` / `.horizontalOnly`; the system Edit button stays horizontal automatically; custom views stay horizontal by default. |
| 9:00 | Prefer symbol-only items | Use badges instead of text-plus-symbol; keep text that carries standalone information (a cart total) horizontal. |
| 10:00 | Keyboard accessory bars | Accessory bars remain attached to the keyboard rather than moving to the vertical axis. |
| 10:07 | Adapt custom views | Fit the fixed width or adapt layout; read `toolbarVerticalEdge` / `verticalBarEdge`. No scroll edge effect by default; background with Reduce Transparency; flexible spacers are zero vertically. |
| 11:40 | Manage overflow | Overflow happens more on the outer display in landscape, with the keyboard, and with Picture in Picture in open portrait. Toolbars compress first by default; `toolbarVerticalCompressionBehavior` / `verticalBarCompressionBehavior`. Consolidate into `ToolbarOverflowMenu` / `additionalOverflowItems`; the ellipsis is for overflow only. |
| 13:10 | Prioritize visibility | Items overflow bottom to top; `visibilityPriority` on groups first, then items. Frequent actions and badged status items overflow last. |
| 14:21 | When to opt out | Bottom-heavy single-page apps, single-control sheets: `toolbarVerticalBehavior(.disabled)` / `preferredVerticalBarBehavior`. |

## Strike a pose with adaptive layouts on iPhone Duo — Tech Talk 111463

<https://developer.apple.com/videos/play/tech-talks/111463/>

| Time | Chapter | Takeaway |
| --- | --- | --- |
| 0:27 | Reserved regions | Each display has its own size class; the hinge and cameras are reserved regions, treated like iPadOS window controls. |
| 1:29 | Designing around the hinge | Partially folded, the hinge divides the inner display; content spanning the fold is harder to see. |
| 2:26 | Displacement patterns | Adjust frames around reserved regions — independently or together; avoid excessive movement; continuously scrolling content does not displace. |
| 4:00 | Choose where content moves | Book pose: alerts to the trailing side. Tabletop: top region for viewing, bottom for interaction. |
| 5:12 | Adapt content | The system repositions action sheets, alerts, menus, popovers; split views split evenly; grids keep outer margins and widen spacing at the hinge. |
| 6:39 | Query reserved regions | `GeometryProxy.reservedRegions(kind:)` (GeometryReader or `onGeometryChange`), `UIView.reservedRegions(kind:)`; use `frame`. |
| 7:50 | Division and occlusion | Active vs inactive (`options: .includeInactive`); the fold is a division region, zero width when flat; occlusion regions represent the FaceTime camera. |
| 8:39 | System containers | Navigation containers and `List`/`ScrollView` adapt to the fold for free. |
| 9:20 | Arrangements | A layout container between navigation and content, arranging a primary and secondary view from size classes, aspect ratio and division regions. |
| 11:17 | ArrangementView | `ArrangementView { primary } secondary: { … }` inside `NavigationStack`; UIKit `UIArrangementViewController` as navigation root. |
| 12:00 | Split arrangement | `.arrangementViewStyle(.split)`; `.split.axes(.horizontal)`; a split that can't split shows one view; UIKit `updateArrangement(_:)`. |
| 13:21 | Overlay arrangement | `.overlay` stacks above or below, side by side when folded; `overlayArrangementZIndex` / `state(for:).zIndex`. |
| 14:39 | Choose | HStack/VStack → split, ZStack → overlay; foreground/background → overlay; main/detail → split. |
| 16:09 | When not to | No navigation containers inside an arrangement; no arrangement inside a scroll view or list. |

## Leverage multiple displays and scenes on iPhone Duo — Tech Talk 111464

<https://developer.apple.com/videos/play/tech-talks/111464/>

| Time | Chapter | Takeaway |
| --- | --- | --- |
| 0:49 | Respond to the hinge | `onHingeChange` (SwiftUI), `UIHingeInteraction` (UIKit): status closed / partially open / fully open, plus a continuous angle. |
| 1:18 | Drive an effect | Check for a non-nil hinge, filter `.partiallyOpen`, reset in the else branch. |
| 2:35 | Hinge data versus layout | Hinge data drives interactions and effects; layout uses arrangements and reserved regions. |
| 2:59 | Split view multitasking | All apps participate; a new video-plus-apps stacked layout; handle with size classes and scene geometry. |
| 3:38 | Multiple scenes | First iPhone with multiple app windows; none can be created on the outer display. Handle scene request errors; `UIWindowSceneActivationAction` hides itself when unavailable. |
| 4:22 | Scene accessories | Content on several displays at once; availability is system-controlled and can change any time. |
| 5:00 | Camera capture accessory | Outer-display UI while the main UI stays inside; requires full screen on the inner display with an active camera session; register on the camera view. |
| 5:34 | Teleprompter example | `.sceneAccessory { CameraCaptureAccessory(isEnabled:) { … } .onAvailabilityChange { … } }`, toolbar toggle disabled while unavailable. |

## Build a great camera experience for iPhone Duo — Tech Talk 111465

<https://developer.apple.com/videos/play/tech-talks/111465/>

| Time | Chapter | Takeaway |
| --- | --- | --- |
| 0:30 | Two front cameras | Both are square sensors with an ultrawide field of view: the outer ultrawide camera and the inner ultrawide camera, the first under-display camera on iPhone. |
| 1:01 | Virtual Front Camera | An `AVCaptureDevice.DiscoverySession` with position `.front` and the wide or ultra wide device type returns the Virtual Front Camera, an `AVCaptureDevice` that switches between the inner camera (device open) and the outer camera (closed) by itself. Existing front-camera code works unchanged. |
| 1:53 | Physical device types | `builtInOuterUltraWideCamera` and `builtInInnerUltraWideCamera` expose each camera fully: inner 1080p up to 60 fps, outer up to 4K at 120 fps. The virtual camera offers only the common subset (1080p, 60 fps); depth only through the individual cameras. With individual cameras, switching on open/close is the app's job. |
| 2:53 | Direction coordinator | `AVCaptureDeviceDirectionCoordinator` reports which cameras face the user. `position` still says where a camera sits (both front cameras are `.front`), not where it points: a front camera can face away, and the rear cameras become a selfie camera when the open device is turned around. |
| 4:02 | Create a coordinator | Needs the app's `UIView`, the device types to monitor and a change handler. As the app moves between displays the forward- and backward-facing sets flip. |
| 4:49 | Two displays at once | An app showing UI on both displays (scene accessories) creates one coordinator per view; each reports directions relative to its own view. |
| 5:37 | Main actor and descriptors | The coordinator is tied to a view and main-actor isolated; the handler must not call AVFoundation directly. It hands out `AVCaptureDeviceDescriptor`, a Sendable representation to pass to the camera actor. |
| 6:16 | In the change handler | Reconfigure the `AVCaptureSession` to keep streaming from the forward-facing camera, decide preview mirroring from direction (mirror a forward-facing rear camera), update the UI. |
| 7:03 | Polished preview | A full-field-of-view rear preview on the inner display leaves extra space: offset the preview and group controls there, or fill with `videoGravity`. `dynamicAspectRatio` on `AVCaptureDevice` picks a landscape ratio from the square front sensors. |
| 8:08 | Rotation | Adopt `AVCaptureDevice.RotationCoordinator`; it updates when the app moves displays. Then disable camera-sensor-orientation compensation (enabled on every front camera on iPhone Duo) for performance. |
| 8:49 | Next steps | Build with the iOS 27.1 SDK; decide how to switch cameras on open/close; adopt the direction coordinator to go beyond the virtual camera; test the preview on iPhone Duo. |

## Design for iPhone Duo — Tech Talk 111466

<https://developer.apple.com/videos/play/tech-talks/111466/>

| Time | Chapter | Takeaway |
| --- | --- | --- |
| 0:28 | Design principles | Many poses; controls move to the outer edge of the display to maximize vertical space; folded, content moves away from the center; Split View multitasking and video PiP put apps at other aspect ratios, so support resizability. |
| 3:42 | Adapting your design | No custom layout per pose — design for compact and regular; layout margins and safe area insets; a bespoke pose layout must keep functionality and hierarchy. |
| 5:07 | Positioning controls | Toolbars, tab bars and controls along the side, sharing that space with Live Activities and the status bar; overflow when it runs out; controls too wide for the vertical space (a text button, a segmented control) stay in the navigation bar. |
| 6:33 | Designing for the outer display | Most content needs an offset so controls don't hide it — safe areas provide it; immersive, non-scrolling UIs may center on the full display; a full-width background can hold inset text. |
| 7:34 | Designing for the inner display | Use the width: split views surface more hierarchy, or rearrange into two columns. |
| 8:36 | Sheet behavior | Outer display: sheet controls move to the side by default; disabling the vertical bar suits single-button sheets, and the sheet then stops short of the camera while the status bar repositions. Inner display: horizontal bars in both orientations. Folded: sheets slide over to avoid resting in the fold. |
| 9:28 | Fold avoidance | System components nudge interactive elements away from the center when partially folded; except for scrollable content, keep interactive elements away from the hinge. |

## Designing for iPhone Duo — Human Interface Guidelines

<https://developer.apple.com/design/human-interface-guidelines/designing-for-iphone-duo>
— new page, change log September 9, 2026. The page renders with JavaScript; its text is
in <https://developer.apple.com/tutorials/data/design/human-interface-guidelines/designing-for-iphone-duo.json>.
It links Tech Talks 111466, 111462 and 111463, the developer guide *Preparing your app
for iPhone Duo*, and the API pages for `ReservedRegion`, `UIView.ReservedRegion`,
`ArrangementView` and `UIArrangementViewController` (checked 2026-09-17).

| Section | Guidance |
| --- | --- |
| Introduction | Two displays, each with its own front camera, and a center hinge. Still designing for iPhone: iOS patterns apply. Standard components plus resizing support adapt with little adjustment. |
| Anatomy | Closed, people use the outer display and the system puts toolbars and tab bars on the side; controls stay on the side when the device opens in landscape. The outer front camera is in the corner, always visible, vertically aligned with the side controls; the inner camera is behind the display, hidden until active. |
| Device poses | Held partially folded like a book, placed on a surface, or standing on its edges (six poses illustrated). Don't design a layout per pose: compact width for the outer display, regular width for the inner display. |
| Best practices | Build to resize (size classes, layout margins, safe area insets; no fixed widths or display-specific dependencies). Keep functionality and state consistent across displays; optionally show one more hierarchy level on the inner display (Mail: list or message closed, both open). Same functionality in every pose. Follow the system vertical layout for bars. Games: playable in every pose, fill the screen, keep text and control sizes consistent, prefer changing the aspect ratio over letterboxing or pillarboxing, else add artwork to the padding. |
| Reserved regions | Outer front camera: always present, expands into the Dynamic Island for Live Activities; side controls account for it. Inner front camera: only while active; the UI moves aside. Folding region: when partially open it divides the inner display, excluding the center. Alerts, context menus and sheets move for the fold; split views adapt column widths and margins to the inner display's symmetry. Prefer adaptive containers (Notes split view); even number of grid columns; reserved-region APIs for custom content; avoid extreme layout changes while folding — small adjustments over rearrangement. |
| Split views | Expand on the inner display, collapse to one pane on the outer display (`NavigationSplitView`, `UISplitViewController`). |
| Arrangement views | Split: horizontal when wider than tall, vertical when taller. Overlay: side by side when partially folded, otherwise primary atop secondary. Split axes can be limited; the overlay secondary can collapse. `HStack`/`VStack` → split, `ZStack` → overlay. Keep navigation containers outside. |
| Vertical controls | Toolbars, tab bars and navigation controls move to the side everywhere except the inner display in portrait. Side stack, top to bottom: Dynamic Island, status bar, toolbar (with navigation buttons), tab bar. In Split View multitasking each app puts controls on its outer edge. Controls stay aligned with the hardware: same position relative to the outer camera, same side in right-to-left languages. Handle the asymmetric content area with safe areas, including controls on the opposite edge. Keep relative positions consistent across poses. |
| Vertical controls — items | Top: primary navigation (Back, Close), then prominent actions (Done); original groupings kept, with system spacing between top-bar and bottom-bar items. Overflow runs bottom to top; set `ToolbarItemVisibilityPriority` / `UIBarButtonItemVisibilityPriority` by group, then item; keep frequent actions (Compose, New Note) and badged items visible longest. Don't override the default bar placement. Full-width layouts suit immersive, non-scrolling UIs if nothing conflicts with the Dynamic Island or status bar (Calculator); a full-width background can hold inset scrolling content. Group with `ToolbarItemGroup` / `UIBarButtonItemGroup`, no manual spacing. Keep controls near the content they affect (Mail list controls stay above the leading pane). Title and symbol for every item that isn't text-only (`Label` / `UIBarButtonItem`); minimize text buttons — text labels stay in a horizontal bar. Limited space: navigation-focused keeps the tab bar and overflows toolbar items (default); task-oriented minimizes the tab bar. One system overflow menu (`ToolbarOverflowMenu` / `additionalOverflowItems`); ellipsis only for overflow. |

## Hardware facts

Displays, dimensions, cameras, hinge position and poses — with Apple's
[tech specs](https://www.apple.com/iphone-duo/specs/) and
[newsroom announcement](https://www.apple.com/newsroom/2026/09/apple-unveils-iphone-duo/)
kept apart from diagram measurements and third-party claims — are in
`device-geometry.md`, shipped with every skill.

## Modernize your UIKit app — WWDC26 session 278

<https://developer.apple.com/videos/play/wwdc2026/278/>

| Time | Chapter | Takeaway |
| --- | --- | --- |
| 0:34 | App adaptivity | iPhone apps are fully resizable in iPhone Mirroring and on iPad. Audit scene lifecycle, main screen, idiom, orientation. |
| 2:10 | App lifecycle | UIScene lifecycle is required with the latest SDKs; without it the app no longer launches. |
| 2:51 | Main screen | Screen from the window scene; pass screens in; `traitCollection.displayScale`; automatic trait tracking; `registerForTraitChanges`; `effectiveGeometry` and `windowScene(_:didUpdateEffectiveGeometry:)`; view bounds. |
| 5:19 | Effective geometry (code sample) | `windowScene.effectiveGeometry` and `windowScene(_:didUpdateEffectiveGeometry:)` for scene-level available space; view bounds at 5:35. |
| 5:46 | Full-screen games | `UIRequiresFullScreen` is honored on iPhone in resizable environments from iOS 27, enabling discrete resizing. |
| 6:17 | Idiom | Not meaningful for layout; phone idiom apps are resizable on iPad. |
| 6:50 | Orientation | Supported orientations are a preference, ignored when resizable; iPhone Mirroring always reports portrait. |
| 7:55 | Body protocols | `UIView` conforms to Core Motion / Core Location body protocols: `deviceMotionBody`, `headingBody`. |
| 8:19 | Testing | Device Hub and Previews resize mode; real devices for iPhone Mirroring and iPad. |
| 9:18 | Tab bars and sidebars | `sidebar.preferredPlacement = .sidebar`, `sidebar.isAvailable`, `prominentTabIdentifier`. |
| 10:52 | Navigation bars | Bar minimization behavior; re-evaluate `.soft` scroll edge overrides. |
| 12:37 | Menus | `preferredImageVisibility`. |
| 14:07 | Agentic coding | Xcode's modernization skill; export with `xcrun agent skills export`. |

Related: *Get the most out of Device Hub* (WWDC26), *Make your UIKit app more
flexible* (WWDC25), *Support the Center Stage front camera in your iOS app* (WWDC26).

## Preparing your app for iPhone Duo — Apple documentation

<https://developer.apple.com/documentation/technologyoverviews/preparing-your-app-for-iphone-duo>
— published by 2026-09-17, re-read 2026-09-19. No timestamps: cite by section.
Note that the page's own Overview still says the iPhone Duo simulator "requires
Xcode 27.1, coming later this month"; Xcode 27.1 beta shipped on September 18, so
that clause is stale at the source. Cite the requirement, not the schedule.

| Section | Guidance |
| --- | --- |
| Overview | Resizing is the key feature; apps that already resize on iPad, Mac or in iPhone Mirroring are well on their way. Build with Xcode 27.1 to use all of the screen — with earlier SDKs the app doesn't extend under the status bar and camera. The iPhone Duo simulator in Device Hub requires Xcode 27.1. |
| Address common layout and resizing considerations | Check every view, sheet and popover on both displays — closed, open, partially folded — and rotate in each pose. Prefer system containers (split views, tab bars, arrangement views, navigation stacks); size views relative to their container, not fixed iPhone dimensions; compute from the scene's or view's bounds, not the screen; Auto Layout; automatic trait tracking of `horizontalSizeClass` / `verticalSizeClass`; no `userInterfaceIdiom` or `UIInterfaceOrientation` for layout. |
| Optimize bars for vertical presentation | Bars go vertical on the outer display when closed and for some leading/trailing views on the inner display. Use container-provided bars (`toolbar(content:)` on `NavigationStack` / `NavigationSplitView`; toolbar items on a view controller inside a navigation controller), never a custom `UIToolbar`, `UINavigationBar` or `UITabBar`. Inspectors: horizontal. Split views: horizontal for sidebar and content, vertical for detail. Sheets: vertical by default on the outer display (`toolbarVerticalBehavior(_:)` / `preferredVerticalBarBehavior` disable it); on the inner display horizontal for centered or leading placement, vertical for trailing (`presentationPlacement(_:)` / `UISheetPresentationController.preferredPlacement`). Read `toolbarVerticalEdge` / `verticalBarEdge` in custom views; extend a hero or background image under a vertical bar with `backgroundExtensionEffect()` / `UIBackgroundExtensionView`. |
| Organize items in your bars | Top: primary navigation (Back/Close — automatic with a navigation controller; custom via `cancellationAction` / `leadingItemGroups`), then prominent actions (`topBarPinnedTrailing` / `pinnedTrailingGroup`). `axisBehavior` decides inclusion in vertical bars; `visibilityPriority` the overflow order; `ToolbarOverflowMenu` / `additionalOverflowItems` put items straight into the overflow menu. Representation: vertical → icon; horizontal → icon or title, preferring the icon; overflow → icon and title; a title-only item and a custom-view item are never presented vertically. |
| Arrange views in different poses | `ArrangementView` / `UIArrangementViewController` with split and overlay styles. Split: side by side when the container is wider than tall, primary on top otherwise, adjusted around the folding region. Overlay: layered while no division region is active (closed or fully open); partially open, the primary view goes to the trailing or bottom side of the fold and the secondary to the leading or top side. Limit axes with `.split.axes(.horizontal)` / `updateArrangement(.split.axes(.horizontal))`. Don't place an arrangement view inside a navigation split view, list or scroll view. |
| Adapt to reserved regions in your views | Divisions (the fold) and occlusions (the inner camera while active; the outer camera always). SwiftUI: `GeometryProxy.reservedRegions(kind:options:layoutDirectionBehavior:)`; UIKit: `UIView.reservedRegions(kind:options:)`; inspect `frame`. A region can be active or inactive — the fold is active only when the device is partially open. |
| Improve your app's camera handling | Capture from the outer, inner and rear cameras; the camera in use may point the other way after the device opens, closes or rotates (*Choosing a camera by the direction it faces*). Fully open and capturing with the rear camera, the app can show content on the outer display (*Registering a camera capture accessory on iPhone Duo*). |

## Apple documentation pages

Cite by page and section. Availability annotations as published on 2026-09-17.

- [Choosing a camera by the direction it faces](https://developer.apple.com/documentation/avkit/choosing-a-camera-by-the-direction-it-faces) (AVKit) — the virtual front camera is a virtual device (`isVirtualDevice`; `activePrimaryConstituent` names the streaming camera). `AVCaptureDeviceDirectionCoordinator(view:deviceTypes:)` lists every built-in camera the app captures from, rear cameras included (the virtual front camera is left out; list the two physical front types instead); keep it alive while the view is on screen; one coordinator per preview view. `AVCaptureDeviceDirectionMap.forwardFacingDeviceDescriptors` is the set to pick from; resolve a descriptor with `AVCaptureDevice(uniqueID:)` on the session actor and handle a `nil` result. Mirroring: set `automaticallyAdjustsVideoMirroring = false` before `isVideoMirrored`, and only when position and direction disagree; reapply after reconnecting an input. Create a new `RotationCoordinator` for each device.
- [Registering a camera capture accessory on iPhone Duo](https://developer.apple.com/documentation/avfoundation/registering-a-camera-capture-accessory-on-iphone-duo) (AVFoundation) — SwiftUI `sceneAccessory { CameraCaptureAccessory(isEnabled:) { … } .onAvailabilityChange { … } }` on the capture view. UIKit `UISceneAccessory.cameraCapture(sceneConfiguration:userInfo:)` + `registerSceneAccessory(_:)` → `UISceneAccessoryRegistration` (`isAvailable`, observable; `isEnabled`), `unregisterSceneAccessory(_:)`; the accessory scene's session role is `windowCameraCaptureAccessory`; `connectionOptions.sceneAccessoryUserInfo` carries the shared model. The system presents the top-most registration of a kind; content goes away when capture stops, the app leaves the foreground or the device closes; different accessory kinds never compete. Simulator has no camera — test on a device.
- [TN3192: Migrating your iPad app from the deprecated UIRequiresFullScreen key](https://developer.apple.com/documentation/technotes/tn3192-migrating-your-app-from-the-deprecated-uirequiresfullscreen-key) (revised 2026-08-13) — from iOS 27 the key no longer opts out of resizing; the scene resizes discretely instead (`effectiveGeometry.coordinateSpace.bounds` changes when the drag ends). `UIRequiresFullScreenIgnoredStartingWithVersion` keeps the old behavior on earlier iOS. `isInteractivelyResizing` / `onInteractiveResizeChange(_:)`, `UISceneSizeRestrictions` / `windowResizability(_:)`, `prefersInterfaceOrientationLocked`. A launch screen is required for App Store submission on iOS 27.
- API reference, as declared by the **iOS 27.1 SDK (Xcode 27.1, 27A9269)** and measured with `sdk_api_check.py` on 2026-09-19: [`ReservedRegion`](https://developer.apple.com/documentation/swiftui/reservedregion) (`frame` includes `margins`; `isActive`; `kind` `.division` / `.occlusion`; `id`; `QueryOptions.includeInactive`; regions are mirrored for right-to-left by default, `layoutDirectionBehavior: .fixed` opts out), [`UIView.ReservedRegion`](https://developer.apple.com/documentation/uikit/uiview/reservedregion), [`ArrangementView`](https://developer.apple.com/documentation/swiftui/arrangementview) (`arrangementViewStyle`, `splitArrangementLayoutRatio`, `splitArrangementLayoutSize`, `splitArrangementFixedLayoutSize`, `overlayArrangementEdge`, environment `splitArrangementAxis` and `overlayArrangementZIndex`), [`UIArrangementViewController`](https://developer.apple.com/documentation/uikit/uiarrangementviewcontroller) (`UISplitArrangement` / `UIOverlayArrangement`, `ViewState.isHidden` / `splitAxis` / `zIndex`, `placement(for:)`), [`UIHinge`](https://developer.apple.com/documentation/uikit/uihinge) / [`UIHingeInteraction`](https://developer.apple.com/documentation/uikit/uihingeinteraction) (`angle` in radians; `Status` `.closed`, `.partiallyOpen`, `.fullyOpen`, `.unknown`; `update.hinge == nil` outside a hinge hierarchy; `isEnabled`), [`CameraCaptureAccessory`](https://developer.apple.com/documentation/swiftui/cameracaptureaccessory), [`UISceneAccessory`](https://developer.apple.com/documentation/uikit/uisceneaccessory) (iOS 27.0), [`ToolbarItemVisibilityPriority`](https://developer.apple.com/documentation/swiftui/toolbaritemvisibilitypriority) (iOS 27.0; `.automatic` / `.low` / `.high`, `init(higherThan:)` / `init(lowerThan:)`), [`ToolbarItemAxisBehavior`](https://developer.apple.com/documentation/swiftui/toolbaritemaxisbehavior), [`toolbarVerticalBehavior(_:)`](https://developer.apple.com/documentation/swiftui/view/toolbarverticalbehavior(_:)) (resolved per window or presentation: `NavigationStack` by its top view, `TabView` by the selected tab, `NavigationSplitView` by the trailing-most column; a stable choice, not a per-state toggle), [`ToolbarVerticalCompressionBehavior`](https://developer.apple.com/documentation/swiftui/toolbarverticalcompressionbehavior) (`.prefersTabBar` / `.prefersToolbarItems`), [`toolbarVerticalEdge`](https://developer.apple.com/documentation/swiftui/environmentvalues/toolbarverticaledge) (`HorizontalEdge?`, `nil` where no vertical bar exists), [`UIVerticalBarEdge`](https://developer.apple.com/documentation/uikit/uiverticalbaredge), [`preferredVerticalBarBehavior`](https://developer.apple.com/documentation/uikit/uiviewcontroller/preferredverticalbarbehavior) (with `childForPreferredVerticalBarBehavior`, `setNeedsUpdateOfVerticalBarConfiguration()`), [`presentationPlacement(_:)`](https://developer.apple.com/documentation/swiftui/view/presentationplacement(_:)) (iOS 27.0; sheets only), [`backgroundExtensionEffect()`](https://developer.apple.com/documentation/swiftui/view/backgroundextensioneffect()) (iOS 26), [`builtInOuterUltraWideCamera`](https://developer.apple.com/documentation/avfoundation/avcapturedevice/devicetype-swift.struct/builtinouterultrawidecamera) / `builtInInnerUltraWideCamera` (discoverable only through a discovery session), [Device Hub](https://developer.apple.com/documentation/xcode/device-hub).
- [Xcode 27.1 beta release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-27_1-release-notes) — cited by radar number, not by timestamp. Swift 6.4; SDKs for iOS/iPadOS 27.1 and tvOS/watchOS/macOS/visionOS 27; requires macOS Tahoe 26.6 or later. Known issues that change what can be verified: StandBy unavailable in the iPhone Duo Simulator runtime (187708663); most app extensions cannot run or debug there (187708767); first launch can take several minutes (187708500); iOS 27.1 APIs fail to compile for Mac Catalyst (185924957); a target on iOS 27.1 gets no Mac Catalyst run destination (187046347). New: a **Display** group in the Previews canvas overrides picker (182598534).
- [App Store Connect screenshot specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications) — iPhone Duo sizes; uploads "later this year". Numbers in `device-geometry.md`.
- [Apple unveils iPhone Duo](https://www.apple.com/newsroom/2026/09/apple-unveils-iphone-duo/) (newsroom, 2026-09-09) — Split View with two apps and two windows of one app on iPhone for the first time; StandBy on either display "even when it's not charging", with new Calendar and Weather faces; the Dock, Lock Screen controls and app navigation move to the side; both displays share the same aspect ratio; ships October 23 on iOS 27.1.

## Release calendar (as of 2026-09-19)

| Date | Event |
| --- | --- |
| September 9 | iPhone Duo announced; *Get ready for iPhone Duo* page, six Tech Talks (111461–111466) and *Designing for iPhone Duo* published; App Store Connect adds iPhone Duo screenshot sizes. Apple also states that from **April 2027** apps uploaded to App Store Connect must be built with the iOS 27 SDK or later. |
| September 14 | Xcode 27 (27A266a) and iOS 27.0 (24A437) ship. Neither release-notes page mentions iPhone Duo; the 27.0 SDK has no Duo-specific API. |
| September 16–17 | Online Group Labs (`meet-with-apple/285`, `/286`). No transcripts published, so nothing in them is citable. Apple also ships the 27.2 betas of every OS on September 16 — 27.1 is not the newest SDK for long. |
| **September 18** | **Xcode 27.1 beta (27A9269)** with the **iOS 27.1 SDK** (27.1, build 24A94403), Swift 6.4, the **iPhone Duo simulator device type** (`iPhone19,4`) and the **iOS 27.1 simulator runtime** (24A94401). Apple news *Build for iPhone Duo with new resources*: Figma and Sketch design kits plus an iPhone Duo product bezel added to Apple Design Resources, and in-person workshops open. |
| September 23 | Developer-forum Q&As: Photos & Camera, SwiftUI, UIKit. |
| September 28 – October 27 | In-person *Workshop: Optimize your app for iPhone Duo* at Apple Developer Centers. Meet with Apple now carries an **iPhone Duo** topic filter: <https://developer.apple.com/events/view/upcoming-events> |
| October 16 | Pre-orders. |
| October 23 | iPhone Duo ships on iOS 27.1. App Store Connect asset uploads for iPhone Duo "later this year". |

There is **no iOS 27.1 OS release-notes page**: Apple's index goes iOS 27 →
iOS 27.2 beta, so the Xcode 27.1 beta release notes are the source for what 27.1
changed. Apple's own *Preparing your app for iPhone Duo* still carries the stale
line "The iPhone Duo simulator in Device Hub requires Xcode 27.1, coming later this
month" — it shipped on September 18. Do not repeat that sentence.

## Design resources

[Apple Design Resources](https://developer.apple.com/design/resources/) carries the
iOS & iPadOS 27 UI Kit (Figma and Sketch), the App Icon Template for
iOS/iPadOS/watchOS 27, SF Symbols 27, and an **iPhone Duo product bezel**
(Photoshop and PNG, `Bezel-iPhone-Duo.dmg`). Use the official bezel for mockups
rather than measuring a third-party one (`device-geometry.md`).

## Background reading (not a citation source)

Blake Crosley, [*iPhone Duo for Developers: The 1.42 Problem and the SDK Gap*](https://blakecrosley.com/blog/iphone%2Dduo-for-developers)
(September 9, 2026, updated September 15) — the point-size arithmetic from App Store
Connect, the SDK-tier summary of the talks, the release calendar and the Touch ID
observation. Every fact it contributes to these skills is re-attributed to the Apple
artifact it rests on (tech specs, App Store Connect, the talks, TN3192); what remains
inference is labelled so in `device-geometry.md`. Do not cite the post itself in a
recommendation.
