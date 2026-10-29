import SwiftUI

@main
struct PuzzlerApp: App {
    var body: some Scene {
        WindowGroup {
            GameView()
                .ignoresSafeArea()
                .persistentSystemOverlays(.hidden)
        }
    }
}
