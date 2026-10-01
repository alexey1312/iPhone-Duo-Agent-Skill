import SwiftUI

/// A small capsule that names the current posture.
struct HingeBadge: View {
    @State private var title = "—"

    var body: some View {
        Text(title)
            .padding(.horizontal, 10)
            .background(.thinMaterial, in: .capsule)
            .onHingeChange { _, context in
                guard let hinge = context.hinge else { return }
                switch hinge.status {
                case .closed: title = "Closed"
                case .partiallyOpen: title = "Half open"
                case .fullyOpen: title = "Open"
                }
            }
    }
}
