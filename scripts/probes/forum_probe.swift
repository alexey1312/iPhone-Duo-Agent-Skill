import UIKit
import WebKit

// Checks, on a booted iPhone Duo simulator, the UIKit answers Apple engineers gave on the
// Developer Forums (references/sources.md › Developer Forums Q&A). One mode per launch:
//
//   -mode layout   a view that reads reserved regions in layoutSubviews next to a control view that
//                  does not, plus the corner-adapted and bar layout regions as insets
//   -mode sheet    a page sheet presented over a host; add -fold-placement YES to set the sheet's
//                  placement from the active division region
//   -mode grid     a compositional layout whose first section keeps its gap on the fold
//   -mode web      a WKWebView: CSS safe-area insets, the experimental web APIs, and the fold passed in
//
// NSLog, so the lines survive a plain `simctl launch` and can be read with `log show`.

func log(_ message: String) { NSLog("FORUMPROBE %@", message) }
func fmt(_ r: CGRect) -> String { String(format: "(%.1f, %.1f, %.1f, %.1f)", r.minX, r.minY, r.width, r.height) }
func fmt(_ i: UIEdgeInsets) -> String { String(format: "(t:%.1f l:%.1f b:%.1f r:%.1f)", i.top, i.left, i.bottom, i.right) }
let mode = UserDefaults.standard.string(forKey: "mode") ?? "layout"

@MainActor func activeFold(_ view: UIView) -> CGRect? {
    view.reservedRegions(kind: .division).first(where: \.isActive)?.frame
}

@main
final class AppDelegate: UIResponder, UIApplicationDelegate {
    func application(_ application: UIApplication, configurationForConnecting session: UISceneSession,
                     options: UIScene.ConnectionOptions) -> UISceneConfiguration {
        let configuration = UISceneConfiguration(name: nil, sessionRole: session.role)
        configuration.delegateClass = SceneDelegate.self
        return configuration
    }
}

final class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?

    func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options: UIScene.ConnectionOptions) {
        guard let windowScene = scene as? UIWindowScene else { return }
        let window = UIWindow(windowScene: windowScene)
        switch mode {
        case "sheet": window.rootViewController = SheetHostController()
        case "grid": window.rootViewController = GridController()
        case "web": window.rootViewController = WebController()
        default: window.rootViewController = LayoutController()
        }
        window.makeKeyAndVisible()
        self.window = window
        log("mode=\(mode)")
    }

    func windowScene(_ windowScene: UIWindowScene, didUpdateEffectiveGeometry previous: UIWindowScene.Geometry) {
        log("SCENE didUpdateEffectiveGeometry size=\(windowScene.effectiveGeometry.coordinateSpace.bounds.size)")
    }
}

// MARK: - layout

final class RegionReadingView: UIView {
    private var passes = 0
    override func layoutSubviews() {
        super.layoutSubviews()
        passes += 1
        let fold = activeFold(self)
        log("LAYOUT reader pass=\(passes) bounds=\(bounds.size) safe=\(fmt(safeAreaInsets)) fold=\(fold.map(fmt) ?? "nil")")
        log("REGIONS margins=\(fmt(edgeInsets(for: .margins()))) "
            + "marginsH=\(fmt(edgeInsets(for: .margins(cornerAdaptation: .horizontal)))) "
            + "marginsV=\(fmt(edgeInsets(for: .margins(cornerAdaptation: .vertical)))) "
            + "safeH=\(fmt(edgeInsets(for: .safeArea(cornerAdaptation: .horizontal)))) "
            + "safeV=\(fmt(edgeInsets(for: .safeArea(cornerAdaptation: .vertical)))) "
            + "barTrailing56=\(fmt(edgeInsets(for: .bar(onEdge: NSDirectionalRectEdge.trailing, extent: 56)))) "
            + "barBottom56=\(fmt(edgeInsets(for: .bar(onEdge: NSDirectionalRectEdge.bottom, extent: 56)))) "
            + "verticalBarEdge=\(traitCollection.verticalBarEdge.rawValue)")
    }
}

final class ControlView: UIView {
    private var passes = 0
    override func layoutSubviews() {
        super.layoutSubviews()
        passes += 1
        log("LAYOUT control pass=\(passes) bounds=\(bounds.size)")
    }
}

