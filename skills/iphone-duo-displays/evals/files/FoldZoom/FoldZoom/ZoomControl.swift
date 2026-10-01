import SwiftUI

/// Fold-to-zoom: half-folding the iPhone Duo zooms the viewfinder; a click plays on
/// every hinge update so it feels mechanical, and at 175° we switch to flat mode.
struct ZoomControl: View {
    @Binding var zoom: Double
    @State private var isFlatMode = false
    let clicker: Clicker

    var body: some View {
        ViewfinderOverlay(zoom: zoom, isFlatMode: isFlatMode)
            .onHingeChange { _, context in
                guard let hinge = context.hinge else { return }
                clicker.play()
                isFlatMode = hinge.angle.degrees >= 175
                if hinge.status == .partiallyOpen {
                    zoom = 1 + (180 - hinge.angle.degrees) / 60
                }
            }
    }
}

struct ViewfinderOverlay: View {
    let zoom: Double
    let isFlatMode: Bool
    var body: some View {
        Text(isFlatMode ? "Flat" : String(format: "%.1f×", zoom))
    }
}

final class Clicker {
    func play() { /* plays a short click sound */ }
}
