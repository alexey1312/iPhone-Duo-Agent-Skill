import UIKit

/// Our own animated tab bar (Lottie icons) over a container of child screens.
/// Deployment target: iOS 17.
final class RootViewController: UIViewController {
    private let tabBar = AnimatedTabBar(items: [
        .init(title: "Today", animation: "sun"),
        .init(title: "Library", animation: "books"),
        .init(title: "Search", animation: "magnifier"),
        .init(title: "Profile", animation: "person"),
    ])
    private let container = UIView()

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        for subview in [container, tabBar] {
            subview.translatesAutoresizingMaskIntoConstraints = false
            view.addSubview(subview)
        }
        // The safe area keeps the bar clear of the home indicator and the camera.
        NSLayoutConstraint.activate([
            container.topAnchor.constraint(equalTo: view.topAnchor),
            container.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            container.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            container.bottomAnchor.constraint(equalTo: tabBar.topAnchor),

            tabBar.leadingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.leadingAnchor),
            tabBar.trailingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.trailingAnchor),
            tabBar.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor),
            tabBar.heightAnchor.constraint(equalToConstant: 64),
        ])
    }
}

/// A horizontal row of icon-only buttons; each plays a Lottie animation when selected.
final class AnimatedTabBar: UIView {
    struct Item {
        let title: String
        let animation: String
    }

    private let stack = UIStackView()

    init(items: [Item]) {
        super.init(frame: .zero)
        stack.axis = .horizontal
        stack.distribution = .fillEqually
        stack.frame = bounds
        stack.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        addSubview(stack)
        for item in items {
            let button = UIButton(type: .system)
            button.accessibilityLabel = item.title
            stack.addArrangedSubview(button)
        }
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) is not supported") }
}
