import SwiftUI

struct Trail: Identifiable, Hashable {
    let id: UUID
    let name: String
    let lengthKilometers: Double
}

struct BoardScreen: View {
    @State private var openTrail: Trail?
    let trails: [Trail]
    private let columnCount = 4

    var body: some View {
        NavigationStack {
            ScrollView {
                LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: columnCount)) {
                    ForEach(trails) { trail in
                        Button { openTrail = trail } label: { TrailTile(trail: trail) }
                    }
                }
                .padding()
            }
            .navigationTitle("Trails")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button("Add Trail", systemImage: "plus") {}
                }
                ToolbarItem(placement: .bottomBar) {
                    Button("Filter", systemImage: "line.3.horizontal.decrease") {}
                }
            }
            .sheet(item: $openTrail) { trail in
                TrailSheet(trail: trail)
                    .presentationPlacement(side(of: trail))
            }
        }
        // The trailing sheet's Close button ended up under the status bar on the open
        // iPhone Duo, so vertical bars are off for the whole board.
        .toolbarVerticalBehavior(.disabled)
    }

    private func side(of trail: Trail) -> PresentationPlacement {
        let index = trails.firstIndex(of: trail) ?? 0
        return index % columnCount < columnCount / 2 ? .leading : .trailing
    }
}

struct TrailSheet: View {
    @Environment(\.dismiss) private var dismiss
    let trail: Trail

    var body: some View {
        NavigationStack {
            TrailMap(trail: trail)
                .navigationTitle(trail.name)
                .toolbar {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button("Close") { dismiss() }
                    }
                }
        }
    }
}

struct TrailTile: View {
    let trail: Trail
    var body: some View {
        VStack(alignment: .leading) {
            Text(trail.name).font(.headline)
            Text("\(trail.lengthKilometers, specifier: "%.1f") km").foregroundStyle(.secondary)
        }
    }
}

struct TrailMap: View {
    let trail: Trail
    var body: some View {
        Color.green.opacity(0.2).overlay(Text(trail.name))
    }
}
