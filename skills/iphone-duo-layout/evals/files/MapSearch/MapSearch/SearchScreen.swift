import MapKit
import SwiftUI

/// Search results float over the map; on iPhone Duo the arrangement takes care of
/// the fold.
struct SearchScreen: View {
    @State private var query = ""
    let results: [Place]

    var body: some View {
        NavigationStack {
            ArrangementView {
                ResultsPanel(results: results)
            } secondary: {
                Map()
            }
            .arrangementViewStyle(.overlay)
            .searchable(text: $query)
            .navigationTitle("Search")
        }
    }
}

struct ResultsPanel: View {
    let results: [Place]
    var body: some View {
        ResultsList(results: results)
            .frame(maxWidth: 360)
            .background(.regularMaterial, in: .rect(cornerRadius: 24))
            .padding()
    }
}

struct ResultsList: View {
    let results: [Place]
    @Environment(\.overlayArrangementZIndex) private var zIndex

    var body: some View {
        List(zIndex > 0 ? Array(results.prefix(3)) : results) { place in
            Text(place.name)
        }
    }
}

struct Place: Identifiable {
    let id: UUID
    let name: String
}
