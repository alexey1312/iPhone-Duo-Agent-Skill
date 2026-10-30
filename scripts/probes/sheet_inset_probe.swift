import SwiftUI
import UIKit

// Checks, on a booted iPhone Duo simulator, two claims of Apple's `app-resizability` skill
// (Xcode 27.1, references/safe-area-task.md):
//   rule 11  "A sheet carries its own inset for a vertical bar. Its content is inset even where
//            the presenting view is not."
//   rule 6   "Interface orientation is a poor proxy: two physically different poses report the
//            same orientation and the same geometry."
// One mode per launch:
//
//   -mode plain              the presenter only: a plain view controller, no navigation bar
//   -mode sheet              the presenter presents a sheet with the default style (.automatic) that holds
//                            a plain view controller
//   -mode sheetNav           the sheet holds a UINavigationController with a title and two bar button
//                            items that have both an image and a title
//   -mode sheetNavDisabled   as sheetNav, with preferredVerticalBarBehavior .disabled on the sheet's
//                            root view controller
//   -mode presenterDisabled  as sheetNav, with .disabled on the presenter instead of the sheet
//   -mode swiftUISheet       a SwiftUI .sheet whose content is a NavigationStack with a .toolbar; reads
//                            the safe area through GeometryReader and @Environment(\.toolbarVerticalEdge)
//   -mode swiftUIPresenterDisabled  as swiftUISheet, with .toolbarVerticalBehavior(.disabled) on the
//                            presenter only
//
// Add `-style page` to a UIKit sheet mode to set modalPresentationStyle .pageSheet. Without it the
// sheet keeps the default, .automatic, and the log line PRESENTED shows what that resolves to.
//
// The sheet is presented without animation as soon as the presenter appears.
// UIKit views log in viewDidLayoutSubviews (or layoutSubviews), SwiftUI readers on every body
// evaluation of their GeometryReader. A line is logged only when its content changes, so the
// pass number shows how many passes it took. Every UIKit reader logs once more, tagged `late`,
// 4 s after launch, outside a layout pass. The presenter also logs its trait in viewDidLoad,
// before its view is in a window, next to the trait of a UIView that is never added to one.
// Labels: PRESENTER, SHEET (the sheet's root view controller), SHEETNAV (the navigation controller
// that holds it), SUI-PRESENTER and SUI-SHEET (GeometryReader), and the same with -UIVIEW (a UIView
// inside the SwiftUI view, for the UIKit trait).
// NSLog, so the lines survive a plain `simctl launch`; `--console-pty` delivers them too.
// Build and run: README.md in this directory.

func log(_ message: String) { NSLog("SHEETPROBE %@", message) }
func fmt(_ r: CGRect) -> String { String(format: "(%.1f, %.1f, %.1f, %.1f)", r.minX, r.minY, r.width, r.height) }
func fmt(_ i: UIEdgeInsets) -> String { String(format: "(t:%.1f l:%.1f b:%.1f r:%.1f)", i.top, i.left, i.bottom, i.right) }
func fmt(_ i: EdgeInsets) -> String {
    String(format: "(t:%.1f l:%.1f b:%.1f r:%.1f)", i.top, i.leading, i.bottom, i.trailing)
}
let mode = UserDefaults.standard.string(forKey: "mode") ?? "plain"
let style = UserDefaults.standard.string(forKey: "style") ?? "automatic"

func name(_ edge: UIVerticalBarEdge) -> String {
    switch edge {
    case .unspecified: "unspecified"
    case .leading: "leading"
    case .trailing: "trailing"
    @unknown default: "unknown"
    }
}

func name(_ edge: HorizontalEdge?) -> String {
    switch edge {
    case .leading: "leading"
    case .trailing: "trailing"
    case nil: "nil"
    }
}

func name(_ orientation: UIInterfaceOrientation) -> String {
    switch orientation {
    case .portrait: "portrait"
    case .portraitUpsideDown: "portraitUpsideDown"
    case .landscapeLeft: "landscapeLeft"
    case .landscapeRight: "landscapeRight"
    case .unknown: "unknown"
    @unknown default: "unknown"
    }
}

func name(_ sizeClass: UIUserInterfaceSizeClass) -> String {
    switch sizeClass {
    case .compact: "compact"
    case .regular: "regular"
    case .unspecified: "unspecified"
    @unknown default: "unknown"
    }
}

func name(_ sizeClass: UserInterfaceSizeClass?) -> String {
    switch sizeClass {
    case .compact: "compact"
    case .regular: "regular"
    case nil: "nil"
    @unknown default: "unknown"
    }
}

