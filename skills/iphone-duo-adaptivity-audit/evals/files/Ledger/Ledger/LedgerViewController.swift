import UIKit

/// The ledger list with a floating "Add entry" button. On iPhone Duo the button must
/// not sit on the crease, so it moves to the right half while the device is folded.
final class LedgerViewController: UIViewController {
    private let addButton = UIButton(configuration: .filled())

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        addButton.setTitle("Add entry", for: .normal)
        view.addSubview(addButton)
        NotificationCenter.default.addObserver(self, selector: #selector(foldStateRestored),
                                               name: .foldStateRestored, object: nil)
    }

    @objc private func foldStateRestored() {
        view.setNeedsLayout()
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        let size = addButton.intrinsicContentSize
        let x = FoldState.shared.isFolded ? view.bounds.width * 0.75 : view.bounds.midX
        addButton.bounds.size = size
        addButton.center = CGPoint(x: x, y: view.bounds.maxY - view.safeAreaInsets.bottom - size.height)
    }
}