final class LayoutController: UIViewController {
    private let reader = RegionReadingView()
    private let control = ControlView()

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        for child in [reader, control] {
            child.frame = view.bounds
            child.autoresizingMask = [.flexibleWidth, .flexibleHeight]
            view.addSubview(child)
        }
        view.addInteraction(UIHingeInteraction { _, update in
            guard let hinge = update.hinge else { return log("HINGE nil") }
            log("HINGE status=\(hinge.status.rawValue) angle=\(hinge.angle)")
        })
    }
}

// MARK: - sheet

final class SheetHostController: UIViewController {
    private let placeFromFold = UserDefaults.standard.bool(forKey: "fold-placement")

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemTeal
    }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        guard presentedViewController == nil else { return }
        let content = SheetContentController()
        content.modalPresentationStyle = .pageSheet
        if let sheet = content.sheetPresentationController {
            sheet.detents = [.medium(), .large()]
            if placeFromFold { sheet.preferredPlacement = placement() }
        }
        present(content, animated: false)
    }

    override func viewWillLayoutSubviews() {
        super.viewWillLayoutSubviews()
        log("HOST layout fold=\(activeFold(view).map(fmt) ?? "nil")")
        guard placeFromFold, let sheet = presentedViewController?.sheetPresentationController else { return }
        let wanted = placement()
        if sheet.preferredPlacement != wanted {
            sheet.animateChanges { sheet.preferredPlacement = wanted }
        }
    }

    private func placement() -> UISheetPresentationController.Placement {
        activeFold(view) == nil ? .automatic : .trailing
    }
}

final class SheetContentController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemOrange
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        let placement = sheetPresentationController?.preferredPlacement.rawValue ?? -1
        log("SHEET frameInWindow=\(fmt(view.convert(view.bounds, to: nil))) placement=\(placement) "
            + "presented=\(presentingViewController != nil)")
    }
}

// MARK: - grid

final class GridController: UICollectionViewController {
    private var lastFold: CGRect?

    init() {
        super.init(collectionViewLayout: UICollectionViewFlowLayout())
    }

    required init?(coder: NSCoder) { fatalError() }

    override func viewDidLoad() {
        super.viewDidLoad()
        collectionView.register(UICollectionViewCell.self, forCellWithReuseIdentifier: "cell")
        collectionView.collectionViewLayout = makeLayout()
    }

    override func numberOfSections(in collectionView: UICollectionView) -> Int { 2 }

    override func collectionView(_ collectionView: UICollectionView, numberOfItemsInSection section: Int) -> Int {
        section == 0 ? 2 : 60
    }

    override func collectionView(_ collectionView: UICollectionView,
                                 cellForItemAt indexPath: IndexPath) -> UICollectionViewCell {
        let cell = collectionView.dequeueReusableCell(withReuseIdentifier: "cell", for: indexPath)
        cell.backgroundColor = indexPath.section == 0 ? .systemOrange : .systemBlue.withAlphaComponent(0.4)
        return cell
    }

    override func viewWillLayoutSubviews() {
        super.viewWillLayoutSubviews()
        let fold = verticalFold()
        if fold != lastFold {
            lastFold = fold
            collectionView.collectionViewLayout.invalidateLayout()
        }
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        let cards = (0..<2).compactMap { collectionView.layoutAttributesForItem(at: IndexPath(item: $0, section: 0))?.frame }
        log("GRID fold=\(verticalFold().map(fmt) ?? "nil") cards=\(cards.map(fmt)) "
            + "safe=\(fmt(collectionView.safeAreaInsets)) adjusted=\(fmt(collectionView.adjustedContentInset)) "
            + "boundsOrigin=\(collectionView.bounds.origin)")
    }

    private func verticalFold() -> CGRect? {
        guard let fold = activeFold(collectionView), fold.height > fold.width else { return nil }
        return fold
    }

    private func makeLayout() -> UICollectionViewCompositionalLayout {
        UICollectionViewCompositionalLayout { [unowned self] section, environment in
            section == 0 ? summarySection(environment) : feedSection()
        }
    }

