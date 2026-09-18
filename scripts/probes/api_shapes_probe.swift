import SwiftUI
import UIKit
import AVFoundation

// --- Reserved regions: SwiftUI ---
struct RegionsView: View {
    var body: some View {
        GeometryReader { proxy in
            let divisions = proxy.reservedRegions(kind: .division)
            let inactive = proxy.reservedRegions(kind: .division, options: .includeInactive)
            let cameras = proxy.reservedRegions(kind: .occlusion)
            Color.clear
                .onAppear {
                    _ = divisions.map(\.frame)
                    _ = inactive.map(\.isActive)
                    _ = cameras.map(\.margins)
                }
        }
    }
}

// --- Reserved regions: UIKit ---
func uikitRegions(_ view: UIView) -> [CGRect] {
    let regions = view.reservedRegions(kind: .division)
    let withInactive = view.reservedRegions(kind: .division, options: .includeInactive)
    _ = withInactive.map(\.isActive)
    return regions.map(\.frame)
}

// --- Arrangements: SwiftUI ---
struct SplitArrangement: View {
    var body: some View {
        ArrangementView {
            Color.red
        } secondary: {
            Color.blue.splitArrangementLayoutRatio(0.4)
        }
        .arrangementViewStyle(.split.axes(.horizontal))
    }
}

struct OverlayArrangement: View {
    @Environment(\.overlayArrangementZIndex) private var zIndex
    @Environment(\.splitArrangementAxis) private var axis
    var body: some View {
        ArrangementView {
            Color.red.overlayArrangementEdge(VerticalEdge.bottom)
        } secondary: {
            Color.blue
        }
        .arrangementViewStyle(.overlay)
    }
}

// --- Arrangements: UIKit ---
@MainActor func uikitArrangement() {
    let vc = UIArrangementViewController()
    vc.setViewController(UIViewController(), for: .primary, animated: false)
    vc.setViewController(UIViewController(), for: .secondary, animated: false)
    vc.updateArrangement(.split.axes(.horizontal), animated: true)
    _ = vc.state(for: .primary)?.zIndex
    _ = vc.viewController(for: .secondary)
    _ = vc.placement(for: UIViewController())
}

// --- Hinge: SwiftUI ---
struct HingeView: View {
    @State private var angle: Angle = .zero
    var body: some View {
        Color.clear.onHingeChange { _, new in
            guard let hinge = new.hinge, hinge.status == .partiallyOpen else { return }
            angle = hinge.angle
        }
    }
}

// --- Hinge: UIKit ---
@MainActor func uikitHinge(_ view: UIView) {
    let interaction = UIHingeInteraction { _, update in
        guard let hinge = update.hinge else { return }
        switch hinge.status {
        case .closed, .partiallyOpen, .fullyOpen, .unknown: _ = hinge.angle
        @unknown default: break
        }
    }
    view.addInteraction(interaction)
}

// --- Vertical bars: SwiftUI ---
struct BarsView: View {
    @Environment(\.toolbarVerticalEdge) private var barEdge
    var body: some View {
        NavigationStack {
            Color.clear
                .toolbar {
                    ToolbarItem(placement: .topBarPinnedTrailing) {
                        Button("Done") {}
                    }
                    .axisBehavior(.verticalPreferred)
                    ToolbarItem(placement: .primaryAction) {
                        Button("Edit") {}
                    }
                    .axisBehavior(.horizontalOnly)
                }
                .toolbarVerticalCompressionBehavior(.prefersTabBar)
        }
        .toolbarVerticalBehavior(.disabled)
    }
}

// --- Vertical bars: UIKit ---
@MainActor func uikitBars(_ vc: UIViewController, _ item: UIBarButtonItem) {
    item.axisBehavior = .verticalPreferred
    item.visibilityPriority = .high
    vc.navigationItem.verticalBarCompressionBehavior = .prefersTabBar
    _ = vc.traitCollection.verticalBarEdge == .trailing
    vc.registerForTraitChanges(UITraitCollection.systemTraitsAffectingVerticalBarEdge) { (_: UIViewController, _) in }
    vc.setNeedsUpdateOfVerticalBarConfiguration()
}

// --- Container content margins (27.1) ---
struct MarginsView: View {
    var body: some View {
        GeometryReader { proxy in
            let margins = proxy.contentMargins(for: .container)
            Color.clear.padding(.leading, margins.leading)
        }
        .contentMargins(for: .container, edges: .horizontal)
    }
}

// --- Cameras ---
func cameraTypes() -> AVCaptureDevice.DiscoverySession {
    AVCaptureDevice.DiscoverySession(
        deviceTypes: [.builtInOuterUltraWideCamera, .builtInInnerUltraWideCamera],
        mediaType: .video,
        position: .front
    )
}
