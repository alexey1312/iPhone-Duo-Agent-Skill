import UIKit

/// Pushed onto the app's UINavigationController from the library list.
/// Brand guidelines want our own chevron instead of the system one, nothing else.
final class BookDetailViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        title = "Details"

        let chevron = UIButton(type: .system)
        chevron.setImage(UIImage(named: "BrandChevron"), for: .normal)
        chevron.accessibilityLabel = "Back"
        chevron.addAction(UIAction { [weak self] _ in
            self?.navigationController?.popViewController(animated: true)
        }, for: .touchUpInside)
        navigationItem.leftBarButtonItem = UIBarButtonItem(customView: chevron)

        navigationItem.rightBarButtonItem = UIBarButtonItem(
            title: "Share", image: UIImage(systemName: "square.and.arrow.up"),
            primaryAction: UIAction { _ in })
    }
}
