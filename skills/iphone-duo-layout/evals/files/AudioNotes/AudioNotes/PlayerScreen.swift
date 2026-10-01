import SwiftUI

/// The audio note player. On iPhone Duo the Up Next list floats over the player
/// and should collapse while it does; the details pane re-lays itself out for the
/// split's axis.
struct PlayerScreen: View {
    let note: AudioNote
    let queue: [AudioNote]

    var body: some View {
        NavigationStack {
            ArrangementView {
                UpNextView(queue: queue)
            } secondary: {
                PlayerView(note: note)
            }
            .arrangementViewStyle(.overlay)
            .navigationTitle(note.title)
        }
    }
}

struct NoteDetailsScreen: View {
    let note: AudioNote

    var body: some View {
        ArrangementView {
            TranscriptView(note: note)
                .splitArrangementLayoutRatio(0.4)
        } secondary: {
            DetailsView(note: note)
        }
        .arrangementViewStyle(.split)
    }
}

enum UpNextMinimization { case collapsed, expanded }

struct UpNextView: View {
    let queue: [AudioNote]
    @Environment(\.overlayArrangementZIndex) private var zIndex: Int

    var body: some View {
        UpNextList(queue: queue, minimization: zIndex > 0 ? .collapsed : .expanded)
    }
}

struct DetailsView: View {
    let note: AudioNote
    @Environment(\.splitArrangementAxis) private var axis

    var body: some View {
        let layout: AnyLayout = axis == .horizontal
            ? AnyLayout(VStackLayout())
            : AnyLayout(HStackLayout())
        layout {
            Waveform(note: note)
            NoteMetadata(note: note)
        }
    }
}

struct AudioNote: Identifiable {
    let id: UUID
    let title: String
    let duration: Duration
}

struct UpNextList: View {
    let queue: [AudioNote]
    let minimization: UpNextMinimization

    var body: some View {
        List(minimization == .collapsed ? Array(queue.prefix(1)) : queue) { note in
            Text(note.title)
        }
    }
}

struct PlayerView: View {
    let note: AudioNote
    var body: some View { Text(note.title).font(.largeTitle) }
}

struct TranscriptView: View {
    let note: AudioNote
    var body: some View { ScrollView { Text("Transcript of \(note.title)") } }
}

struct Waveform: View {
    let note: AudioNote
    var body: some View { Rectangle().fill(.tint.opacity(0.3)) }
}

struct NoteMetadata: View {
    let note: AudioNote
    var body: some View { Text(note.duration.formatted()) }
}
