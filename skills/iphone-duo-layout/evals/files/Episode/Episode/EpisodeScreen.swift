import SwiftUI

/// The episode screen: player on the leading side, transcript on the trailing side.
/// We only ever want them side by side, never stacked.
struct EpisodeScreen: View {
    let episode: EpisodeModel

    var body: some View {
        NavigationStack {
            ArrangementView {
                PlayerPane(episode: episode)
            } secondary: {
                TranscriptPane(episode: episode)
            }
            .arrangementViewStyle(.split.axes(.horizontal))
        }
    }
}

struct TranscriptPane: View {
    let episode: EpisodeModel
    @State private var didLogView = false

    var body: some View {
        ScrollView {
            Text(episode.transcript).padding()
        }
        .onGeometryChange(for: CGFloat.self) { $0.size.height } action: { height in
            // A transcript taller than 300 pt is on screen and readable.
            if height > 300, !didLogView {
                didLogView = true
                Analytics.log("transcript_viewed", episode: episode.id)
            }
        }
    }
}

struct PlayerPane: View {
    let episode: EpisodeModel
    var body: some View { Text(episode.title).font(.title) }
}

struct EpisodeModel: Identifiable {
    let id: UUID
    let title: String
    let transcript: String
}

enum Analytics {
    static func log(_ event: String, episode: UUID) { print(event, episode) }
}
