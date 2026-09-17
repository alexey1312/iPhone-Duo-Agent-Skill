# Layout — code

Samples as published on the session pages of Tech Talks 111461 and 111463, plus a few
reproduced from Apple's documentation (marked). APIs marked **27.1** were absent from
the iOS 27.0 SDK; confirm with `scripts/sdk_api_check.py`.

## Size classes (111461, 2:59)

```swift
// SwiftUI
@Environment(\.horizontalSizeClass) private var horizontalSizeClass
@Environment(\.verticalSizeClass) private var verticalSizeClass

// UIKit
traitCollection.horizontalSizeClass
traitCollection.verticalSizeClass
```

## Screen from the window scene (111461, 4:16)

```swift
let screen = window?.windowScene?.screen
```

## Screen corners (111461, 4:30)

```swift
// SwiftUI (iOS 26)
ConcentricRectangle()
    .fill(Color.green)
    .padding(8.0)
    .ignoresSafeArea()

// UIKit (iOS 26): UICornerConfiguration
```

## Sidebar on the inner display (111461, 5:44; WWDC26 278, 9:51)

```swift
// SwiftUI
TabView { /* tabs */ }
    .defaultTabBarPlacement(.sidebar)

// UIKit
tabBarController.sidebar.preferredPlacement = .sidebar
if !tabBarController.sidebar.isAvailable {
    // surface sidebar-only destinations elsewhere
}
```

## Safe areas (111461, 6:52–7:30)

```swift
// Foreground: inside the safe area
foreground.frame = view.bounds.inset(by: view.safeAreaInsets)

// Background: past it
backgroundView.frame = view.bounds          // UIKit
.ignoresSafeArea()                          // SwiftUI

// ✗ assumes opposite insets are equal
let width = view.bounds.width - view.safeAreaInsets.left * 2
// ✓ each side independently
let width = view.bounds.inset(by: view.safeAreaInsets).width
```

## Query reserved regions — 27.1 (111463, 6:46–8:07)

```swift
// SwiftUI
GeometryReader { proxy in
    let regions = proxy.reservedRegions(kind: .division)
    // ...
}

// UIKit
let regions = view.reservedRegions(kind: .division)
let frames = regions.map(\.frame)

// Include the fold even when flat (zero width) for high-level decisions
GeometryReader { proxy in
    let regions = proxy.reservedRegions(kind: .division, options: .includeInactive)
    let frames = regions.map(\.frame)
    // e.g. prefer an even number of grid columns
}

// The FaceTime camera
GeometryReader { proxy in
    let frames = proxy.reservedRegions(kind: .occlusion).map(\.frame)
    // ...
}
```

A displacement sketch: keep a floating control out of the fold.

```swift
struct FloatingControls: View {
    var body: some View {
        GeometryReader { proxy in
            let fold = proxy.reservedRegions(kind: .division).first?.frame
            ControlsCluster()
                .position(position(in: proxy.size, avoiding: fold))
        }
    }

    private func position(in size: CGSize, avoiding fold: CGRect?) -> CGPoint {
        let centered = CGPoint(x: size.width / 2, y: size.height - 60)
        guard let fold, fold.width > 0, fold.minX...fold.maxX ~= centered.x else { return centered }
        // Move to the trailing half, next to where it would sit when closed.
        return CGPoint(x: fold.maxX + (size.width - fold.maxX) / 2, y: centered.y)
    }
}
```

Treat the sketch as a pattern, not API truth: the region's coordinate space and type
come from the SDK.

From the `ReservedRegion` documentation — the full signature, and a custom `Layout`
that keeps its subviews clear of any occlusion (the camera). Frames arrive mirrored
for right-to-left languages unless you ask for `.fixed`:

```swift
func reservedRegions(kind: ReservedRegion.Kind,
                     options: ReservedRegion.QueryOptions = [],
                     layoutDirectionBehavior: LayoutDirectionBehavior = .mirrors) -> [ReservedRegion]

GeometryReader { proxy in
    RegionAvoidingLayout(regions: proxy.reservedRegions(kind: .occlusion)) {
        ForEach(items) { item in
            ItemView(item)
        }
    }
}
// Each region: id, kind (.division / .occlusion), frame (includes margins), margins, isActive
```

## ArrangementView — 27.1 (111463, 11:23–13:07)

```swift
// SwiftUI
NavigationStack {
    ArrangementView {
        PlayerView()
    } secondary: {
        UpNextView()
    }
    .arrangementViewStyle(.split)                 // default
    // .arrangementViewStyle(.split.axes(.horizontal))
}

// UIKit
let arrangementVC = UIArrangementViewController()
let navController = UINavigationController(rootViewController: arrangementVC)
arrangementVC.setViewController(PlayerViewController(), for: .primary)
arrangementVC.setViewController(UpNextViewController(), for: .secondary)
arrangementVC.updateArrangement(.split.axes(.horizontal))
```

## Overlay arrangement — 27.1 (111463, 13:26–14:21)

```swift
// SwiftUI
NavigationStack {
    ArrangementView {
        UpNextView()
    } secondary: {
        PlayerView()
    }
    .arrangementViewStyle(.overlay)
}

enum UpNextMinimization { case collapsed, expanded }

struct UpNextView: View {
    @Environment(\.overlayArrangementZIndex) private var zIndex: Int
    var body: some View {
        UpNextList(minimization: zIndex > 0 ? .collapsed : .expanded)
    }
}

// UIKit
let primaryState = arrangementVC.state(for: .primary)
myModel.minimization = (primaryState?.zIndex ?? 0) > 0 ? .collapsed : .expanded
```

## Tuning an arrangement — 27.1 (`ArrangementView` documentation)

```swift
// A 30 / 70 split; the view with the highest layoutPriority is sized first
ArrangementView {
    ConversationView()
        .splitArrangementLayoutRatio(0.3)
} secondary: {
    PhotosView()
}
.arrangementViewStyle(.split.axes(.horizontal))

// Where the overlay's primary view lands when the fold makes the layers side by side
ArrangementView {
    ControlsView()
        .overlayArrangementEdge(.trailing)
} secondary: {
    ContentView()
}
.arrangementViewStyle(.overlay)

// A child re-lays itself out for the split's axis (nil outside a split arrangement)
struct DetailsView: View {
    @Environment(\.splitArrangementAxis) var axis

    var body: some View {
        let layout: AnyLayout = axis == .horizontal
            ? AnyLayout(VStackLayout())
            : AnyLayout(HStackLayout())
        layout {
            Artwork()
            Metadata()
        }
    }
}
```
