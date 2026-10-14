// What does `toolbarVerticalEdge` read inside a toolbar item, and where does the item
// go? Logs, for every reader, the edge it reads and its global frame, each time
// either changes. The frame tells which bar holds the item: a vertical bar sits in
// the trailing safe-area inset, a horizontal bottom bar above the bottom edge.
//
// Pick the case with a launch argument, -mode <name>:
//   items      a NavigationStack with three bottom-bar items: a Menu whose label
//              switches HStack ↔ VStack on the edge (.verticalPreferred), a Slider
//              (.horizontalOnly) and a custom view (.automatic); plus a content reader
//   automatic  the same screen, but the Menu keeps the default .automatic axis
//   disabled   the same screen with .toolbarVerticalBehavior(.disabled)
//   sheet      the `items` screen presents a sheet whose own NavigationStack has
//              a Close item and .toolbarVerticalBehavior(.disabled)
//   tabs       three tabs; the first holds nine symbol items and
//              .toolbarVerticalCompressionBehavior(.prefersTabBar)
//   toolbar    the same with .prefersToolbarItems
// Build and run: README.md in this directory.
import SwiftUI

@main
struct ToolbarEdgeProbeApp: App {
    var body: some Scene {
        WindowGroup { ProbeRoot() }
    }
}

struct ProbeRoot: View {
    private let mode = UserDefaults.standard.string(forKey: "mode") ?? "items"

    var body: some View {
        switch mode {
        case "automatic":
            ItemsScreen(menuAxis: .automatic)
        case "disabled":
            ItemsScreen().toolbarVerticalBehavior(.disabled)
        case "sheet":
            SheetPresenter()
        case "tabs":
            TabsScreen(behavior: .prefersTabBar)
        case "toolbar":
            TabsScreen(behavior: .prefersToolbarItems)
        default:
            ItemsScreen()
        }
    }
}

/// Logs the edge it reads and its global frame.
struct EdgeReader<Content: View>: View {
    @Environment(\.toolbarVerticalEdge) private var edge
    let name: String
    @ViewBuilder let content: (HorizontalEdge?) -> Content
    @State private var frame: CGRect = .zero

    var body: some View {
        content(edge)
            .onGeometryChange(for: CGRect.self) { $0.frame(in: .global) } action: { newFrame in
                frame = newFrame
                report()
            }
            .onChange(of: edge, initial: true) { report() }
    }

    private func report() {
        let side = switch edge {
        case .leading: "leading"
        case .trailing: "trailing"
        case nil: "nil"
        }
        NSLog("TBPROBE %@ edge=%@ frame=(%.1f, %.1f, %.1f, %.1f)", name, side,
              frame.minX, frame.minY, frame.width, frame.height)
    }
}

struct ItemsScreen: View {
    var menuAxis: ToolbarItemAxisBehavior = .verticalPreferred
    @State private var width: Double = 4

    var body: some View {
        NavigationStack {
            VStack {
                EdgeReader(name: "content") { _ in Text("Canvas") }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .navigationTitle("Probe")
            .toolbar {
                ToolbarItem(placement: .bottomBar) {
                    Menu {
                        Button("2 pt") { width = 2 }
                        Button("4 pt") { width = 4 }
                    } label: {
                        EdgeReader(name: menuAxis == .automatic ? "menu.automatic" : "menu.verticalPreferred") { edge in
                            let layout = edge == nil
                                ? AnyLayout(HStackLayout()) : AnyLayout(VStackLayout())
                            layout {
                                Capsule().frame(width: 24, height: width)
                                Text("\(Int(width)) pt").font(.caption2)
                            }
                        }
                    }
                }
                .axisBehavior(menuAxis)

                ToolbarItem(placement: .bottomBar) {
                    EdgeReader(name: "slider.horizontalOnly") { _ in
                        Slider(value: $width, in: 2...6, step: 2) { Text("Line width") }
                            .frame(width: 140)
                    }
                }
                .axisBehavior(.horizontalOnly)

                ToolbarItem(placement: .bottomBar) {
                    EdgeReader(name: "custom.automatic") { _ in
                        HStack {
                            Circle().frame(width: 12, height: 12)
                            Text("Ink")
                        }
                    }
                }

                ToolbarItem(placement: .primaryAction) {
                    Button("Share", systemImage: "square.and.arrow.up") {}
                }
            }
        }
    }
}

struct SheetPresenter: View {
    @State private var showsSheet = false

    var body: some View {
        ItemsScreen()
            .task {
                try? await Task.sleep(for: .seconds(2))
                showsSheet = true
            }
            .sheet(isPresented: $showsSheet) {
                NavigationStack {
                    VStack {
                        EdgeReader(name: "sheet.content") { _ in Text("Help") }
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .navigationTitle("Help")
                    .toolbar {
                        ToolbarItem(placement: .cancellationAction) {
                            Button(role: .close) { showsSheet = false }
                        }
                    }
                    .toolbarVerticalBehavior(.disabled)
                }
            }
    }
}

struct TabsScreen: View {
    let behavior: ToolbarVerticalCompressionBehavior
    private let symbols = ["pencil", "eraser", "lasso", "scissors", "paintbrush",
                           "ruler", "crop", "wand.and.stars", "textformat"]

    var body: some View {
        TabView {
            Tab("Draw", systemImage: "pencil.tip") {
                NavigationStack {
                    Text("Canvas")
                        .navigationTitle("Draw")
                        .toolbar {
                            ForEach(symbols, id: \.self) { symbol in
                                ToolbarItem(placement: .bottomBar) {
                                    Button(symbol, systemImage: symbol) {}
                                }
                            }
                        }
                        .toolbarVerticalCompressionBehavior(behavior)
                }
            }
            Tab("Library", systemImage: "photo.on.rectangle") { Text("Library") }
            Tab("Settings", systemImage: "gear") { Text("Settings") }
        }
    }
}
