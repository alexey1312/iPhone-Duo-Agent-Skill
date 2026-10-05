# Layout — code

Samples as published on the session pages of Tech Talks 111461 and 111463, plus a few
reproduced from Apple's documentation (marked). APIs marked **27.1** were absent from
the iOS 27.0 SDK; confirm with `scripts/sdk_api_check.py`.
Samples marked *Forums* put an Apple engineer's forum answer into code
(`sources.md` › Developer Forums Q&A).
They are this repository's code, not Apple's, and they typecheck against the
iOS 27.1 SDK (`scripts/probes/forum_samples_probe.swift` in the repository).
*Booted* marks behavior measured on the iPhone Duo simulator
(`scripts/probes/forum_probe.swift`).

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

## Corner-aware margins — iOS 26 (Forums 848019)

`UIView.LayoutRegion` gives margins that move in from the rounded screen corners.
The axis names the direction of the move.
*Booted*, inner display in landscape: `.horizontal` added 16 pt on the leading edge,
`.vertical` 16 pt on the top, and an edge the safe area already insets did not change.
No gate is needed above iOS 26.

```swift
@MainActor func pinToCornerMargins(_ view: UIView, _ filterButton: UIButton) {
    let guide = view.layoutGuide(for: .margins(cornerAdaptation: .horizontal))
    NSLayoutConstraint.activate([
        filterButton.leadingAnchor.constraint(equalTo: guide.leadingAnchor),
        filterButton.topAnchor.constraint(equalTo: guide.topAnchor),
    ])
    _ = view.edgeInsets(for: .margins(cornerAdaptation: .vertical))
}
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

## Query during layout, not at scene transitions — 27.1 (Forums 848035)

Read the regions where the view lays itself out.
Do not save a fold state when the scene goes to the background,
and do not restore one when it comes back: the regions are current by then.
*Booted*: a view that read the regions in `layoutSubviews` got a layout pass when the
device folded and another when it opened, with bounds and safe area unchanged.
A sibling view that did not read them got no pass.
That is UIKit's observation tracking.
It was measured in `layoutSubviews` and in `viewWillLayoutSubviews`;
Apple's *Updating views automatically with observation tracking in UIKit* also lists
`updateProperties()`.
Folding does not call `windowScene(_:didUpdateEffectiveGeometry:)`.

```swift
final class RecordControlsView: UIView {
    let recordButton = UIButton(configuration: .filled())

    override init(frame: CGRect) {
        super.init(frame: frame)
        addSubview(recordButton)
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) is not supported") }

    override func layoutSubviews() {
        super.layoutSubviews()
        let size = recordButton.intrinsicContentSize
        var center = CGPoint(x: bounds.midX, y: bounds.maxY - safeAreaInsets.bottom - size.height)
        if let fold = reservedRegions(kind: .division).first(where: \.isActive)?.frame,
           fold.height > fold.width, fold.minX...fold.maxX ~= center.x {
            center.x = fold.maxX + (bounds.maxX - safeAreaInsets.right - fold.maxX) / 2
        }
        recordButton.bounds.size = size
        recordButton.center = center
    }
}
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

## A sheet that follows the fold — 27.1 (Forums 847797)

A presented sheet stays presented through a fold (Forums 848034).
Folded, it moves to the leading side by default.
*Booted*: x 8–467 pt in book pose, centred at x 149–802 pt when flat.
`preferredPlacement` applies in every pose, and no per-pose API exists.
When the design needs another side while folded, set the placement from the active
division region, and update it from `viewWillLayoutSubviews`, which runs again on a fold.
*Booted*: the sheet moved to x 483.5–943 pt in book pose and back to the centre when flat.
Placing a sheet at an edge changes its toolbar: `iphone-duo-bars` owns that.

