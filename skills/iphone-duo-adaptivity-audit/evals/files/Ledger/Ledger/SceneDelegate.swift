import UIKit

extension Notification.Name {
    static let foldStateRestored = Notification.Name("FoldStateRestored")
}

/// Fold handling for iPhone Duo: remember whether the device was folded when the app
/// left the foreground, so the layout is right when it comes back or launches from a
/// notification while folded.
final class FoldState {
    static let shared = FoldState()
    var isFolded = false
}

final class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?

    func scene(_ scene: UIScene, willConnectTo session: UISceneSession,
               options connectionOptions: UIScene.ConnectionOptions) {
        guard let windowScene = scene as? UIWindowScene else { return }
        let window = UIWindow(windowScene: windowScene)
        let root = LedgerViewController()
        root.view.addInteraction(UIHingeInteraction { _, update in
            FoldState.shared.isFolded = update.hinge?.status == .partiallyOpen
        })
        window.rootViewController = UINavigationController(rootViewController: root)
        window.makeKeyAndVisible()
        self.window = window
        FoldState.shared.isFolded = UserDefaults.standard.bool(forKey: "wasFolded")
    }

    func sceneWillResignActive(_ scene: UIScene) {
        UserDefaults.standard.set(FoldState.shared.isFolded, forKey: "wasFolded")
    }

    func sceneDidBecomeActive(_ scene: UIScene) {
        FoldState.shared.isFolded = UserDefaults.standard.bool(forKey: "wasFolded")
        NotificationCenter.default.post(name: .foldStateRestored, object: nil)
    }
}
