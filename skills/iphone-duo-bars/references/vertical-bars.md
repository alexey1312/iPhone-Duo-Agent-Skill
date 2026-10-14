# Vertical bars — code

Samples from Tech Talk 111462 as published on the session page, plus a few from
Apple's documentation (marked). APIs marked **27.1** were absent from the iOS 27.0
SDK; confirm with `scripts/sdk_api_check.py`.
Samples marked *Forums* put an Apple engineer's forum answer into code
(`sources.md` › Developer Forums Q&A); they are this repository's code and typecheck
against the iOS 27.1 SDK (`scripts/probes/forum_samples_probe.swift`).

## Opt in: use container bars (2:24, 2:39)

```swift
// SwiftUI — toolbar inside a navigation container
var body: some View {
    NavigationStack {
        ContentView()
            .toolbar {
                ToolbarItem(placement: .bottomBar) { /* ... */ }
            }
    }
}
```

```swift
// UIKit — content of standalone bars is not considered
let toolbar = UIToolbar()          // ✗ not part of the vertical bar
toolbar.items = [/* ... */]

// ✓ let the navigation controller own the toolbar
toolbarItems = [/* ... */]
navigationController?.setToolbarHidden(false, animated: false)
```

## Back or close at the top (5:00)

```swift
// SwiftUI
.toolbar {
    ToolbarItem(placement: .cancellationAction) { /* close */ }
}

// UIKit
navigationItem.leftItemsSupplementBackButton = false
navigationItem.leadingItemGroups = [UIBarButtonItemGroup(/* ... */)]
```

## Custom back button (Forums 847875)

Only the chevron changes: keep the system back button, which joins the vertical bar
by itself. A back item that really is custom asks for the vertical bar — 27.1.

```swift
@MainActor func keepSystemBackButton(_ navigationController: UINavigationController, chevron: UIImage) {
    let appearance = UINavigationBarAppearance()
    appearance.configureWithDefaultBackground()
    appearance.setBackIndicatorImage(chevron, transitionMaskImage: chevron)
    navigationController.navigationBar.standardAppearance = appearance
    navigationController.navigationBar.scrollEdgeAppearance = appearance
}

@MainActor func customBackItem(_ viewController: UIViewController, backButton: UIButton) {
    let back = UIBarButtonItem(customView: backButton)
    back.axisBehavior = .verticalPreferred
    viewController.navigationItem.leftBarButtonItem = back
}
```

## Prominent actions next (5:24)

```swift
// SwiftUI
.toolbar {
    ToolbarItem(placement: .topBarPinnedTrailing) { /* done */ }
}

// UIKit
navigationItem.pinnedTrailingGroup = UIBarButtonItemGroup(/* ... */)
```

## Sheets (3:58; Preparing your app › Optimize bars — documentation samples)

```swift
// Inner display: put the sheet at an edge so the map stays visible.
// Only a trailing sheet receives a vertical bar; leading and centered stay horizontal.
Map()
    .sheet(isPresented: $isPresented) {
        PlaceDetailView()
            .presentationDetents([.medium, .large])
            .presentationPlacement(.leading)              // iOS 27.0
    }

// UIKit
sheet.sheetPresentationController?.preferredPlacement = .leading

// Outer display: a sheet with a single close button keeps its horizontal bar — 27.1
SheetContent()
    .toolbarVerticalBehavior(.disabled)
```

### A sheet on the side it came from (regular width)

A design pattern from a third-party post (Nil Coalescing, 2026-10-04), not from Apple.
The tapped tile's column picks the side. `LazyVGrid` fills each row from the leading
edge, so the column index also holds in right-to-left languages. A trailing sheet
gets a vertical bar and a centred or leading one a horizontal bar, so the sheet's
items must work on both axes.

