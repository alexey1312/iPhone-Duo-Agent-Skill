---
name: iphone-duo-layout
description: >-
  Use when an app's layout or geometry breaks or wastes space on iPhone Duo's
  foldable inner display: layouts that should become multi-column in regular ×
  regular size classes, NavigationSplitView or TabView sidebars, a phone-width
  column stuck in the middle, safe-area insets that differ left and right, content,
  floating controls, sheets, collection-view sections or WKWebView pages crossed by
  the hinge in book or tabletop pose, the FaceTime camera covering UI, or video
  letterboxing on the wide inner screen. Also use it for the iOS 27.1 layout APIs:
  reservedRegions (division, occlusion, right-to-left mirroring), ReservedRegion /
  UIView.ReservedRegion, ArrangementView / UIArrangementViewController split or
  overlay with their ratio, edge and axis modifiers, and corner-aware margins.
  Follows Apple's talks, documentation and forum answers. Not for toolbar items or
  overflow menus, removing idiom or orientation checks, hinge-angle interactions, or
  generic SwiftUI and Auto Layout bugs unrelated to the foldable.
---

# iPhone Duo layout

Layout on iPhone Duo is ordinary adaptive layout pushed further: two displays with
different size classes, a hinge that divides the inner display when folded, and
cameras that occlude part of it. Start from system containers — most of the behavior
comes for free — and add custom work only where a container cannot express it.

Code: `references/layout-code.md`. Availability: `references/api-availability.md`
(reserved regions, arrangements and `ContentMarginGuide` need the **iOS 27.1 SDK**,
which ships with Xcode 27.1 — on that toolchain they need a deployment-target gate,
not a blocked entry). Physical facts — display sizes, where the cameras and fold sit,
poses, drawing mockups: `references/device-geometry.md` (never a layout input).
Apple engineers' forum answers fill gaps the talks leave — collection views, web
views, sheets in folded poses — and rank below the talks
(`references/sources.md` › Developer Forums Q&A; cite them as *Forums 848036*).

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
- **Sheets through a fold** (Forums 848034, 847797): a presented sheet stays
  presented and adapts — never dismiss and re-present it for a pose. Folded, it
  moves to the leading side; flat, it is centred (*Booted*: x 8–467 pt in book
  pose). The placement applies in every pose, and there is no per-pose placement.
  If a design needs the trailing side while folded, set `preferredPlacement` from the
  active division region in `viewWillLayoutSubviews`, which runs again on a fold
  (`references/layout-code.md` › A sheet that follows the fold), and suggest an
  enhancement request. Update custom detents on a size-class change only when the
  content needs it, through `registerForTraitChanges` (Forums 848010).
- `.fullScreen` / `fullScreenCover` fills the app's own window scene, not the
  display: in Split View it covers only the app's own side (Forums 847874).
  `.overCurrentContext` applies only in regular width (Forums 847644).
- A `UINavigationController` app needs no new architecture: adapt the content inside
  it, for example with a `UIArrangementViewController` as a pushed screen
  (Forums 848055). Keep `UISplitViewController` for sidebar and content; an
  arrangement does not replace it (Forums 848000).

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
  For controls placed against the margins, UIKit's
  `view.layoutGuide(for: .margins(cornerAdaptation: .horizontal))` (iOS 26, no gate)
  moves them in from the rounded corners (Forums 848019). *Booted*: 16 pt on the
  leading edge with `.horizontal`, on the top with `.vertical`; an edge the safe area
  already insets does not change.
- **The fold is not in the safe area.** The division region adds no safe-area inset,
  no layout margin and no trait (Forums 847879; *Booted*: book pose leaves
  `safeAreaInsets` and `adjustedContentInset` unchanged). Code that waits for an inset
  to move a control off the fold waits forever: query the region.

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
- The fold is a **division** region: active only while the device is partially
  folded; flat, it is inactive and, in the talk's words, has a width of zero (7:32).
  `options: .includeInactive` returns it anyway — use that for high-level decisions
  such as preferring an even number of grid columns.
  Decide with `isActive`, or with the default active-only query, never with
  `frame.width`: the zero width is the fold line, while `frame` includes 20 pt of
  margin each side and measures 40 pt flat and folded alike (*Booted*,
  `references/device-geometry.md`).
- In landscape the fold is the middle of the display, not of the safe area: the
  84 pt trailing inset leaves 455.5 pt before the fold's frame and 371.5 pt after
  it. Anything centred in the safe area misses the crease by 42 pt — place against
  the region's frame, not against the middle (*Booted*).
