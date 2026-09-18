import SwiftUI

extension ToolbarContent {
    @ToolbarContentBuilder
    func duoHorizontalOnly() -> some ToolbarContent {
        if #available(iOS 27.1, *) {
            self.axisBehavior(.horizontalOnly)
        } else {
            self
        }
    }
}

struct Uses: View {
    var body: some View {
        NavigationStack {
            Color.clear.toolbar {
                ToolbarItem(placement: .primaryAction) { Button("Edit") {} }
                    .duoHorizontalOnly()
            }
        }
    }
}
