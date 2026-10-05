import UIKit
import WebKit

/// Shows an article from our own server. The page draws a floating "Listen" button at
/// the bottom centre; tapping it starts text-to-speech in the app.
final class ArticleViewController: UIViewController, WKScriptMessageHandler {
    private let articleURL: URL
    private lazy var webView: WKWebView = {
        let configuration = WKWebViewConfiguration()
        configuration.userContentController.add(self, name: "listen")
        return WKWebView(frame: .zero, configuration: configuration)
    }()

    init(articleURL: URL) {
        self.articleURL = articleURL
        super.init(nibName: nil, bundle: nil)
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) is not supported") }

    override func viewDidLoad() {
        super.viewDidLoad()
        webView.frame = view.bounds
        webView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        view.addSubview(webView)
        webView.load(URLRequest(url: articleURL))
    }

    func userContentController(_ controller: WKUserContentController, didReceive message: WKScriptMessage) {
        guard message.name == "listen" else { return }
        SpeechPlayer.shared.read(articleURL)
    }
}

final class SpeechPlayer {
    static let shared = SpeechPlayer()
    func read(_ url: URL) {}
}
