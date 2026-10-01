import SwiftUI

/// The photo wall. Apple's iPhone Duo talk suggests an even number of grid columns
/// whenever a division region exists, so that's what we do.
struct GalleryGrid: View {
    let photos: [Photo]
    private let minimumTileWidth: CGFloat = 140

    var body: some View {
        GeometryReader { proxy in
            let hasVerticalFold = proxy.reservedRegions(kind: .division, options: .includeInactive)
                .contains { $0.frame.height > $0.frame.width }
            ScrollView {
                LazyVGrid(columns: columns(for: proxy.size.width, preferEven: hasVerticalFold), spacing: 8) {
                    ForEach(photos) { photo in
                        PhotoTile(photo: photo)
                    }
                }
                .padding(.horizontal, 12)
            }
        }
    }

    private func columns(for width: CGFloat, preferEven: Bool) -> [GridItem] {
        var count = max(Int(width / minimumTileWidth), 1)
        if preferEven, count > 1, !count.isMultiple(of: 2) { count -= 1 }
        return Array(repeating: GridItem(.flexible(), spacing: 8), count: count)
    }
}

struct Photo: Identifiable {
    let id: UUID
    let thumbnail: Image
}

struct PhotoTile: View {
    let photo: Photo
    var body: some View {
        photo.thumbnail
            .resizable()
            .aspectRatio(1, contentMode: .fill)
            .clipShape(.rect(cornerRadius: 10))
    }
}
