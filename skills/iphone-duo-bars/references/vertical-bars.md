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
