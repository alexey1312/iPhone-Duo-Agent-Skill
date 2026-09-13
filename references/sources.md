# Sources

Every recommendation in these skills traces to one of the sessions or pages below.
Cite the session and chapter timestamp when you recommend a change, so the developer
can watch the exact passage. The Human Interface Guidelines have no timestamps: cite
the page and section (for example *HIG, Designing for iPhone Duo › Vertical
controls*).

Chapter summaries and code samples are published on each session page. When a
code sample and the SDK disagree, the SDK wins — see `api-availability.md`.

## Prepare your app for iPhone Duo — Tech Talk 111461

<https://developer.apple.com/videos/play/tech-talks/111461/>

| Time | Chapter | Takeaway |
| --- | --- | --- |
| 0:30 | Build with the latest SDK | Apps run unmodified, but screen use improves per SDK: the iOS 27 SDK extends the app left of the status bar on the inner display; the iOS 27.1 SDK reaches the screen edge and lays standard navigation and toolbar buttons out vertically. |
| 1:17 | Get started in Xcode | Xcode 27.1, iPhone Duo simulator in Device Hub, on-screen controls to open, close, rotate and fold. |
| 1:33 | Adopt flexible layouts | No assumptions about display size or capability from the user interface idiom; design across a continuum of sizes. |
| 2:46 | Use size classes | Outer display behaves like other iPhones; inner display is regular × regular. The inner display does not honor supported interface orientations. |
| 3:57 | Avoid screen assumptions | Don't reference the main screen (ambiguous, being deprecated). Use environment, trait collection, scene bounds, `window?.windowScene?.screen`. Concentricity APIs fit the screen corners. |
| 5:01 | Adopt standard navigation | `NavigationSplitView`, `UISplitViewController`, `TabView`, `UITabBarController` adapt across every pose; sidebar placement on the inner display; sheets, popovers, context menus and alerts adapt. |
| 6:06 | Respect safe areas | Bars sit outside the safe area; interactive content inside it; backgrounds extend past it. Insets are often asymmetric — handle each side, test Split View. |
| 8:08 | Use reserved regions | iOS 27.1 `ReservedRegion` (SwiftUI) / `UIViewReservedRegion` (UIKit) let custom UI claim space without colliding with system UI. |
| 9:12 | Next steps | Xcode's app modernization skill is called App Resizability in Xcode 27.1 and covers SwiftUI and iPhone Duo. |

## Raise the bar with iPhone Duo — Tech Talk 111462

<https://developer.apple.com/videos/play/tech-talks/111462/>

| Time | Chapter | Takeaway |
| --- | --- | --- |
| 0:28 | Why bars move to the side | The wide aspect ratio moves top and bottom controls to the side; consistent on the inner display in landscape; horizontal again in portrait. |
| 2:00 | Opt in to vertical bars | Rebuild with the latest SDK and use container-provided bars. Custom `UIToolbar`/`UINavigationBar`/`UITabBar` content is not considered. |
| 3:09 | Shared bar region | Navigation, toolbar and tab bar share one region. In split views only the detail column participates; inspectors get no bar; sheets differ per display; the bar is hardware-aligned and does not flip for right-to-left. |
| 4:29 | Order items | Top: back or close (`.cancellationAction`; UIKit leading group with `leftItemsSupplementBackButton = false`), then prominent actions (`.topBarPinnedTrailing` / `pinnedTrailingGroup`). |
| 5:56 | Prepare toolbar content | Fixed width, flexible height. Items with an icon go vertical, text-only items stay horizontal. Always provide a title. |
| 8:00 | Control the axis | `axisBehavior(.verticalPreferred)` / `.horizontalOnly`; custom views stay horizontal by default. |
| 9:00 | Prefer symbol-only items | Use badges instead of text-plus-symbol; keep text that carries standalone information (a cart total) horizontal. |
| 10:07 | Adapt custom views | Fit the fixed width or adapt layout; read `toolbarVerticalEdge` / `verticalBarEdge`. No scroll edge effect by default; background with Reduce Transparency; flexible spacers are zero vertically. |
| 11:40 | Manage overflow | Overflow happens more on the outer display in landscape and with the keyboard. Toolbars compress first by default; `toolbarVerticalCompressionBehavior` / `verticalBarCompressionBehavior`. Consolidate into `ToolbarOverflowMenu` / `additionalOverflowItems`; the ellipsis is for overflow only. |
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

## Design for iPhone Duo — Tech Talk 111466

<https://developer.apple.com/videos/play/tech-talks/111466/>

| Time | Chapter | Takeaway |
| --- | --- | --- |
| 0:28 | Design principles | Many poses; controls move to the outer edge of the display to maximize vertical space; folded, content moves away from the center; Split View multitasking and video PiP put apps at other aspect ratios, so support resizability. |
| 3:42 | Adapting your design | No custom layout per pose — design for compact and regular; layout margins and safe area insets; a bespoke pose layout must keep functionality and hierarchy. |
| 5:07 | Positioning controls | Toolbars, tab bars and controls along the side, sharing that space with Live Activities and the status bar; overflow when it runs out; controls too wide for the vertical space are the exception. |
| 6:33 | Designing for the outer display | Most content needs an offset so controls don't hide it — safe areas provide it; immersive, non-scrolling UIs may center on the full display; a full-width background can hold inset text. |
| 7:34 | Designing for the inner display | Use the width: split views surface more hierarchy, or rearrange into two columns. |
| 8:36 | Sheet behavior | Outer display: sheets can present with vertical controls. Inner display: horizontal bars. Folded: sheets slide over to avoid resting in the fold. |
| 9:28 | Fold avoidance | System components nudge interactive elements away from the center when partially folded; except for scrollable content, keep interactive elements away from the hinge. |

## Designing for iPhone Duo — Human Interface Guidelines

<https://developer.apple.com/design/human-interface-guidelines/designing-for-iphone-duo>
— new page, change log September 9, 2026. The page renders with JavaScript; its text is
in <https://developer.apple.com/tutorials/data/design/human-interface-guidelines/designing-for-iphone-duo.json>.
It links Tech Talks 111466, 111462 and 111463.

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
`device-geometry.md`, shipped with the readiness, bars, layout and displays skills.

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

Related: *Get the most out of Device Hub* (WWDC26), *Build a great camera experience
for iPhone Duo* (Tech Talk 111465), *Make your UIKit app more flexible* (WWDC25).
