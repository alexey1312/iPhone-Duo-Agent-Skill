import SwiftUI

/// Notes: a narrow outline on the leading side, the editor on the trailing side.
struct EditorScreen: View {
    @State private var selection: Note.ID?
    let notes: [Note]

    var body: some View {
        NavigationStack {
            ArrangementView {
                OutlineList(notes: notes, selection: $selection)
                    .splitArrangementLayoutRatio(0.3)
            } secondary: {
                NoteEditor(note: notes.first { $0.id == selection })
            }
            .arrangementViewStyle(.split.axes(.horizontal))
            .navigationTitle("Notes")
        }
    }
}

struct Note: Identifiable {
    let id: UUID
    var title: String
    var body: String
}

struct OutlineList: View {
    let notes: [Note]
    @Binding var selection: Note.ID?
    var body: some View {
        List(notes, selection: $selection) { note in Text(note.title) }
    }
}

struct NoteEditor: View {
    let note: Note?
    var body: some View {
        ScrollView { Text(note?.body ?? "Select a note").padding() }
    }
}
