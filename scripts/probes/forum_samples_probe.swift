import SwiftUI
import UIKit
import WebKit

// The samples layout-code.md and vertical-bars.md took from the Developer Forums answers, as written
// there, so `swiftc -typecheck` can check them against the SDK. `forum_probe.swift` runs the UIKit
// ones on the simulator. Stand-ins (`TransportBar`, `deleteAlbum`, …) are at the bottom.

// MARK: layout-code.md › Corner-aware margins — iOS 26 (Forums 848019)

@MainActor func pinToCornerMargins(_ view: UIView, _ filterButton: UIButton) {
    let guide = view.layoutGuide(for: .margins(cornerAdaptation: .horizontal))
    NSLayoutConstraint.activate([
        filterButton.leadingAnchor.constraint(equalTo: guide.leadingAnchor),
        filterButton.topAnchor.constraint(equalTo: guide.topAnchor),
    ])
    _ = view.edgeInsets(for: .margins(cornerAdaptation: .vertical))
}

#if FORUM_27_1   // everything below needs the iOS 27.1 SDK and target; the block above also compiles at iOS 26

// MARK: layout-code.md › Query during layout, not at scene transitions (Forums 848035)

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

// MARK: layout-code.md › A sheet that follows the fold (Forums 847797)

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

// MARK: layout-code.md › Split ratio in UIKit (Forums 847990)

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

// MARK: layout-code.md › A collection-view section clear of the fold (Forums 847879)

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

// MARK: layout-code.md › Web content and the fold (Forums 848036)

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

// MARK: vertical-bars.md › Custom back button (Forums 847875)

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

// MARK: vertical-bars.md › A bar that must stay custom — UIKit (Forums 847835)

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

// MARK: vertical-bars.md › A bar that must stay custom — SwiftUI (iOS 26)

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

// MARK: vertical-bars.md › A confirmation from the overflow menu (Forums 847644)

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

#endif

// MARK: stand-ins

struct PlayerContent: View { var body: some View { Color.clear } }

final class TransportBarView: UIStackView {}