@MainActor func sceneDescription(_ scene: UIWindowScene?) -> String {
    guard let scene else { return "scene=nil" }
    let geometry = scene.effectiveGeometry
    return "scene=\(name(geometry.interfaceOrientation))(\(geometry.interfaceOrientation.rawValue)) "
        + "sceneBounds=\(fmt(geometry.coordinateSpace.bounds))"
}

@MainActor func regions(_ view: UIView) -> String {
    func describe(_ region: UIView.ReservedRegion) -> String {
        "\(fmt(region.frame))|m\(fmt(region.margins))|active=\(region.isActive)"
    }
    let divisions = view.reservedRegions(kind: .division, options: .includeInactive)
    let occlusions = view.reservedRegions(kind: .occlusion, options: .includeInactive)
    return "divisions=[\(divisions.map(describe).joined(separator: ", "))] "
        + "occlusions=[\(occlusions.map(describe).joined(separator: ", "))]"
}

/// Everything the brief asks for, read from one UIKit view.
@MainActor func describe(_ view: UIView) -> String {
    let traits = view.traitCollection
    return "safe=\(fmt(view.safeAreaInsets)) frameInWindow=\(fmt(view.convert(view.bounds, to: nil))) "
        + "verticalBarEdge=\(traits.verticalBarEdge.rawValue)(\(name(traits.verticalBarEdge))) "
        + "size=\(name(traits.horizontalSizeClass))/\(name(traits.verticalSizeClass)) "
        + "\(sceneDescription(view.window?.windowScene)) \(regions(view))"
}

/// Logs a line for one label when its content differs from the previous line for that label.
@MainActor final class Reporter {
    static var readers: [() -> Void] = []
    private var passes = 0
    private var last = ""
    let label: String

    init(_ label: String) { self.label = label }

    func pass(_ content: String) {
        passes += 1
        guard content != last else { return }
        last = content
        log("\(label) pass=\(passes) \(content)")
    }

    func late(_ content: String) { log("\(label) late \(content)") }
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
        window.rootViewController = mode.hasPrefix("swiftUI")
            ? UIHostingController(rootView: SwiftUIPresenter()) : PresenterController()
        window.makeKeyAndVisible()
        self.window = window
        log("mode=\(mode) \(sceneDescription(windowScene))")
        DispatchQueue.main.asyncAfter(deadline: .now() + 4) {
            log("WINDOW late safe=\(fmt(window.safeAreaInsets)) "
                + "verticalBarEdge=\(window.traitCollection.verticalBarEdge.rawValue)")
            Reporter.readers.forEach { $0() }
        }
    }
}

// MARK: - UIKit modes

final class PresenterController: UIViewController {
    private let reporter = Reporter("PRESENTER")
    private var presented = false

    override var preferredVerticalBarBehavior: UIVerticalBarBehavior {
        mode == "presenterDisabled" ? .disabled : .automatic
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        // Before the view is in a window: what the trait reads when nothing has resolved it.
        log("PRESENTER viewDidLoad window=\(view.window == nil ? "nil" : "set") "
            + "verticalBarEdge=\(traitCollection.verticalBarEdge.rawValue) "
            + "detachedView=\(UIView().traitCollection.verticalBarEdge.rawValue)")
        view.backgroundColor = .systemTeal
        Reporter.readers.append { [weak self] in
            guard let self else { return }
            reporter.late(describe(view))
        }
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        reporter.pass(describe(view))
    }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        guard mode != "plain", !presented else { return }
        presented = true
        let content = SheetContentController()
        let sheet: UIViewController = mode == "sheet" ? content : SheetNavController(rootViewController: content)
        if style == "page" { sheet.modalPresentationStyle = .pageSheet }
        present(sheet, animated: false)
        log("PRESENTED style=\(sheet.modalPresentationStyle.rawValue) "
            + "controller=\(sheet.presentationController.map { String(describing: type(of: $0)) } ?? "nil")")
    }
}

/// The sheet's root view controller.
final class SheetContentController: UIViewController {
    private let reporter = Reporter("SHEET")

    override var preferredVerticalBarBehavior: UIVerticalBarBehavior {
        mode == "sheetNavDisabled" ? .disabled : .automatic
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemOrange
        title = "Sheet"
        navigationItem.rightBarButtonItems = [
            UIBarButtonItem(title: "Share", image: UIImage(systemName: "square.and.arrow.up"),
                            primaryAction: UIAction { _ in }),
            UIBarButtonItem(title: "Edit", image: UIImage(systemName: "pencil"), primaryAction: UIAction { _ in }),
        ]
        Reporter.readers.append { [weak self] in
            guard let self else { return }
            reporter.late(describe(view) + container())
        }
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        reporter.pass(describe(view) + container())
    }

