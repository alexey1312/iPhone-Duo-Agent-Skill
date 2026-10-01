// Where do an ArrangementView's environment values reach, and what does each style do
// with its two views? Logs, for the primary and the secondary view, the
// `overlayArrangementZIndex` and `splitArrangementAxis` that the content's root view
// reads, the ones a view nested inside it reads, and the global frame of each.
//
// Pick the case with a launch argument, -mode <name>:
//   overlay, split, splitH, splitV  the root view is a custom View placed directly
//                                   (`.overlay`, `.split`, `.split.axes(.horizontal)`,
//                                   `.split.axes(.vertical)`)
//   overlayModified                 the same root view with a modifier applied
//   overlayWrapped                  the same view, wrapped in a VStack
//   overlaySmall                    a 200 × 120 primary, to see where the overlay puts it
//   overlayLeading                  the primary with `.overlayArrangementEdge(.leading)`
//   splitRatio                      `.split` with `.splitArrangementLayoutRatio(0.3)` on the primary
// Build and run: README.md in this directory.
import SwiftUI

@main
struct ArrangementProbeApp: App {
    var body: some Scene {
        WindowGroup { ProbeRoot() }
    }
}

struct ProbeRoot: View {
    private let mode = UserDefaults.standard.string(forKey: "mode") ?? "overlay"

    var body: some View {
        NavigationStack {
            switch mode {
            case "split":
                ArrangementView { Pane(name: "primary", color: .orange) }
                    secondary: { Pane(name: "secondary", color: .teal) }
                    .arrangementViewStyle(.split)
            case "splitH":
                ArrangementView { Pane(name: "primary", color: .orange) }
                    secondary: { Pane(name: "secondary", color: .teal) }
                    .arrangementViewStyle(.split.axes(.horizontal))
            case "splitV":
                ArrangementView { Pane(name: "primary", color: .orange) }
                    secondary: { Pane(name: "secondary", color: .teal) }
                    .arrangementViewStyle(.split.axes(.vertical))
            case "overlayModified":
                ArrangementView { Pane(name: "primary", color: .orange).padding(0) }
                    secondary: { Pane(name: "secondary", color: .teal).padding(0) }
                    .arrangementViewStyle(.overlay)
            case "overlayWrapped":
                ArrangementView { VStack { Pane(name: "primary", color: .orange) } }
                    secondary: { VStack { Pane(name: "secondary", color: .teal) } }
                    .arrangementViewStyle(.overlay)
            case "overlaySmall":
                ArrangementView { Pane(name: "primary", color: .orange).frame(width: 200, height: 120) }
                    secondary: { Pane(name: "secondary", color: .teal) }
                    .arrangementViewStyle(.overlay)
            case "overlayLeading":
                ArrangementView { Pane(name: "primary", color: .orange).overlayArrangementEdge(HorizontalEdge.leading) }
                    secondary: { Pane(name: "secondary", color: .teal) }
                    .arrangementViewStyle(.overlay)
            case "splitRatio":
                ArrangementView { Pane(name: "primary", color: .orange).splitArrangementLayoutRatio(0.3) }
                    secondary: { Pane(name: "secondary", color: .teal) }
                    .arrangementViewStyle(.split)
            default:
                ArrangementView { Pane(name: "primary", color: .orange) }
                    secondary: { Pane(name: "secondary", color: .teal) }
                    .arrangementViewStyle(.overlay)
            }
        }
        .onAppear { NSLog("DUOARR mode=%@", mode) }
    }
}

/// The view under test: it reads the environment itself, then hands it to a child.
struct Pane: View {
    let name: String
    let color: Color
    @Environment(\.overlayArrangementZIndex) private var zIndex
    @Environment(\.splitArrangementAxis) private var axis

    var body: some View {
        Leaf(name: name, outerZIndex: zIndex, outerAxis: axis)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(color.opacity(0.6))
            .onGeometryChange(for: CGRect.self) { $0.frame(in: .global) } action: { frame in
                NSLog("DUOARR %@ frame=%@", name, NSCoder.string(for: frame))
            }
    }
}

/// A view nested inside `Pane`.
struct Leaf: View {
    let name: String
    let outerZIndex: Int
    let outerAxis: Axis?
    @Environment(\.overlayArrangementZIndex) private var zIndex
    @Environment(\.splitArrangementAxis) private var axis

    private var line: String {
        "\(name) pane(zIndex=\(outerZIndex) axis=\(describe(outerAxis))) "
            + "leaf(zIndex=\(zIndex) axis=\(describe(axis)))"
    }

    var body: some View {
        Text(line)
            .font(.caption.monospaced())
            .padding()
            .onChange(of: line, initial: true) { NSLog("DUOARR %@", line) }
    }

    private func describe(_ axis: Axis?) -> String {
        switch axis {
        case .horizontal: "horizontal"
        case .vertical: "vertical"
        case nil: "nil"
        }
    }
}
