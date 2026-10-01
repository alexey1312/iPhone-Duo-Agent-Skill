import SwiftUI

/// While a broadcast is live we draw a small red dot right beside the outer
/// display's camera hole, like a recording light.
struct BroadcastScreen: View {
    let isLive: Bool

    var body: some View {
        ZStack {
            BroadcastContent()
                .overlay {
                    GeometryReader { proxy in
                        let camera = proxy.reservedRegions(kind: .occlusion).first?.frame
                        Color.clear.preference(key: CameraFrameKey.self, value: camera)
                    }
                }
                .padding(16)
        }
        .overlayPreferenceValue(CameraFrameKey.self) { camera in
            if isLive, let camera {
                Circle()
                    .fill(.red)
                    .frame(width: 8, height: 8)
                    .position(x: camera.minX - 10, y: camera.midY)
            }
        }
    }
}

struct CameraFrameKey: PreferenceKey {
    static let defaultValue: CGRect? = nil
    static func reduce(value: inout CGRect?, nextValue: () -> CGRect?) {
        value = value ?? nextValue()
    }
}

struct BroadcastContent: View {
    var body: some View { Text("On air").font(.largeTitle) }
}