    /// Where the presentation puts the sheet, and what its container view reports.
    private func container() -> String {
        let presented = navigationController ?? self
        guard let controller = presented.presentationController else { return " presentation=nil" }
        let presentedView = controller.presentedView.map { fmt($0.convert($0.bounds, to: nil)) } ?? "nil"
        let containerSafe = controller.containerView.map { fmt($0.safeAreaInsets) } ?? "nil"
        return " presentedView=\(presentedView) container.safe=\(containerSafe)"
    }
}

/// The navigation controller of sheetNav, logged on its own: its view has no bar of its own in its
/// safe area, so it shows what the sheet adds before the navigation bar does.
final class SheetNavController: UINavigationController {
    private let reporter = Reporter("SHEETNAV")

    override func viewDidLoad() {
        super.viewDidLoad()
        Reporter.readers.append { [weak self] in
            guard let self else { return }
            reporter.late(describe(view) + " navBar=\(fmt(navigationBar.convert(navigationBar.bounds, to: nil)))")
        }
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        reporter.pass(describe(view) + " navBar=\(fmt(navigationBar.convert(navigationBar.bounds, to: nil)))")
    }
}

// MARK: - swiftUISheet

struct SwiftUIPresenter: View {
    @State private var showsSheet = false

    var body: some View {
        SwiftUIReader(label: "SUI-PRESENTER", color: .teal)
            .toolbarVerticalBehavior(mode == "swiftUIPresenterDisabled" ? .disabled : .automatic)
            .task {
                try? await Task.sleep(for: .milliseconds(300))
                showsSheet = true
            }
            .sheet(isPresented: $showsSheet) {
                NavigationStack {
                    SwiftUIReader(label: "SUI-SHEET", color: .orange)
                        .navigationTitle("Sheet")
                        .toolbar {
                            ToolbarItem(placement: .primaryAction) {
                                Button("Share", systemImage: "square.and.arrow.up") {}
                            }
                            ToolbarItem(placement: .primaryAction) {
                                Button("Edit", systemImage: "pencil") {}
                            }
                        }
                }
            }
    }
}

/// A GeometryReader that logs its proxy, with a UIView behind it that logs the UIKit side.
/// The UIView ignores the safe area, so it fills the window or the sheet, as a UIKit root view does.
struct SwiftUIReader: View {
    let label: String
    let color: Color
    @Environment(\.toolbarVerticalEdge) private var edge
    @Environment(\.horizontalSizeClass) private var horizontal
    @Environment(\.verticalSizeClass) private var vertical

    var body: some View {
        GeometryReader { proxy in
            let _ = report(proxy)
            color.background(UIKitReader(label: "\(label)-UIVIEW").ignoresSafeArea())
        }
    }

    @MainActor private func report(_ proxy: GeometryProxy) {
        func describe(_ region: ReservedRegion) -> String {
            "\(fmt(region.frame))|m\(fmt(region.margins))|active=\(region.isActive)"
        }
        let divisions = proxy.reservedRegions(kind: .division, options: .includeInactive)
        let occlusions = proxy.reservedRegions(kind: .occlusion, options: .includeInactive)
        let scene = UIApplication.shared.connectedScenes.first as? UIWindowScene
        let content = "safe=\(fmt(proxy.safeAreaInsets)) size=\(fmt(CGRect(origin: .zero, size: proxy.size))) "
            + "global=\(fmt(proxy.frame(in: .global))) toolbarVerticalEdge=\(name(edge)) "
            + "sizeClass=\(name(horizontal))/\(name(vertical)) \(sceneDescription(scene)) "
            + "divisions=[\(divisions.map(describe).joined(separator: ", "))] "
            + "occlusions=[\(occlusions.map(describe).joined(separator: ", "))]"
        SwiftUIReporters.reporter(label).pass(content)
    }
}

@MainActor enum SwiftUIReporters {
    static var all: [String: Reporter] = [:]
    static func reporter(_ label: String) -> Reporter {
        if let reporter = all[label] { return reporter }
        let reporter = Reporter(label)
        all[label] = reporter
        return reporter
    }
}

struct UIKitReader: UIViewRepresentable {
    let label: String
    func makeUIView(context: Context) -> ReaderView { ReaderView(label: label) }
    func updateUIView(_ uiView: ReaderView, context: Context) {}
}

final class ReaderView: UIView {
    private let reporter: Reporter

    init(label: String) {
        reporter = Reporter(label)
        super.init(frame: .zero)
        Reporter.readers.append { [weak self] in
            guard let self else { return }
            reporter.late(describe(self))
        }
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) is not used") }

    override func layoutSubviews() {
        super.layoutSubviews()
        reporter.pass(describe(self))
    }
}
