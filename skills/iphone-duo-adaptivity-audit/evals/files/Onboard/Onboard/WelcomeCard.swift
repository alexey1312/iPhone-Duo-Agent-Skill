import SwiftUI
import UIKit

/// The first onboarding card. It is sized to the screen so it looks the same
/// on every iPhone.
struct WelcomeCard: View {
    private let cardWidth = UIScreen.main.bounds.width * 0.86
    private let cardHeight = UIScreen.main.bounds.height * 0.55

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "sparkles").font(.system(size: 56))
            Text("Welcome to Onboard").font(.title.bold())
            Text("Plan trips with friends, split costs, keep everyone in the loop.")
                .multilineTextAlignment(.center)
        }
        .padding(24)
        .frame(width: cardWidth, height: cardHeight)
        .background(.background, in: .rect(cornerRadius: 28))
        .shadow(radius: 12)
    }
}
