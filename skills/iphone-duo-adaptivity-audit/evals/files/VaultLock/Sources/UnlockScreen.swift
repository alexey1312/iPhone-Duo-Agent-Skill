import LocalAuthentication
import SwiftUI

struct UnlockScreen: View {
    @State private var isUnlocked = false
    @State private var message: String?

    var body: some View {
        VStack(spacing: 24) {
            Image(systemName: "faceid")
                .font(.system(size: 64))
            Text("Unlock with Face ID")
                .font(.title2)
            Button("Use Face ID") { unlock() }
                .buttonStyle(.borderedProminent)
            if let message {
                Text(message)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
    }

    private func unlock() {
        let context = LAContext()
        context.localizedCancelTitle = "Enter Passcode"
        context.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics,
                               localizedReason: "Face ID is required to open your vault") { success, _ in
            Task { @MainActor in
                isUnlocked = success
                message = success ? nil : "Face ID didn't recognize you. Try again."
            }
        }
    }
}
