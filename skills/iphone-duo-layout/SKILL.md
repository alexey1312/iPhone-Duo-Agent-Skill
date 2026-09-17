---
name: iphone-duo-layout
description: >-
  Use this skill when an app's layout or geometry breaks or wastes space on iPhone
  Duo's foldable inner display: layouts that should become multi-column in regular
  × regular size classes, NavigationSplitView or TabView sidebars on the inner
  screen, a phone-width column stuck in the middle, safe-area insets that differ
  left and right, content or floating controls crossed by the hinge in book or
  tabletop pose, the FaceTime camera covering UI, or video letterboxing on the
  wide inner screen. Also use it for the iOS 27.1 layout APIs: reservedRegions
  (division, occlusion, right-to-left mirroring), ReservedRegion /
  UIView.ReservedRegion, ArrangementView / UIArrangementViewController split or
  overlay with their ratio, edge and axis modifiers, and ConcentricRectangle /
  UICornerConfiguration. Follows Apple's iPhone Duo tech talks and documentation.
  Not for toolbar items or overflow menus, removing idiom or orientation checks,
  hinge-angle interactions, or generic SwiftUI and Auto Layout bugs unrelated to
  the foldable.
---

# iPhone Duo layout

Layout on iPhone Duo is ordinary adaptive layout pushed further: two displays with
different size classes, a hinge that divides the inner display when folded, and
cameras that occlude part of it. Start from system containers — most of the behavior
comes for free — and add custom work only where a container cannot express it.

Code: `references/layout-code.md`. Availability: `references/api-availability.md`
(reserved regions and arrangements need the **iOS 27.1 SDK**). Physical facts —
display sizes, where the cameras and fold sit, poses, drawing mockups:
`references/device-geometry.md` (never a layout input).

## 1. Size classes, not devices (Tech Talk 111461, 2:46)

- Outer display: like other iPhones. Inner display: regular × regular — room for
  sidebars and multiple columns.
- Drive layout from `horizontalSizeClass` / `verticalSizeClass` (environment in
  SwiftUI, trait collection in UIKit) and from the container size; never from
  orientation or idiom (`iphone-duo-adaptivity-audit` owns removing those).
- Design across a continuum of sizes (1:33). A fixed phone-width column centered on
  the inner display is a finding: propose two columns, a split view, or a grid.
- Keep functionality and state the same on both displays; show one more level of
  hierarchy on the inner display where it fits (Mail: list or message when closed,
  both when open). Don't design a layout per pose. (HIG › Best practices; Tech Talk
  111466, 3:42 and 7:34)
- Games: playable in every pose and filling the screen; prefer changing the aspect
  ratio over letterboxing or pillarboxing, else put artwork in the padding. (HIG ›
  Best practices)
- Video: 16:9 in landscape on the inner display leaves about a fifth of the height
  as letterbox — the 1.42 display is nowhere near 16:9 (derived,
  `references/device-geometry.md` › Aspect-ratio consequences). Design that band
  (controls, metadata, artwork) instead of leaving it black; it is a finding when a
  player centers a 16:9 frame and hides everything else.
- Support landscape on the outer display: it rotates like any iPhone and people set
  the device down like a tent (111461, 3:30). The inner display ignores supported
  orientations regardless, so portrait-only never bought anything there (`DUO021`).

## 2. Standard navigation and presentations (5:01; 111463 8:39)

- `NavigationSplitView` / `UISplitViewController` and `TabView` /
  `UITabBarController` adapt across every pose: columns collapse when closed, tile
  or overlay when open. `List` and `ScrollView` adapt to the fold.
- Inner display sidebar: `TabView { … }.defaultTabBarPlacement(.sidebar)` /
  `tabBarController.sidebar.preferredPlacement = .sidebar`. On iPhone this is an app
  choice with no user toggle; the system shows the sidebar when space allows. Check
  `sidebar.isAvailable` and surface sidebar-only destinations elsewhere when it is
  not. (WWDC26 278, 9:18)
- Sheets, popovers, context menus, alerts and action sheets adapt and are
  repositioned around reserved regions automatically. (111463 5:12) Sheets can
  present with vertical controls on the outer display, use horizontal bars on the
  inner display, and slide clear of the fold. (111466 8:36) On the inner display
  `presentationPlacement(.leading)` / `.trailing` (UIKit
  `sheetPresentationController?.preferredPlacement`, iOS 27.0) parks a sheet at an
  edge so the content behind it stays visible; `iphone-duo-bars` owns what that
  does to the sheet's toolbar.

## 3. Safe areas (111461, 6:06)

- Standard bars lay out outside the safe area and avoid the status bar and camera.
- Interactive foreground content stays inside the safe area.
- Background artwork extends past it (`ignoresSafeArea()` / `view.bounds`).
- Insets and layout margins are often **asymmetric**: never double one side
  (scanner rule `DUO006`); inset by all edges. Test in Split View.
- Custom UI that must claim as much space as possible without colliding with system
  UI (custom bars, edge-to-edge designs): `ReservedRegion` / `UIViewReservedRegion`
  (27.1, 8:08).
- Fit screen corners with `ConcentricRectangle` / `UICornerConfiguration` (iOS 26).

