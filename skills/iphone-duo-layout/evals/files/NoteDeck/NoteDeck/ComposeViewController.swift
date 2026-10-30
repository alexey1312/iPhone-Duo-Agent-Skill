import SwiftUI
import UIKit

struct ComposeView: UIViewControllerRepresentable {
    func makeUIViewController(context: Context) -> ComposeViewController { ComposeViewController() }
    func updateUIViewController(_ controller: ComposeViewController, context: Context) {}
}

final class ComposeViewController: UIViewController, UITableViewDataSource {
    private let header = UILabel()
    private let attachments = UITableView()
    private let textView = UITextView()
    private var bottomConstraint: NSLayoutConstraint!

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        header.text = "New Note"
        header.font = .preferredFont(forTextStyle: .title2)
        attachments.dataSource = self
        attachments.register(UITableViewCell.self, forCellReuseIdentifier: "cell")
        attachments.contentInsetAdjustmentBehavior = .never
        textView.font = .preferredFont(forTextStyle: .body)
        for subview in [header, attachments, textView] {
            subview.translatesAutoresizingMaskIntoConstraints = false
            view.addSubview(subview)
        }
        NSLayoutConstraint.activate([
            header.topAnchor.constraint(equalTo: view.topAnchor, constant: 64),
            header.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 16),
            attachments.topAnchor.constraint(equalTo: header.bottomAnchor, constant: 8),
            attachments.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            attachments.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            textView.topAnchor.constraint(equalTo: attachments.bottomAnchor, constant: 8),
            textView.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 16),
            textView.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -16),
            textView.heightAnchor.constraint(equalToConstant: 120),
        ])
        bottomConstraint = textView.bottomAnchor.constraint(equalTo: view.bottomAnchor, constant: -34)
        bottomConstraint.isActive = true
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(keyboardWillChangeFrame(_:)),
            name: UIResponder.keyboardWillChangeFrameNotification,
            object: nil
        )
    }

    @objc private func keyboardWillChangeFrame(_ notification: Notification) {
        guard let frame = notification.userInfo?[UIResponder.keyboardFrameEndUserInfoKey] as? CGRect else { return }
        let local = view.convert(frame, from: nil)
        bottomConstraint.constant = -(view.bounds.height - local.minY) - 8
        view.layoutIfNeeded()
    }

    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int { 12 }

    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = tableView.dequeueReusableCell(withIdentifier: "cell", for: indexPath)
        cell.textLabel?.text = "Attachment \(indexPath.row + 1)"
        return cell
    }
}
