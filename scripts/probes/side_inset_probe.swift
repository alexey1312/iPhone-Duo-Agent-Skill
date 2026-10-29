import SwiftUI
import UIKit

// Checks, on a booted iPhone Duo simulator, what happens to the vertical bar's side inset —
// and to content under it — in the cases a third-party report describes
// (Samorek, 2026-10-19, references/sources.md › Background reading). One mode per launch:
//
//   -mode nav           a navigation controller with a title and two bar button items
//   -mode disabled      the same with preferredVerticalBarBehavior .disabled
//   -mode statusHidden  the same with prefersStatusBarHidden true
//   -mode card          `nav` presents a 320 × 420 card through a custom UIPresentationController
//   -mode cardDisabled  the same, with the card's view controller opting out of the vertical bar
//   -mode cardNav       the card holds a navigation controller with a title and two bar button items
//   -mode cardNavDisabled  the same, with the card's view controller opting out
//   -mode nested        a horizontal scroll view pinned to the view's edges holds a second one
//   -mode edgeSoft      a SwiftUI carousel that scrolls under the trailing inset, with
//                       .scrollEdgeEffectStyle(.soft, for: .trailing)
//   -mode edgeHard      the same with .hard
//   -mode edgeHidden    the same with .scrollEdgeEffectHidden(for: .trailing): the control
//   -mode edgeBarSoft   edgeSoft inside a NavigationStack whose toolbar item sits in the vertical bar
//   -mode edgeBarHidden its control
//   -mode topSoft       the positive control: cards scrolling vertically under the top
//                       navigation bar, with .scrollEdgeEffectStyle(.soft, for: .top)
//   -mode topHidden     its control
//   -mode edgeUIKit     a UIScrollView carousel with rightEdgeEffect.style = .soft
//   -mode edgeUIKitHidden  the same with rightEdgeEffect.isHidden: the UIKit control
//
// Compare the trailing 84 pt of an edge screenshot with its control: identical
// pixels mean no effect was drawn there.
// NSLog, so the lines survive a plain `simctl launch` and can be read with `log show`.

func log(_ message: String) { NSLog("SIDEPROBE %@", message) }
func fmt(_ r: CGRect) -> String { String(format: "(%.1f, %.1f, %.1f, %.1f)", r.minX, r.minY, r.width, r.height) }
func fmt(_ i: UIEdgeInsets) -> String { String(format: "(t:%.1f l:%.1f b:%.1f r:%.1f)", i.top, i.left, i.bottom, i.right) }
let mode = UserDefaults.standard.string(forKey: "mode") ?? "nav"

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
        case "nested": window.rootViewController = NestedController()
        case "edgeSoft": window.rootViewController = UIHostingController(rootView: Carousel(style: .soft))
        case "edgeHard": window.rootViewController = UIHostingController(rootView: Carousel(style: .hard))
        case "edgeHidden": window.rootViewController = UIHostingController(rootView: Carousel(style: nil))
        case "edgeBarSoft": window.rootViewController = UIHostingController(rootView: Carousel(style: .soft, inBar: true))
        case "edgeBarHidden": window.rootViewController = UIHostingController(rootView: Carousel(style: nil, inBar: true))
        case "topSoft":
            window.rootViewController = UIHostingController(
                rootView: Carousel(style: .soft, axis: .vertical, edge: .top, inBar: true))
        case "topHidden":
            window.rootViewController = UIHostingController(
                rootView: Carousel(style: nil, axis: .vertical, edge: .top, inBar: true))
        case "edgeUIKit", "edgeUIKitHidden": window.rootViewController = UIKitCarouselController()
        default: window.rootViewController = UINavigationController(rootViewController: ScreenController())
        }
        window.makeKeyAndVisible()
        self.window = window
        log("mode=\(mode)")
    }
}

// MARK: - nav, disabled, statusHidden, card…

final class ScreenController: UIViewController {
    override var preferredVerticalBarBehavior: UIVerticalBarBehavior { mode == "disabled" ? .disabled : .automatic }
    override var prefersStatusBarHidden: Bool { mode == "statusHidden" }

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        title = "Probe"
        navigationItem.rightBarButtonItems = [
            UIBarButtonItem(systemItem: .close),
            UIBarButtonItem(systemItem: .action),
        ]
    }

    override func viewSafeAreaInsetsDidChange() {
        super.viewSafeAreaInsetsDidChange()
        log("SCREEN safe=\(fmt(view.safeAreaInsets)) bounds=\(fmt(view.bounds)) "
            + "verticalBarEdge=\(traitCollection.verticalBarEdge.rawValue)")
    }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        guard mode.hasPrefix("card"), presentedViewController == nil else { return }
        let card = CardController()
        let presented: UIViewController = mode.hasPrefix("cardNav")
            ? UINavigationController(rootViewController: card) : card
        presented.modalPresentationStyle = .custom
        presented.transitioningDelegate = card
        present(presented, animated: false)
    }
}

final class CardController: UIViewController, UIViewControllerTransitioningDelegate {
    override var preferredVerticalBarBehavior: UIVerticalBarBehavior {
        mode.hasSuffix("Disabled") ? .disabled : .automatic
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemOrange
        title = "Card"
        navigationItem.rightBarButtonItems = [UIBarButtonItem(systemItem: .close)]
        let label = UILabel()
        label.text = "Card"
        label.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(label)
        NSLayoutConstraint.activate([
            label.centerXAnchor.constraint(equalTo: view.safeAreaLayoutGuide.centerXAnchor),
            label.centerYAnchor.constraint(equalTo: view.safeAreaLayoutGuide.centerYAnchor),
        ])
    }

