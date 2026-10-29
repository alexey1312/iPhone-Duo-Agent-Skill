import SpriteKit
import SwiftUI

struct GameView: View {
    @State private var scene = BoardScene()

    var body: some View {
        GeometryReader { proxy in
            SpriteView(scene: scene)
                .onChange(of: proxy.size, initial: true) { _, size in
                    scene.size = size
                }
        }
    }
}

final class BoardScene: SKScene {
    override init() {
        super.init(size: CGSize(width: 1, height: 1))
        scaleMode = .resizeFill
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) { fatalError("init(coder:) is not supported") }
}
