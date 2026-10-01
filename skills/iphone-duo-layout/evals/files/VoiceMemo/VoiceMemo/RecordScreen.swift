import SwiftUI

/// The record screen. The round Record button floats at the bottom centre and
/// should step off the crease only while the iPhone Duo is half folded.
struct RecordScreen: View {
    @State private var isRecording = false

    var body: some View {
        GeometryReader { proxy in
            ZStack {
                WaveformView()
                RecordButton(isRecording: $isRecording)
                    .position(buttonPosition(in: proxy))
            }
        }
    }

    private func buttonPosition(in proxy: GeometryProxy) -> CGPoint {
        let centred = CGPoint(x: proxy.size.width / 2, y: proxy.size.height - 72)
        guard let fold = proxy.reservedRegions(kind: .division, options: .includeInactive).first else {
            return centred
        }
        // A flat device reports a zero-width fold; anything wider means it is folded.
        if fold.frame.width > 0 {
            return CGPoint(x: fold.frame.maxX + (proxy.size.width - fold.frame.maxX) / 2, y: centred.y)
        }
        return centred
    }
}

struct WaveformView: View {
    var body: some View { Rectangle().fill(.tint.opacity(0.15)) }
}

struct RecordButton: View {
    @Binding var isRecording: Bool
    var body: some View {
        Button(isRecording ? "Stop" : "Record", systemImage: isRecording ? "stop.fill" : "record.circle") {
            isRecording.toggle()
        }
        .labelStyle(.iconOnly)
        .font(.system(size: 44))
    }
}