    // Not viewSafeAreaInsetsDidChange: a card with no inset never gets that call.
    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        log("CARD safe=\(fmt(view.safeAreaInsets)) frameInWindow=\(fmt(view.convert(view.bounds, to: nil))) "
            + "verticalBarEdge=\(traitCollection.verticalBarEdge.rawValue)")
    }

    func presentationController(forPresented presented: UIViewController, presenting: UIViewController?,
                                source: UIViewController) -> UIPresentationController? {
        CardPresentationController(presentedViewController: presented, presenting: presenting)
    }
}

final class CardPresentationController: UIPresentationController {
    override var frameOfPresentedViewInContainerView: CGRect {
        let bounds = containerView?.bounds ?? .zero
        let size = CGSize(width: 320, height: 420)
        return CGRect(x: (bounds.width - size.width) / 2, y: (bounds.height - size.height) / 2,
                      width: size.width, height: size.height)
    }

    override func containerViewDidLayoutSubviews() {
        super.containerViewDidLayoutSubviews()
        presentedView?.frame = frameOfPresentedViewInContainerView
        if let containerView { log("CONTAINER safe=\(fmt(containerView.safeAreaInsets))") }
    }
}

// MARK: - nested

final class NestedController: UIViewController {
    private let outer = UIScrollView()
    private let inner = UIScrollView()

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        outer.frame = view.bounds
        outer.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        view.addSubview(outer)
        inner.backgroundColor = .systemTeal
        outer.addSubview(inner)
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        outer.contentSize = CGSize(width: view.bounds.width * 3, height: view.bounds.height)
        inner.frame = CGRect(x: 0, y: 100, width: view.bounds.width, height: 200)
        inner.contentSize = CGSize(width: view.bounds.width * 3, height: 200)
        log("NESTED view=\(fmt(view.safeAreaInsets)) outer.safe=\(fmt(outer.safeAreaInsets)) "
            + "outer.adjusted=\(fmt(outer.adjustedContentInset)) inner.safe=\(fmt(inner.safeAreaInsets)) "
            + "inner.adjusted=\(fmt(inner.adjustedContentInset))")
    }
}

// MARK: - edge effects

let cardColors: [Color] = [.red, .orange, .yellow, .green, .blue, .purple]

/// Cards that scroll along `axis` under `edge`. With `inBar`, a NavigationStack puts a
/// toolbar item in the bar on that edge — the vertical bar for .trailing.
struct Carousel: View {
    let style: ScrollEdgeEffectStyle?
    var axis: Axis = .horizontal
    var edge: Edge.Set = .trailing
    var inBar = false

    var body: some View {
        if inBar {
            NavigationStack {
                content
                    .navigationTitle("Probe")
                    .toolbar { Button("Share", systemImage: "square.and.arrow.up") {} }
            }
        } else {
            content
        }
    }

    @ViewBuilder private var content: some View {
        let layout = axis == .horizontal ? AnyLayout(HStackLayout(spacing: 16)) : AnyLayout(VStackLayout(spacing: 16))
        let carousel = ScrollView(axis == .horizontal ? .horizontal : .vertical) {
            layout {
                ForEach(0..<12, id: \.self) { index in
                    RoundedRectangle(cornerRadius: 24)
                        .fill(cardColors[index % cardColors.count])
                        .frame(width: axis == .horizontal ? 300 : nil, height: axis == .horizontal ? nil : 200)
                }
            }
            .padding(axis == .horizontal ? .vertical : .horizontal, 40)
        }
        // Vertical cards start below the top bar; start in the middle so some sit under it.
        .defaultScrollAnchor(axis == .vertical ? .center : .leading)
        .onGeometryChange(for: EdgeInsets.self) { $0.safeAreaInsets } action: { insets in
            log("CAROUSEL safe=(t:\(insets.top) l:\(insets.leading) b:\(insets.bottom) r:\(insets.trailing))")
        }
        if let style {
            carousel.scrollEdgeEffectStyle(style, for: edge)
        } else {
            carousel.scrollEdgeEffectHidden(for: edge)
        }
    }
}

final class UIKitCarouselController: UIViewController {
    private let scrollView = UIScrollView()

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        scrollView.frame = view.bounds
        scrollView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        scrollView.rightEdgeEffect.style = .soft
        scrollView.rightEdgeEffect.isHidden = mode == "edgeUIKitHidden"
        view.addSubview(scrollView)
        for index in 0..<12 {
            let card = UIView(frame: CGRect(x: CGFloat(index) * 316, y: 40, width: 300, height: 400))
            card.backgroundColor = [.systemRed, .systemOrange, .systemYellow, .systemGreen,
                                    .systemBlue, .systemPurple][index % 6]
            card.layer.cornerRadius = 24
            scrollView.addSubview(card)
        }
        scrollView.contentSize = CGSize(width: 12 * 316, height: 480)
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        log("UIKITCAROUSEL safe=\(fmt(scrollView.safeAreaInsets)) adjusted=\(fmt(scrollView.adjustedContentInset))")
    }
}
