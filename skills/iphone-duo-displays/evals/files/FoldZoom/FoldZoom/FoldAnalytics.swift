import SwiftUI

/// Logs how people use the fold. Attached to the app's root view.
struct FoldAnalytics: ViewModifier {
    func body(content: Content) -> some View {
        content.onHingeChange { old, new in
            if new.hinge?.status != old.hinge?.status {
                Telemetry.send("device_folded", ["status": String(describing: new.hinge?.status)])
            }
        }
    }
}

enum Telemetry {
    static func send(_ event: String, _ properties: [String: String]) {
        print(event, properties)
    }
}
