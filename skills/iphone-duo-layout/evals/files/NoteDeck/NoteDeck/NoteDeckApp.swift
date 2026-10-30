import SwiftUI

@main
struct NoteDeckApp: App {
    var body: some Scene {
        WindowGroup {
            NoteListView(notes: Note.samples)
        }
    }
}

struct Note: Identifiable {
    let id = UUID()
    let title: String
    let preview: String

    static let samples = [
        Note(title: "Groceries", preview: "Oat milk, lemons, rye bread"),
        Note(title: "Trip", preview: "Check in opens Thursday at 10"),
        Note(title: "Ideas", preview: "A widget for the outer display"),
    ]
}
