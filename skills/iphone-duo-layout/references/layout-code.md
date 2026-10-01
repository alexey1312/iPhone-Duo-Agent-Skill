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
        // The default query returns active regions only, so `fold` is nil when flat or closed.
        // Don't test `fold.width` instead: the frame includes the margins.
        guard let fold, fold.minX...fold.maxX ~= centered.x else { return centered }
        // Move to the trailing half, next to where it would sit when closed.
        return CGPoint(x: fold.maxX + (size.width - fold.maxX) / 2, y: centered.y)
    }
}
```

Treat the sketch as a pattern, not API truth: the region's coordinate space and type
come from the SDK — measured proxy-local on the simulator, see `device-geometry.md`.
`.first` holds here only because a closed or flat device reports at most one division.
The order of the array is undocumented,
and the same query for `.occlusion` on the outer display comes back with two regions —
a camera hole and the bar strip — so pick by a property that means something
rather than by position.

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

## Pose from the fold — 27.1 (111463, 4:09–4:46)

Book pose sends alerts to the trailing side; tabletop puts viewing content on top and
controls on the bottom. Which one the device is in follows from the shape of the
active division region — a vertical band is book, a horizontal one tabletop — so the
layout needs no hinge reading (111464, 2:35). Book pose is measured — a 40 × 669 pt
band, active, in landscape; tabletop's horizontal band is derived from the poses in
`device-geometry.md`, because the simulator cannot be rotated from a script.

```swift
struct NowPlaying: View {
    var body: some View {
        GeometryReader { proxy in
            // Active regions only: nil while the device is flat or closed.
            let fold = proxy.reservedRegions(kind: .division).first?.frame
            if let fold, fold.width > fold.height {
                // Tabletop: content above the fold, controls below it.
                VStack(spacing: 0) {
                    Artwork().frame(height: max(fold.minY, 0))
                    Color.clear.frame(height: fold.height)
                    TransportControls().frame(maxHeight: .infinity)
                }
            } else if let fold {
                // Book: one side each.
                HStack(spacing: 0) {
                    Artwork().frame(width: max(fold.minX, 0))
                    Color.clear.frame(width: fold.width)
                    TransportControls().frame(maxWidth: .infinity)
                }
            } else {
                VStack {
                    Artwork()
                    TransportControls()
                }
            }
        }
    }
}
```

Checked on the simulator in book pose: the fold falls in the gap between the halves.
Use this for discrete, manually placed controls. An arrangement does the same split
for two views without any of this code, and continuously scrolling content does not
displace at all (3:45).

## Even columns — 27.1 (111463, 7:36)

The fold exists whether or not it is active, so a grid can prefer an even number of
columns whenever a vertical division is present — the talk's high-level decision.
On its own that does not keep tiles off the fold (below):

```swift
struct PhotoGrid: View {
    let photos: [Photo]

    var body: some View {
        GeometryReader { proxy in
            let hasVerticalFold = proxy.reservedRegions(kind: .division, options: .includeInactive)
                .contains { $0.frame.height > $0.frame.width }
            let count = columnCount(width: proxy.size.width, minimum: 140, preferEven: hasVerticalFold)
            ScrollView {
                LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: count)) {
                    ForEach(photos) { PhotoTile(photo: $0) }
                }
                .padding()
            }
        }
    }

    private func columnCount(width: CGFloat, minimum: CGFloat, preferEven: Bool) -> Int {
        let fitting = max(Int(width / minimum), 1)
        return preferEven && fitting > 1 && !fitting.isMultiple(of: 2) ? fitting - 1 : fitting
    }
}
```

Run on the simulator, this grid lays out six columns flat, and the fold runs
through the middle of the fourth. An even count alone does not put the gutter on the
fold. In landscape the fold is
the middle of the display, not of the safe area: measured on the simulator, the
84 pt trailing inset puts the fold's frame at x 455.5–495.5 of an 867 pt reader,
so the middle gutter of a symmetric grid (x 433.5) misses it by 42 pt
(`device-geometry.md` › Inner display, measured).
When it must line up, lay out the halves either side of the fold's frame,
the way the talk's Fitness grid keeps its outer margins and widens the spacing at
the hinge (111463, 5:50):

```swift
struct FoldAlignedGrid: View {
    let photos: [Photo]

    var body: some View {
        GeometryReader { proxy in
            let fold = proxy.reservedRegions(kind: .division, options: .includeInactive)
                .first { $0.frame.height > $0.frame.width }?.frame
            ScrollView {
                if let fold {
                    let leading = max(fold.minX, 0)
                    let trailing = max(proxy.size.width - fold.maxX, 0)
                    let perSide = max(Int(min(leading, trailing) / 140), 1)
                    HStack(alignment: .top, spacing: 0) {
                        half(Array(photos.enumerated()), keep: { $0 % (perSide * 2) < perSide }, columns: perSide)
                            .frame(width: leading)
                        Color.clear.frame(width: fold.width)        // the fold's frame, margins included
                        half(Array(photos.enumerated()), keep: { $0 % (perSide * 2) >= perSide }, columns: perSide)
                            .frame(width: trailing)
                    }
                } else {
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 140))]) {
                        ForEach(photos) { PhotoTile(photo: $0) }
                    }
                }
            }
        }
    }

    private func half(_ items: [(offset: Int, element: Photo)], keep: (Int) -> Bool, columns: Int) -> some View {
        LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: columns)) {
            ForEach(items.filter { keep($0.offset) }, id: \.element.id) { PhotoTile(photo: $0.element) }
        }
        .padding(.horizontal, 8)
    }
}
```

Checked on the simulator, flat and in book pose: the fold falls in the gap between
the halves. The halves are unequal in landscape (455.5 against 371.5 pt). Both get the column
count the narrower one fits, so tiles on the leading side come out wider; each row
stays even, and no tile crosses the fold, flat or folded.

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

**Copied as it is, the SwiftUI half never collapses.** `UpNextView` is the view
written directly in the closure, and that view reads the environment's default, 0;
only views nested inside it see the arrangement's value (measured on Xcode 27.1
(27A9269); `scripts/probes/arrangement_probe.swift` in the repository). Read it one
view down:

```swift
struct UpNextView: View {
    var body: some View {
        UpNextContent()                    // the closure's root: reads 0 whatever happens
    }
}

struct UpNextContent: View {
    @Environment(\.overlayArrangementZIndex) private var zIndex: Int
    var body: some View {
        UpNextList(minimization: zIndex > 0 ? .collapsed : .expanded)
    }
}

// Or leave UpNextView as it was and wrap it where it is placed:
// ArrangementView { VStack { UpNextView() } } secondary: { PlayerView() }
```

A modifier on the root does not help — `UpNextView().padding(0)` still reads 0. The
same holds for `splitArrangementAxis`, which reads `nil` at the root.

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

// A range per axis instead of one ratio; a fixed-size variant also exists
ConversationView()
    .splitArrangementLayoutRatio(minHorizontal: 0.25, idealHorizontal: 0.3, maxHorizontal: 0.4)
ConversationView()
    .splitArrangementFixedLayoutSize(horizontal: true, vertical: false)

// Where the overlay's primary view lands when the fold makes the layers side by side;
// .overlay.axes(_:) limits the axes it may go side by side along
ArrangementView {
    ControlsView()
        .overlayArrangementEdge(.trailing)
} secondary: {
    ContentView()
}
.arrangementViewStyle(.overlay.axes(.horizontal))

// A child re-lays itself out for the split's axis (nil outside a split arrangement).
// It must sit one view below the closure's root: placed directly as `primary` or
// `secondary`, DetailsView reads nil and always takes the HStack branch.
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