- Tell book pose from tabletop by the shape of the active division —
  a vertical band is book, a horizontal one tabletop —
  not by the hinge (`references/layout-code.md` › Pose from the fold).
- **Occlusion** regions represent the FaceTime camera. The inner camera's region is
  active only while the camera is (the UI moves aside) and inactive otherwise, so
  `.includeInactive` returns it even then (8:12; HIG › Reserved regions). The outer
  camera's is always active and expands into the Dynamic Island for Live Activities.
  On the outer display the same query also returns the bar strip beside it,
  both with zero margins (*Booted*, `references/device-geometry.md`).
- Each region carries `frame` (already including `margins`, the extra room
  interactive content keeps), `isActive`, `kind` and `id`;
  `reservedRegions(kind:options:layoutDirectionBehavior:)` returns every region that
  intersects the view. (Apple documentation › `ReservedRegion`)
- Right-to-left: the camera does not move for a person's language, so SwiftUI
  mirrors the region frames by default and a `Layout` needs no special casing. Pass
  `layoutDirectionBehavior: .fixed` only when you place content in absolute
  coordinates on purpose. (Apple documentation › `ReservedRegion`)
- **Query during layout, not at scene transitions** (Forums 848035, 847876). Read the
  regions in `layoutSubviews` / `viewWillLayoutSubviews` (SwiftUI: the geometry
  reader); UIKit's observation tracking lays the view out again when they change.
  *Booted*: the reading view got a pass on fold and on unfold, a sibling that did not
  read them got none. Saving a fold state in `sceneWillResignActive` and restoring it
  in `sceneDidBecomeActive` is a finding: the regions are current when the scene
  returns, and a launch into a folded device needs no special path. Folding does not
  call `windowScene(_:didUpdateEffectiveGeometry:)` (*Booted*).
- There is no layout guide for the fold — reserved regions are the manual-layout
  API — and the region's rect is oriented: taller than wide is a vertical fold
  (Forums 847854). Prefer an arrangement, which does this evaluation itself.
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
  allowed axis it shows only the primary view (12:44). UIKit:
  `updateArrangement(.split.axes(…))`.
  The hidden secondary stays in the hierarchy and is still laid out at full size —
  its `onGeometryChange` fires — so never read visibility from its geometry
  (*Booted*: `.split.axes(.horizontal)` on the portrait outer display).
  In book pose the split moves its divider onto the fold, even against a
  `splitArrangementLayoutRatio`, and leaves the fold's 40 pt frame empty between
  the panes (*Booted*: 0.3 flat → 455.5 | 371.5 pt folded).
- **Overlay**: layers the views while no division is active, side by side when
  partially folded. The **primary** is the foreground: layered, it reads
  `overlayArrangementZIndex` 1 against the secondary's 0 and sits at the top leading
  corner at its own size (*Booted*, outer display). Respond to the z-index (UIKit:
  `state(for:)?.zIndex`): the talk makes its collapsible Up Next list the primary
  and collapses it while it floats over the player (13:44–14:17); the HIG also lets
  you collapse the secondary when it should not appear. `.overlay.axes(_:)` limits
  the axes it may go side by side along (SDK; UIKit `UIOverlayArrangement.axes`).
  Folded like a book, the primary takes the trailing side of the fold and the
  secondary the leading side, both at z-index 0, unless `overlayArrangementEdge`
  says otherwise (*Booted*; *Preparing your app for iPhone Duo* › Arrange views).
- **Both styles start from the unfolded layout.** Reserved regions arrive a few
  layout passes late, so an app launched folded first lays out layered or evenly
  split and only then moves to the fold (*Booted*). Code that samples the first
  layout — an `onAppear` measurement — sees the unfolded one.
- **Read the arrangement's environment one view down.** The view written directly in
  the `primary` or `secondary` closure reads the defaults — `overlayArrangementZIndex`
  0, `splitArrangementAxis` `nil` — whatever modifiers it carries; a view nested
  inside it, or the same view wrapped in a `VStack`, reads the real values. Apple's
  own samples (the talk's `UpNextView`, the documentation's `DetailsView`) read at
  that root, so copied as they are they never collapse or re-lay out.
  (*Booted*, Xcode 27.1 (27A9269), outer display, the repository's
  `arrangement_probe.swift`; the fix is in `references/layout-code.md`.)