```swift
final class MapViewController: UIViewController {
    func showDetails(_ details: UIViewController) {
        details.modalPresentationStyle = .pageSheet
        details.sheetPresentationController?.detents = [.medium(), .large()]
        details.sheetPresentationController?.preferredPlacement = placementForFold()
        present(details, animated: true)
    }

    override func viewWillLayoutSubviews() {
        super.viewWillLayoutSubviews()
        guard let sheet = presentedViewController?.sheetPresentationController else { return }
        let placement = placementForFold()
        if sheet.preferredPlacement != placement {
            sheet.animateChanges { sheet.preferredPlacement = placement }
        }
    }

    private func placementForFold() -> UISheetPresentationController.Placement {
        view.reservedRegions(kind: .division).contains(where: \.isActive) ? .trailing : .automatic
    }
}
```

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

## A collection-view section clear of the fold — 27.1 (Forums 847879)

`UICollectionView` and compositional layouts do not avoid the fold,
and the division region adds no safe-area insets and no traits.
*Booted*: in book pose the collection view's `safeAreaInsets`, `adjustedContentInset`
and the layout environment's insets did not change.
Scrolling content need not avoid the fold.
Adjust only a section that does not scroll across the fold's axis,
such as a row of summary cards, from the collection view's own reserved regions,
and invalidate the layout when the fold changes.
*Booted*: the gap between the two cards fell on the fold's frame, x 455.7–495.7 pt,
while the 6-column grid below kept scrolling across it.
To hide a section in some size classes, change the data source or the layout.
A section sized to 0.1 pt still makes items, only tiny ones (Forums 848018).

```swift
final class DashboardViewController: UICollectionViewController {
    private var lastFold: CGRect?

    override func viewWillLayoutSubviews() {
        super.viewWillLayoutSubviews()
        let fold = verticalFold()
        if fold != lastFold {
            lastFold = fold
            collectionView.collectionViewLayout.invalidateLayout()
        }
    }

    private func verticalFold() -> CGRect? {
        guard let fold = collectionView.reservedRegions(kind: .division).first(where: \.isActive)?.frame,
              fold.height > fold.width else { return nil }
        return fold
    }

    func makeLayout() -> UICollectionViewCompositionalLayout {
        UICollectionViewCompositionalLayout { [unowned self] index, environment in
            index == 0 ? summarySection(environment) : feedSection()
        }
    }

    private func summarySection(_ environment: NSCollectionLayoutEnvironment) -> NSCollectionLayoutSection {
        let height = NSCollectionLayoutDimension.absolute(120)
        let full = NSCollectionLayoutSize(widthDimension: .fractionalWidth(1), heightDimension: height)
        let leading = environment.container.effectiveContentInsets.leading
        let width = environment.container.effectiveContentSize.width
        let group: NSCollectionLayoutGroup
        if let fold = verticalFold(), fold.minX > leading, fold.maxX < leading + width {
            let first = NSCollectionLayoutItem(layoutSize: .init(widthDimension: .absolute(fold.minX - leading),
                                                                 heightDimension: height))
            let second = NSCollectionLayoutItem(layoutSize: .init(widthDimension: .absolute(leading + width - fold.maxX),
                                                                  heightDimension: height))
            group = .horizontal(layoutSize: full, subitems: [first, second])
            group.interItemSpacing = .fixed(fold.width)
        } else {
            let card = NSCollectionLayoutItem(layoutSize: .init(widthDimension: .fractionalWidth(0.5), heightDimension: height))
            group = .horizontal(layoutSize: full, repeatingSubitem: card, count: 2)
            group.interItemSpacing = .fixed(16)
        }
        return NSCollectionLayoutSection(group: group)
    }

    private func feedSection() -> NSCollectionLayoutSection {
        let tile = NSCollectionLayoutItem(layoutSize: .init(widthDimension: .fractionalWidth(1.0 / 6),
                                                            heightDimension: .fractionalWidth(1.0 / 6)))
        let row = NSCollectionLayoutGroup.horizontal(
            layoutSize: .init(widthDimension: .fractionalWidth(1), heightDimension: .fractionalWidth(1.0 / 6)),
            repeatingSubitem: tile, count: 6)
        return NSCollectionLayoutSection(group: row)
    }
}
```