```swift
struct TrailBoard: View {
    @Environment(\.horizontalSizeClass) private var widthClass
    @State private var openTrail: Trail?
    let trails: [Trail]

    private var columnCount: Int { widthClass == .regular ? 5 : 2 }

    var body: some View {
        NavigationStack {
            ScrollView {
                LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: columnCount)) {
                    ForEach(trails) { trail in
                        Button { openTrail = trail } label: { TrailTile(trail: trail) }
                    }
                }
            }
            .navigationTitle("Trails")
            .sheet(item: $openTrail) { trail in
                TrailSheet(trail: trail)
                    .presentationPlacement(side(of: trail))   // iOS 27.0
                    .presentationDetents([.large])            // the default; see below
            }
        }
    }

    private func side(of trail: Trail) -> PresentationPlacement {
        guard widthClass == .regular,
              let index = trails.firstIndex(where: { $0.id == trail.id }) else {
            return .automatic                                 // compact width: the system decides
        }
        let column = index % columnCount
        if column * 2 + 1 == columnCount { return .center }   // the middle of an odd count
        return column * 2 < columnCount ? .leading : .trailing
    }
}
```

`presentationDetents([.large])` restates the default. It is here for one
*Unverified* reason. On the iOS 27.1 beta, a third party saw `.trailing` sheets
without explicit detents lose their vertical bar, with controls under the status bar
and camera. Writing out the detent fixed it in that testing.
Keep the line only if P3 or P5 shows the collision without it.

### A single-control sheet keeps its horizontal bar — 27.1

Put the opt-out on the top view inside the sheet's own `NavigationStack`. It resolves
for that presentation, so the board behind the sheet keeps its vertical bar
(`toolbarVerticalBehavior(_:)` documentation).

```swift
struct TrailSheet: View {
    @Environment(\.dismiss) private var dismiss
    let trail: Trail

    var body: some View {
        NavigationStack {
            TrailMap(trail: trail)
                .navigationTitle(trail.name)
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button(role: .close) { dismiss() }    // iOS 26: the standard Close label
                    }
                }
                .toolbarVerticalBehavior(.disabled)           // this sheet only
        }
    }
}
```

The two samples above are fragments:
`Trail`, `TrailTile` and `TrailMap` are placeholders.
Their iOS 27.x calls are in `scripts/probes/api_shapes_probe.swift`,
which typechecked clean on 2026-10-14 against the iOS 27.1 SDK (Xcode 27.1, 27A9269).

## Axis behavior — 27.1 (8:08, 8:36, 8:52)

```swift
// A custom view that has a vertical representation
ToolbarItem { ProfileView() }
    .axisBehavior(.verticalPreferred)

let item = UIBarButtonItem(customView: ProfileView())
item.axisBehavior = .verticalPreferred

// An item that switches between symbol and text: keep it horizontal
ToolbarItem { SelectOrDoneButton() }
    .axisBehavior(.horizontalOnly)

item.axisBehavior = .horizontalOnly
```

## Badges instead of text (9:27)

```swift
// SwiftUI
ToolbarItem(/* ... */) {
    InboxButton()
        .badge(7)
}

// UIKit (iOS 26)
let item = UIBarButtonItem(/* ... */)
item.badge = .count(7)
```

## Read the vertical bar edge — 27.1 (10:36; `toolbarVerticalEdge` documentation)

The value is the system's preferred edge whether or not a bar is visible right now,
and `nil` (UIKit: `.unspecified`) wherever the system never places a vertical bar.

```swift
// SwiftUI — keep a custom palette on the same side as the system bar
struct ContentView: View {
    @Environment(\.toolbarVerticalEdge) var toolbarVerticalEdge   // HorizontalEdge?

    var body: some View {
        FloatingToolPalette()
            .frame(maxWidth: .infinity,
                   alignment: toolbarVerticalEdge == .trailing ? .trailing : .leading)
    }
}

// UIKit
switch traitCollection.verticalBarEdge {          // .leading, .trailing, .unspecified
case .trailing: alignPalette(.trailing)
case .leading: alignPalette(.leading)
default: alignPalette(.trailing)
}
```

## A custom item that joins the vertical bar — 27.1 (8:00, 10:07)

A custom view stays in the horizontal bar by default (8:00).
To move it to the vertical bar, give its item `.verticalPreferred`.
Let the view pick its layout from `toolbarVerticalEdge`:
side by side when the value is `nil`, stacked when the value is an edge.
The stacked form must fit the bar's fixed width (10:07).

