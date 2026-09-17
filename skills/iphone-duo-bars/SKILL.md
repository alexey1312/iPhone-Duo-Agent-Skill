---
name: iphone-duo-bars
description: >-
  Prepare navigation bars, toolbars and tab bars for iPhone Duo's vertical bars,
  where controls move to the side of the outer display and of the inner display
  in landscape. Use when a
  developer asks about vertical bars, bar item ordering, back or close button
  placement, pinned trailing or prominent actions, toolbar items without titles,
  axisBehavior, symbol-only items and badges, custom views in toolbars,
  toolbarVerticalEdge or verticalBarEdge, overflow menus and ToolbarOverflowMenu,
  visibilityPriority, toolbar or tab bar compression, custom UIToolbar or
  UINavigationBar instances, sheet toolbars and presentationPlacement, backgrounds
  under the bar with backgroundExtensionEffect, or opting out with
  toolbarVerticalBehavior. Covers SwiftUI and UIKit, based on Apple's "Raise the bar
  with iPhone Duo" and "Preparing your app for iPhone Duo".
---

# iPhone Duo vertical bars

On the outer display and on the inner display in landscape, iPhone Duo moves controls
that normally sit at the top and bottom to the side, keeping vertical space for content
and controls within reach. Only the inner display in portrait keeps horizontal bars.
Top to bottom the side stack is Dynamic Island, status bar, toolbar (with navigation
buttons), tab bar. (Tech Talk 111462, 0:28; Tech Talk 111466, 5:07; HIG *Designing for
iPhone Duo* › Vertical controls)

Read `references/vertical-bars.md` for the code; `references/api-availability.md` for
which parts compile with the selected SDK — `axisBehavior`, `toolbarVerticalEdge`,
compression behavior and the opt-out need the **iOS 27.1 SDK**, while titles, symbols,
badges, placements, `visibilityPriority` and `ToolbarOverflowMenu` work today.
Where the corner camera and the side controls physically sit:
`references/device-geometry.md`.

## How the system decides

- **Only container bars participate.** SwiftUI: `.toolbar` inside `NavigationStack`
  or `NavigationSplitView`. UIKit: `UINavigationController` and `UITabBarController`.
  Standalone `UIToolbar`, `UINavigationBar`, `UITabBar` content is not considered.
  (2:00)
- **One shared region.** Navigation, toolbar and tab bar controls stack into one
  vertical region. In split views only the detail column participates; inspectors
  get no bar of their own. The bar is aligned with the hardware and stays on the same
  side in right-to-left languages. (3:09)
- **Sheets differ per display.** On the outer display a sheet's toolbar goes vertical
  by default. On the inner display sheets are centered with horizontal bars;
  `presentationPlacement(.leading)` / `.trailing` (UIKit:
  `sheetPresentationController?.preferredPlacement`) moves a sheet to an edge, and
  only a trailing sheet receives a vertical bar. (3:58; *Preparing your app for iPhone
  Duo* › Optimize bars for vertical presentation)
- **Keyboard accessory bars stay with the keyboard.** (10:00)
- **Fixed width, flexible height.** Items with an icon go vertical; text-only items
  stay horizontal. The title is still required — it is used in overflow menus and
  expanded forms. (5:56)
- **Custom views stay horizontal by default.** (8:00)
- **Overflow runs bottom to top**, and toolbars compress before the tab bar by
  default. Overflow happens sooner on the outer display in landscape, with the
  keyboard up, and with Picture in Picture pinned at the top in open portrait.
  (11:40, 13:10)

## Audit checklist (per screen)

1. **Container.** Is every bar item owned by a navigation or tab container? Scanner
   rule `DUO007` finds standalone bars; move their items into the container.
2. **Order.** Top of the vertical bar: primary navigation (back or close), then
   prominent actions (done, save). Use `.cancellationAction` / leading item groups
   with `leftItemsSupplementBackButton = false` for close, and
   `.topBarPinnedTrailing` / `pinnedTrailingGroup` for prominent actions. Keep
   controls associated with the container they belong to. (4:29) Group related items
   with `ToolbarItemGroup` / `UIBarButtonItemGroup` instead of manual spacing, and keep
   controls next to the content they affect — Mail's list controls stay above the
   leading pane. (HIG › Vertical controls)
