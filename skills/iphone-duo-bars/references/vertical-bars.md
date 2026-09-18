# Vertical bars — code

Samples from Tech Talk 111462 as published on the session page, plus a few from
Apple's documentation (marked). APIs marked **27.1** were absent from the iOS 27.0
SDK; confirm with `scripts/sdk_api_check.py`.

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
