import SwiftUI

/// Shared label for the custom tools in the bottom bar.
/// Stacks the swatch above the caption when iPhone Duo shows a vertical bar.
struct ToolLabel<Swatch: View>: View {
    @Environment(\.toolbarVerticalEdge) private var verticalEdge
    let caption: String
    @ViewBuilder let swatch: () -> Swatch

    var body: some View {
        if verticalEdge != nil {
            VStack(spacing: 2) {
                swatch()
                Text(caption).font(.caption2)
            }
        } else {
            HStack {
                swatch()
                Text(caption).font(.caption)
            }
        }
    }
}

struct CanvasScreen: View {
    @State private var strokeWidth = 4.0
    @State private var opacity = 1.0

    var body: some View {
        NavigationStack {
            Canvas { _, _ in }
                .navigationTitle("Sketchpad")
                .toolbar {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button("Undo", systemImage: "arrow.uturn.backward") {}
                    }
                    ToolbarItem(placement: .bottomBar) {
                        Button("Pen", systemImage: "pencil.tip") {}
                    }
                    ToolbarItem(placement: .bottomBar) {
                        Button("Eraser", systemImage: "eraser") {}
                    }
                    ToolbarItem(placement: .bottomBar) {
                        Menu {
                            Picker("Stroke width", selection: $strokeWidth) {
                                ForEach([2.0, 4.0, 6.0], id: \.self) { Text("\(Int($0)) pt") }
                            }
                        } label: {
                            ToolLabel(caption: "\(Int(strokeWidth)) pt") {
                                Capsule().frame(width: 22, height: strokeWidth)
                            }
                        }
                    }
                    ToolbarItem(placement: .bottomBar) {
                        HStack {
                            ToolLabel(caption: "Opacity") {
                                Circle().opacity(opacity).frame(width: 12, height: 12)
                            }
                            Slider(value: $opacity)
                                .frame(width: 120)
                        }
                    }
                }
        }
    }
}