The frames are in the collection view's own coordinates,
which are content coordinates because a scroll view's bounds origin is its offset.
With vertical scrolling, x matches the layout's x (bounds origin x was 0);
y moves with the scroll position.

## Web content and the fold — 27.1 (Forums 848036)

The fold does not reach web content.
CSS `env(safe-area-inset-*)` and the web view's adjusted content insets exclude it.
The Viewport Segments and Device Posture APIs are experimental Safari feature flags
and cannot be enabled in `WKWebView` (Forums 848036, 847644).
*Booted*: `window.viewport.segments`, `navigator.devicePosture` and
`env(viewport-segment-width 0 0)` were all unavailable,
and the safe-area padding stayed the same in book pose.
For a page the app controls, query the regions in the host and pass them in as CSS
custom properties, separate from the safe-area insets, so neither side applies the
same spacing twice.
A page the app does not control keeps scrolling across the fold.
Keep native controls that float over it clear of the fold.

```swift
final class ArticleWebViewController: UIViewController, WKNavigationDelegate {
    private let webView = WKWebView()
    private var sentFold: CGRect??          // .none: nothing sent to this page yet

    override func viewDidLoad() {
        super.viewDidLoad()
        webView.navigationDelegate = self
        webView.frame = view.bounds
        webView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        view.addSubview(webView)
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        sentFold = .none                    // a new page knows nothing yet
        view.setNeedsLayout()
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        let fold = webView.reservedRegions(kind: .division).first(where: \.isActive)?.frame
        guard sentFold != .some(fold) else { return }
        sentFold = .some(fold)
        let inset = webView.scrollView.adjustedContentInset
        let script = fold.map { f in
            let x = f.minX - inset.left, y = f.minY - inset.top
            return """
            document.documentElement.style.setProperty('--fold-min-x', '\(x)px');
            document.documentElement.style.setProperty('--fold-max-x', '\(x + f.width)px');
            document.documentElement.style.setProperty('--fold-min-y', '\(y)px');
            document.documentElement.style.setProperty('--fold-max-y', '\(y + f.height)px');
            document.documentElement.classList.add('fold-active');
            """
        } ?? "document.documentElement.classList.remove('fold-active');"
        webView.evaluateJavaScript(script)
    }
}
```

```css
/* In the page: a fixed button moves to the middle of the trailing half while folded */
.listen { position: fixed; bottom: 40px; width: 120px; left: calc(50% - 60px); }
.fold-active .listen {
    left: calc(var(--fold-max-x) + (100% - env(safe-area-inset-right) - var(--fold-max-x)) / 2 - 60px);
}
```

*Booted*: with the page at scale 1 and no leading content inset,
the fold's frame in the web view matched CSS pixels 1 : 1
(the button centred on x 723.25 = 495.5 + (951 − 495.5) / 2, measured without the
safe-area term).
Subtracting the adjusted content inset is derived, not measured.

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

UIKit, the same 30 / 70 split (Forums 847990).
`UISplitArrangement` is a struct and `setViewProperties(_:for:)` is `mutating`,
so copy the defaults, change them, and write them back:

```swift
@MainActor func makeEditor(outline: UIViewController, editor: UIViewController) -> UIArrangementViewController {
    let controller = UIArrangementViewController()
    controller.setViewController(outline, for: .primary)
    controller.setViewController(editor, for: .secondary)
    var arrangement: UISplitArrangement = .split.axes(.horizontal)
    var properties = arrangement.defaultViewProperties
    properties.width.preferred = .fractional(0.3)
    arrangement.setViewProperties(properties, for: .primary)
    controller.updateArrangement(arrangement)
    return controller
}
```
