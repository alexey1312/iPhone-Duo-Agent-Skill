import SwiftUI

struct NoteListView: View {
    let notes: [Note]
    @State private var composing = false

    var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: 12) {
                Text("Notes")
                    .font(.largeTitle.bold())
                ForEach(notes) { note in
                    VStack(alignment: .leading) {
                        Text(note.title).font(.headline)
                        Text(note.preview).foregroundStyle(.secondary)
                    }
                }
                Spacer()
            }
            .padding(.horizontal, 16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(.background)
            .ignoresSafeArea()
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button("New Note", systemImage: "square.and.pencil") { composing = true }
                }
            }
            .sheet(isPresented: $composing) {
                ComposeView()
            }
        }
    }
}