```swift
// SwiftUI — a stroke-width menu joins the vertical bar; the slider stays in the horizontal bar
struct SketchScreen: View {
    @State private var strokeWidth = 4.0
    @State private var opacity = 1.0

    var body: some View {
        NavigationStack {
            Canvas { _, _ in }
                .navigationTitle("Sketch")
                .toolbar {
                    ToolbarItem(placement: .bottomBar) {
                        Menu {
                            Picker("Stroke width", selection: $strokeWidth) {
                                ForEach([2.0, 4.0, 6.0], id: \.self) { Text("\(Int($0)) pt") }
                            }
                        } label: {
                            StrokeWidthLabel(width: strokeWidth)
                        }
                    }
                    .axisBehavior(.verticalPreferred)   // moves custom content out of the horizontal bar

                    ToolbarItem(placement: .bottomBar) {
                        Slider(value: $opacity) { Text("Opacity") }
                            .frame(width: 140)
                    }
                    .axisBehavior(.horizontalOnly)      // keeps the slider in the horizontal bar
                }
        }
    }
}

struct StrokeWidthLabel: View {
    @Environment(\.toolbarVerticalEdge) private var verticalEdge   // nil: no vertical bar
    let width: Double

    var body: some View {
        let layout = verticalEdge == nil
            ? AnyLayout(HStackLayout()) : AnyLayout(VStackLayout(spacing: 2))
        layout {
            RoundedRectangle(cornerRadius: width / 2).frame(width: 22, height: width)
            Text("\(Int(width)) pt").font(.caption2)
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Stroke width, \(Int(width)) points")
    }
}
```

Typechecked on 2026-10-14 against the iOS 27.1 SDK (Xcode 27.1, 27A9269);
the same code is in `scripts/probes/api_shapes_probe.swift`.
The overflow menu shows an item by its title and symbol
(*Preparing your app* › Organize items in your bars).
This custom label supplies neither,
and this repository has not measured how such an item looks in the overflow menu.

**Inside a toolbar item, switch the layout on the edge only if the item goes to the
vertical bar.**
`toolbarVerticalEdge` is the preferred edge for the whole window or presentation,
whether or not a bar is visible (`toolbarVerticalEdge` documentation).
It is not the edge of the bar that holds the item.
*Booted*, on the outer display closed and on the inner display flat
(`scripts/probes/toolbar_edge_probe.swift`):

| Item | Bar it sat in | `toolbarVerticalEdge` |
| --- | --- | --- |
| `Menu` with a custom label, `.verticalPreferred` | vertical, trailing | `.trailing` |
| The same `Menu`, `.automatic` (outer display only) | horizontal, bottom | `.trailing` |
| `Slider`, `.horizontalOnly` | horizontal, bottom | `.trailing` |
| Custom view, `.automatic` | horizontal, bottom | `.trailing` |
| The `.verticalPreferred` menu, the slider and the custom view, under `toolbarVerticalBehavior(.disabled)` | horizontal, bottom | `nil` |

A label that stacks for every non-`nil` value therefore stacks in the horizontal bar too.
The `.automatic` menu did exactly that.
Keep the layout of an item in the horizontal bar side by side.
Views outside the toolbar read the edge as before, for example to align a palette.
Check in P1 and P3 that the `.verticalPreferred` item really sits in the vertical bar.

## A bar that must stay custom — 27.1 (Forums 847835, 847644)

Migrate to container bars first. When a bar must stay custom, put it where the
system bar would go and keep it there as the edge changes.
`bar(onEdge:extent:)` is that slot: *Booted*, inner display in landscape, a 56 pt
trailing region sat at x 875–931 inside the 84 pt trailing inset and started at
y 120, below the status-bar strip; with no vertical bar, a bottom region sat 20 pt
above the bottom edge.