## 4. The hinge and reserved regions (111463)

**Design first** (1:29–5:12):

- Content and controls spanning the fold are harder to see — like a photo across a
  book's spine.
- Many interfaces flow around reserved regions naturally. Others need
  **displacement**: adjust the frame of existing elements. Move elements
  independently when they adapt alone, together when they work as a unit; avoid
  movement that breaks visual relationships.
- **Continuously scrolling content (articles, feeds) does not displace.** That also
  rules out re-flowing an article into two "book pages" split at the crease: the
  talk's guidance is to let scrolling content flow and to move discrete elements —
  floating buttons, overlays, custom controls — instead.
- Choose destinations by purpose and pose: book pose — alerts to the trailing side,
  near where they appear as the device closes; tabletop — viewing content on top,
  interactive controls on the bottom. Keep it contextual.
- Adapt more than position and size where it helps: a grid keeps outer margins and
  widens spacing around the hinge; a split view keeps an even split.
- Favor small adjustments over rearrangement while folding: controls that vanish or
  jump are hard to track. (HIG › Reserved regions)

**Then query** (6:39–7:50):

- `reservedRegions(kind: .division)` on a `GeometryProxy` (via `GeometryReader` or
  `onGeometryChange`) or on a `UIView`; use each region's `frame`.
- The fold is a **division** region: active only when folded, zero width when flat.
  `options: .includeInactive` returns it anyway — use that for high-level decisions
  such as preferring an even number of grid columns.
- **Occlusion** regions represent the FaceTime camera. The inner camera's region
  exists only while the camera is active (the UI moves aside); the outer camera's is
  always present and expands into the Dynamic Island for Live Activities. (HIG ›
  Reserved regions)
- Each region carries `frame` (already including `margins`, the extra room
  interactive content keeps), `isActive`, `kind` and `id`;
  `reservedRegions(kind:options:layoutDirectionBehavior:)` returns every region that
  intersects the view. (Apple documentation › `ReservedRegion`)
- Right-to-left: the camera does not move for a person's language, so SwiftUI
  mirrors the region frames by default and a `Layout` needs no special casing. Pass
  `layoutDirectionBehavior: .fixed` only when you place content in absolute
  coordinates on purpose. (Apple documentation › `ReservedRegion`)
- Adopt the query for the highest-priority manually laid out controls, not for every
  view (16:34).

## 5. Arrangements (111463, 9:20–16:09)

An arrangement is a layout container between navigation containers and content: it
places a primary and a secondary view from size classes, aspect ratio and active
division regions.

- `ArrangementView { primary } secondary: { secondary }` inside a `NavigationStack`;
  UIKit: `UIArrangementViewController` as the navigation controller's root with
  `setViewController(_:for: .primary / .secondary)`.
- **Split** (default): divides its bounds; horizontal when wider than tall, vertical
  when taller. `.split.axes(.horizontal)` restricts it; when it cannot split along its
  allowed axis it shows only one view. UIKit: `updateArrangement(.split.axes(…))`.
- **Overlay**: prefers content above or below, side by side when folded. Respond with
  `overlayArrangementZIndex` (UIKit: `state(for:)?.zIndex`), e.g. collapse the
  secondary view when it is on top.
- **Tuning** (Apple documentation › `ArrangementView`, `UIArrangementViewController`):
  `splitArrangementLayoutRatio(_:)` sizes a view by a fraction of the container
  (the view with the highest `layoutPriority` is sized first, the rest fill),
  `splitArrangementLayoutSize(minWidth:idealWidth:maxWidth:…)` by points; read
  `splitArrangementAxis` from the environment to re-lay out a child for a horizontal
  or vertical split. `overlayArrangementEdge(.trailing)` anchors an overlay's view
  when the fold turns the layers into a side-by-side layout. UIKit:
  `UISplitArrangement.DimensionRange`, `state(for:)` → `ViewState.isHidden` /
  `splitAxis` / `zIndex`, `placement(for:)`, `updateArrangement(_:animated:)`.
- **Choosing:** an existing `HStack`/`VStack` pattern → split; `ZStack` → overlay.
  Without one: clear foreground/background relationship where partially covering
  scrollable content is fine → overlay; main/detail where neither may be obscured →
  split.
- **Don't** put navigation containers (e.g. `NavigationSplitView`) inside an
  arrangement, and don't put an arrangement inside `List`, `ScrollView` or any
  container that could make part of it unreachable.

## Workflow

1. From the scan inventory and the code, list screens by layout shape: container-based,
   centered single column, custom split/overlay, manually positioned controls,
   full-bleed media.
2. For each, pick the smallest change that works on the pose matrix: container first,
   size-class adaptation second, arrangement third, reserved-region query last.
3. Recommend (`references/recommendation-format.md`), marking 27.1 APIs *blocked* when
   the SDK lacks them; apply after approval; build.
4. Verify with poses P1, P3, P5, P6, P7 and P8 from `references/pose-test-matrix.md`.

## Hinge data is not a layout input

`onHingeChange` / `UIHingeInteraction` report the live angle for interactions and
effects. For layout use arrangements and reserved regions. (Tech Talk 111464, 2:35)