3. **Title and symbol on every item.** Provide both, even when only the symbol shows.
4. **Text that carries information stays horizontal.** A symbol plus redundant text →
   symbol only (use a badge for counts, iOS 26 badge API). Text with standalone value
   (a cart showing a total) → keep, and it stays in the horizontal bar. The system
   Edit button and wide controls such as segmented controls stay horizontal on their
   own. (9:00; 8:25; Tech Talk 111466, 6:20)
5. **Axis for items that change shape.** An item that switches between symbol and
   text (Select ↔ Done) → `.horizontalOnly`, and keep related items on the same axis.
   A custom view that has a vertical representation → `.verticalPreferred`. (8:00)
6. **Custom views fit.** Fixed bar width, or a vertically adapted layout keyed off
   `toolbarVerticalEdge` / `verticalBarEdge`. Flexible spacers collapse to zero
   vertically; fixed spacers keep their minimum. Legible with no scroll edge effect
   and with the Reduce Transparency background. (10:07)
7. **Overflow.** One overflow menu, and the ellipsis symbol belongs to it (scanner rule
   `DUO011`). A custom ellipsis menu is one of two things: a grab bag of secondary
   actions — move it into `ToolbarOverflowMenu` / `additionalOverflowItems` so people
   see one "more" instead of two — or a single named function such as Filter, which
   deserves its own symbol and title so it can survive in the vertical bar. (11:40)
8. **Compression.** Navigation-focused apps: default, or explicitly
   `.prefersTabBar` (toolbar compresses first). Task-oriented screens where actions
   matter more than tabs: `.toolbarVerticalCompressionBehavior(.prefersToolbarItems)` /
   `verticalBarCompressionBehavior = .prefersBarItems`. (12:23)
9. **Priority.** Set `visibilityPriority` on groups first, then items. Compose / New
   Note / primary creation: high. Status-bearing items (badged inbox): high, to
   preserve glanceability. Rare actions: low. Finer steps:
   `ToolbarItemVisibilityPriority(higherThan:)` / `(lowerThan:)`; UIKit's default is
   `.standard`. (13:10)
10. **Opt-out only where it fits.** Single-page, bottom-heavy layouts (Calculator-like)
    and sheets with a single close button — the sheet then stops short of the camera
    and the status bar repositions (Tech Talk 111466, 9:03). Not as a fix for items
    that overflow. (14:21) The behavior resolves per window or presentation: a
    `NavigationStack` uses its top view, a `TabView` its selected tab, a
    `NavigationSplitView` its trailing-most column; make it a stable choice, never a
    toggle on a view's state, and use `toolbarVisibility` to hide bars instead. UIKit:
    `preferredVerticalBarBehavior`, `childForPreferredVerticalBarBehavior`,
    `setNeedsUpdateOfVerticalBarConfiguration()`. Otherwise don't override the default
    placement; a full-width layout suits only immersive, non-scrolling screens that
    don't conflict with the Dynamic Island or status bar. (HIG › Vertical controls;
    Tech Talk 111466, 6:33)
11. **Backgrounds under the bar.** A hero image or full-bleed header extends under the
    vertical bar with `backgroundExtensionEffect()` / `UIBackgroundExtensionView`
    (iOS 26) rather than a manually stretched frame; scrollable foreground content
    stays inset. (*Preparing your app for iPhone Duo* › Optimize bars for vertical
    presentation; Tech Talk 111466, 6:33)

## Output

One recommendation per screen (not per item) in the format of
`references/recommendation-format.md`, listing the checklist steps that apply. Items
that need 27.1 APIs are marked *blocked* when the SDK lacks them; everything else can
ship now and improves bars on every iPhone.

## Verify

Pose matrix P1 (outer display: side controls), P2 (outer display landscape, keyboard
up), P3 (inner landscape: vertical bar), P4 (inner portrait: horizontal), P11 (right-to-left), P12 (Reduce Transparency)
from `references/pose-test-matrix.md`. Check which items overflow and in what order.