```swift
final class PlayerViewController: UIViewController {
    private let transportBar = TransportBarView()          // a UIStackView of bar buttons
    private var barEdge: NSDirectionalRectEdge?
    private var barConstraints: [NSLayoutConstraint] = []

    override func viewDidLoad() {
        super.viewDidLoad()
        transportBar.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(transportBar)
        transportBar.addInteraction(UILargeContentViewerInteraction())
        registerForTraitChanges(UITraitCollection.systemTraitsAffectingVerticalBarEdge) { (self: Self, _) in
            self.view.setNeedsLayout()
        }
    }

    override func viewWillLayoutSubviews() {
        super.viewWillLayoutSubviews()
        let edge: NSDirectionalRectEdge
        switch traitCollection.verticalBarEdge {
        case .leading: edge = .leading
        case .trailing: edge = .trailing
        default: edge = .bottom                 // no vertical bar in this pose
        }
        guard edge != barEdge else { return }
        barEdge = edge
        let guide = view.layoutGuide(for: .bar(onEdge: edge, extent: 56))
        NSLayoutConstraint.deactivate(barConstraints)
        barConstraints = [
            transportBar.leadingAnchor.constraint(equalTo: guide.leadingAnchor),
            transportBar.trailingAnchor.constraint(equalTo: guide.trailingAnchor),
            transportBar.topAnchor.constraint(equalTo: guide.topAnchor),
            transportBar.bottomAnchor.constraint(equalTo: guide.bottomAnchor),
        ]
        NSLayoutConstraint.activate(barConstraints)
        transportBar.axis = edge == .bottom ? .horizontal : .vertical
    }
}

@MainActor func configureBarButton(_ button: UIButton, title: String, symbol: String) {
    button.setImage(UIImage(systemName: symbol), for: .normal)
    button.accessibilityLabel = title
    button.showsLargeContentViewer = true
    button.largeContentTitle = title
    button.largeContentImage = UIImage(systemName: symbol)
}
```

SwiftUI has `safeAreaBar(edge:)` for both a `VerticalEdge` and a `HorizontalEdge`
(iOS 26). One modifier per edge keeps the content's identity when the edge changes:

```swift
struct PlayerScreen: View {
    @Environment(\.toolbarVerticalEdge) private var verticalEdge     // 27.1; nil: no vertical bar

    var body: some View {
        PlayerContent()
            .safeAreaBar(edge: .trailing) {
                if verticalEdge == .trailing { TransportBar(axis: .vertical) }
            }
            .safeAreaBar(edge: .leading) {
                if verticalEdge == .leading { TransportBar(axis: .vertical) }
            }
            .safeAreaBar(edge: .bottom) {
                if verticalEdge == nil { TransportBar(axis: .horizontal) }
            }
    }
}

struct TransportBar: View {
    let axis: Axis
    var body: some View {
        let layout = axis == .vertical ? AnyLayout(VStackLayout()) : AnyLayout(HStackLayout())
        layout {
            Button("Play", systemImage: "play.fill") {}
                .accessibilityShowsLargeContentViewer()
        }
        .labelStyle(.iconOnly)
    }
}
```

A custom bar also owes people what a system bar gives them: item labels that expand
on a long press, and the Large Content Viewer from *Accessibility Medium* text sizes up.
In UIKit add a `UILargeContentViewerInteraction` to the bar and set
`showsLargeContentViewer`, `largeContentTitle` and `largeContentImage` on each item
(`configureBarButton` above); in SwiftUI use `accessibilityShowsLargeContentViewer()`.

## Backgrounds under the bar (iOS 26; Preparing your app › Optimize bars)

```swift
// SwiftUI — the hero image extends under the vertical bar; the list stays inset
NavigationStack {
    ScrollView {
        HeroImage()
            .backgroundExtensionEffect()
        ArticleBody()
    }
}

// UIKit
let hero = UIBackgroundExtensionView()
hero.contentView = heroImageView
```

## Compression — 27.1 (12:23)

```swift
// SwiftUI — keep toolbar items, compress the tab bar (.prefersTabBar is the other choice)
TabView {
    Tab("Recents", systemImage: "clock") {
        ContentView()
            .toolbarVerticalCompressionBehavior(.prefersToolbarItems)
    }
}

// UIKit — .prefersBarItems or .prefersTabBar
navigationItem.verticalBarCompressionBehavior = .prefersBarItems
```