- **Tuning** (Apple documentation › `ArrangementView`, `UIArrangementViewController`):
  `splitArrangementLayoutRatio(_:)` sizes a view by a fraction of the container
  (the view with the highest `layoutPriority` is sized first, the rest fill), or by
  a range per axis with `splitArrangementLayoutRatio(minHorizontal:idealHorizontal:…)`;
  `splitArrangementLayoutSize(minWidth:idealWidth:maxWidth:…)` sizes it by points,
  and `splitArrangementFixedLayoutSize(horizontal:vertical:)` also exists (SDK).
  Read `splitArrangementAxis` from the environment, one view down, to re-lay out a
  child for a horizontal or vertical split. `overlayArrangementEdge(.trailing)`
  anchors an overlay's view when the fold turns the layers into a side-by-side
  layout. UIKit: `UISplitArrangement.DimensionRange`, `state(for:)` →
  `ViewState.isHidden` / `splitAxis` / `zIndex`, `placement(for:)`,
  `updateArrangement(_:animated:)`. A UIKit ratio: copy the arrangement's
  `defaultViewProperties`, set `width.preferred = .fractional(0.3)`, write it back
  with `setViewProperties(_:for: .primary)` on a `var` arrangement, then
  `updateArrangement(_:)` (Forums 847990).
- Arrangements and reserved regions are not iPhone Duo-only: they work on every
  iPhone and iPad on iOS 27.1 (Forums 847644, 848021), so the same code path runs
  everywhere.
- **Choosing:** an existing `HStack`/`VStack` pattern → split; `ZStack` → overlay.
  Without one: clear foreground/background relationship where partially covering
  scrollable content is fine → overlay; main/detail where neither may be obscured →
  split.
  Not every two-column interface needs an arrangement:
  a list → detail that is really navigation stays in `NavigationSplitView`,
  which already adapts across displays.
  An arrangement is for two views inside one destination.
  (Follows from 111463 placing arrangements between navigation containers and
  content, and from the rule below.)
- **Don't** put navigation containers (e.g. `NavigationSplitView`) inside an
  arrangement, and don't put an arrangement inside `List`, `ScrollView` or any
  container that could make part of it unreachable.

## 6. Content the system does not move (Forums)

Containers, `List`, `ScrollView` and system presentations adapt to the fold.
These do not, and the talks say nothing about them:

- **Collection views** (Forums 847879): `UICollectionView` and compositional layouts
  have no automatic fold avoidance. Scrolling grids need not avoid the fold — let them
  scroll across it. Adjust only a section that does not scroll across the fold's axis
  (a row of summary cards), from the collection view's own reserved regions, and
  invalidate the layout when the fold changes (`references/layout-code.md`). Lining a
  whole grid up with the fold is a refinement, not a requirement; the talk's Fitness
  grid shows how (111463, 5:50). Hide content per size class in the data source or the
  layout, never with a 0.1 pt section (Forums 848018).
- **Web content** (Forums 848036): CSS `env(safe-area-inset-*)` and the web view's
  content insets do not include the fold, and the Viewport Segments and Device
  Posture APIs cannot be enabled in `WKWebView` — they are experimental Safari flags
  (Forums 847644; *Booted*: all three unavailable). For a page the app controls,
  query the regions in the host and pass them in as CSS custom properties, separate
  from the safe-area insets. A page the app does not control keeps scrolling across
  the fold; keep native controls that float over it clear of the fold.
- **Custom sheets, panels and accessories**: a hand-built bottom sheet or floating
  panel must avoid the fold itself (Forums 847644). Place a `UITabAccessory` from the
  division region when partially folded (Forums 847814).
- **Accessibility**: a custom layout that the fold splits in two may need
  accessibility containers or sort priorities for a sensible VoiceOver order
  (Forums 847644).
- **The camera hole**: a custom element over the camera's reserved region can lose
  touches there (Forums 847644). Query `.occlusion` and keep controls out of it.

## Workflow

1. From the scan inventory and the code, list screens by layout shape: container-based,
   centered single column, custom split/overlay, manually positioned controls,
   full-bleed media, collection views (`compositional layout` in the inventory) and
   web content (`web views`).
2. For each, pick the smallest change that works on the pose matrix: container first,
   size-class adaptation second, arrangement third, reserved-region query last.
3. Recommend (`references/recommendation-format.md`), marking 27.1 APIs *blocked* when
   the SDK lacks them; apply after approval; build.
4. Verify with poses P1, P3, P5, P6, P7 and P8 from `references/pose-test-matrix.md`.
   `scripts/duo_pose.py shoot` reaches P1, P5 and P3 from a script (third-party
   `hinge` CLI; ask first): look in the book-pose screenshot for anything that sits
   on the fold. P6 needs rotation, which only Device Hub does.

## Hinge data is not a layout input

`onHingeChange` / `UIHingeInteraction` report the live angle for interactions and
effects. For layout use arrangements and reserved regions. (Tech Talk 111464, 2:35)