    // Two cards side by side that never scroll sideways: in book pose, put the gap between them on the fold.
    private func summarySection(_ environment: NSCollectionLayoutEnvironment) -> NSCollectionLayoutSection {
        let height = NSCollectionLayoutDimension.absolute(120)
        let insets = environment.container.effectiveContentInsets
        let width = environment.container.effectiveContentSize.width
        log("GRID environment insets=(l:\(insets.leading) r:\(insets.trailing)) width=\(width)")
        let group: NSCollectionLayoutGroup
        if let fold = verticalFold(), fold.minX - insets.leading > 0, insets.leading + width - fold.maxX > 0 {
            let first = NSCollectionLayoutItem(layoutSize: .init(widthDimension: .absolute(fold.minX - insets.leading),
                                                                 heightDimension: height))
            let second = NSCollectionLayoutItem(layoutSize: .init(widthDimension: .absolute(insets.leading + width - fold.maxX),
                                                                  heightDimension: height))
            group = .horizontal(layoutSize: .init(widthDimension: .fractionalWidth(1), heightDimension: height),
                                subitems: [first, second])
            group.interItemSpacing = .fixed(fold.width)
        } else {
            let item = NSCollectionLayoutItem(layoutSize: .init(widthDimension: .fractionalWidth(0.5), heightDimension: height))
            group = .horizontal(layoutSize: .init(widthDimension: .fractionalWidth(1), heightDimension: height),
                                repeatingSubitem: item, count: 2)
            group.interItemSpacing = .fixed(16)
        }
        let section = NSCollectionLayoutSection(group: group)
        section.contentInsets.bottom = 16
        return section
    }

    // Scrolling content: no fold avoidance.
    private func feedSection() -> NSCollectionLayoutSection {
        let item = NSCollectionLayoutItem(layoutSize: .init(widthDimension: .fractionalWidth(1.0 / 6),
                                                            heightDimension: .fractionalWidth(1.0 / 6)))
        item.contentInsets = .init(top: 2, leading: 2, bottom: 2, trailing: 2)
        let group = NSCollectionLayoutGroup.horizontal(
            layoutSize: .init(widthDimension: .fractionalWidth(1), heightDimension: .fractionalWidth(1.0 / 6)),
            repeatingSubitem: item, count: 6)
        return NSCollectionLayoutSection(group: group)
    }
}

// MARK: - web

final class WebController: UIViewController, WKNavigationDelegate {
    private let webView = WKWebView()
    private var loaded = false
    private var lastFold: CGRect??

    override func viewDidLoad() {
        super.viewDidLoad()
        webView.frame = view.bounds
        webView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        webView.navigationDelegate = self
        view.addSubview(webView)
        webView.loadHTMLString(Self.page, baseURL: nil)
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        loaded = true
        lastFold = nil
        view.setNeedsLayout()
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        guard loaded else { return }
        let fold = activeFold(webView)
        log("WEBHOST fold=\(fold.map(fmt) ?? "nil") safe=\(fmt(webView.safeAreaInsets)) "
            + "adjusted=\(fmt(webView.scrollView.adjustedContentInset))")
        guard lastFold != .some(fold) else { return }
        lastFold = .some(fold)
        let script = fold.map {
            "setFold(\($0.minX), \($0.minY), \($0.width), \($0.height))"
        } ?? "setFold(null)"
        webView.evaluateJavaScript(script + "; report()") { result, error in
            log("WEB \(result as? String ?? "nil") error=\(error.map { "\($0)" } ?? "nil")")
        }
    }

    static let page = """
    <!doctype html><html><head>
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <style>
      body { margin: 0; font: 17px -apple-system;
             padding-left: env(safe-area-inset-left); padding-right: env(safe-area-inset-right); }
      #cta { position: fixed; bottom: 40px; width: 120px; height: 44px; background: orange;
             left: calc(50% - 60px); }
      body.folded #cta { left: calc(var(--fold-max-x) + (100% - var(--fold-max-x)) / 2 - 60px); }
    </style>
    <script>
      function setFold(x, y, w, h) {
        const root = document.documentElement.style;
        if (x === null) { document.body.classList.remove('folded'); return; }
        root.setProperty('--fold-min-x', x + 'px');
        root.setProperty('--fold-max-x', (x + w) + 'px');
        root.setProperty('--fold-min-y', y + 'px');
        root.setProperty('--fold-max-y', (y + h) + 'px');
        document.body.classList.add('folded');
      }
      function report() {
        const style = getComputedStyle(document.body);
        return JSON.stringify({
          paddingLeft: style.paddingLeft, paddingRight: style.paddingRight,
          innerWidth: innerWidth, innerHeight: innerHeight,
          viewportSegments: !!(window.viewport && window.viewport.segments),
          devicePosture: 'devicePosture' in navigator,
          envSegment: CSS.supports('width', 'env(viewport-segment-width 0 0)'),
          cta: document.getElementById('cta').getBoundingClientRect().toJSON()
        });
      }
    </script></head>
    <body><div id="cta"></div><p>Probe</p></body></html>
    """
}