What each choice looks like, *Booted* on the outer display closed,
when the items do not fit:
one tab of a three-tab `TabView` holds nine symbol items
(`toolbar_edge_probe.swift`, `-mode tabs` and `-mode toolbar`; read from screenshots).

- `.prefersTabBar`: all three tabs stayed.
  Four items stayed in the bar, next to the overflow button.
- `.prefersToolbarItems`: the tab bar collapsed into one control.
  The control shows the selected tab's symbol.
  Seven items stayed in the bar, next to the overflow button.

The probe did not open the overflow menu or tap the collapsed control.

## One overflow menu (12:43)

```swift
// SwiftUI
.toolbar {
    ToolbarOverflowMenu {
        Button("Scan") { /* ... */ }
        Button("Connect") { /* ... */ }
    }
}

// UIKit
navigationItem.additionalOverflowItems = UIDeferredMenuElement({ provider in
    provider(self.persistentOverflowItems())
})
```

## A confirmation from the overflow menu (Forums 847644)

The overflow menu is not a view a dialog can anchor to. Set state from the item and
present from the screen:

```swift
struct AlbumScreen: View {
    @State private var confirmingDelete = false

    var body: some View {
        NavigationStack {
            PlayerContent()
                .toolbar {
                    ToolbarOverflowMenu {
                        Button("Delete Album", systemImage: "trash", role: .destructive) {
                            confirmingDelete = true
                        }
                    }
                }
                .confirmationDialog("Delete this album?", isPresented: $confirmingDelete) {
                    Button("Delete", role: .destructive) { deleteAlbum() }
                }
        }
    }

    private func deleteAlbum() {}
}
```

## Visibility priority (13:21)

```swift
// SwiftUI — .automatic, .low, .high, or a step relative to another value
.toolbar {
    ToolbarItem { Button(/* ... */) { /* ... */ } }
        .visibilityPriority(.high)
    ToolbarItem { Button(/* ... */) { /* ... */ } }
        .visibilityPriority(ToolbarItemVisibilityPriority(higherThan: .high))
}

// UIKit — .standard (default), .low, .high, init(higherThan:) / init(lowerThan:)
let item = UIBarButtonItem(/* ... */)
item.visibilityPriority = .high
```

## Opt out — 27.1 (14:47)

```swift
// SwiftUI
NavigationStack {
    ContentView()
        .toolbarVerticalBehavior(.disabled)
}

// UIKit
class MyViewController: UIViewController {
    override var preferredVerticalBarBehavior: UIVerticalBarBehavior { .disabled }
    // A container forwards the decision with childForPreferredVerticalBarBehavior;
    // call setNeedsUpdateOfVerticalBarConfiguration() when the answer changes.
}
```

The choice resolves per window or presentation: a `NavigationStack` uses its top
view, a `TabView` the selected tab, a `NavigationSplitView` the trailing-most column.
A different answer per horizontal size class is not a toggle, but it needs a reason as
strong as Safari's: its tabs stack horizontally and use the width the vertical bar
would take, so it disables the bar in regular width (Forums 847864).
The system animates the switch — content reflows, the status bar changes axis and the
side inset comes and goes — so treat it as a stable property of a screen, not a state.

## Deployment targets below 27.1

A modifier introduced in 27.1 cannot be applied unconditionally when the app deploys
to an earlier iOS. Wrap it once and reuse:

```swift
extension ToolbarContent {
    @ToolbarContentBuilder
    func duoHorizontalOnly() -> some ToolbarContent {
        if #available(iOS 27.1, *) {
            self.axisBehavior(.horizontalOnly)
        } else {
            self
        }
    }
}
```

Typechecked on 2026-09-19 with the real `axisBehavior` — no stand-in — at an iOS 18
deployment target against the iOS 27.1 SDK
(`xcrun --sdk iphonesimulator swiftc -typecheck -target arm64-apple-ios18.0-simulator`).
It still only compiles on an SDK that declares `axisBehavior`, so on Xcode 27.0 the
whole extension is blocked, not just its `if` branch.
