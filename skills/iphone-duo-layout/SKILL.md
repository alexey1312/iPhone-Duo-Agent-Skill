---
name: iphone-duo-layout
description: >-
  Use this skill when an app's screen layout and geometry break or waste space on
  iPhone Duo's foldable inner display: layouts that should become multi-column in
  regular × regular size classes, NavigationSplitView or TabView sidebars on the
  inner screen, a phone-width column stuck in the middle, safe-area insets that
  differ left and right, content or floating controls crossed by the hinge in book
  or tabletop pose, or the FaceTime camera covering UI. Also use it for the iOS
  27.1 layout APIs: reservedRegions (division and occlusion),
  ReservedRegion/UIViewReservedRegion, ArrangementView/UIArrangementViewController
  split or overlay, and ConcentricRectangle/UICornerConfiguration. The skill
  follows Apple's iPhone Duo adaptive-layout tech talks. Do not use it for toolbar
  items, overflow menus or bar-button priority, for removing idiom or orientation
  checks, for hinge-angle interactions, or for general SwiftUI or Auto Layout bugs
  that have nothing to do with the foldable.
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
  inner display, and slide clear of the fold. (111466 8:36)

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
- **Choosing:** an existing `HStack`/`VStack` pattern → split; `ZStack` → overlay.
  Without one: clear foreground/background relationship where partially covering
  scrollable content is fine → overlay; main/detail where neither may be obscured →
  split.
- **Don't** put navigation containers (e.g. `NavigationSplitView`) inside an
  arrangement, and don't put an arrangement inside `List` or `ScrollView`.

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
