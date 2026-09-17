import AVKit
import SwiftUI

struct PlayerScreen: View {
    let player: AVPlayer
    let chapters: [Chapter]
    @State private var showsChapters = false

    var body: some View {
        NavigationStack {
            ZStack {
                Color.black
                    .ignoresSafeArea()
                VideoPlayer(player: player)
                    .aspectRatio(16 / 9, contentMode: .fit)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                VStack {
                    Spacer()
                    PlaybackControls(player: player)
                        .padding(.bottom, 24)
                }
            }
            .overlay(alignment: .trailing) {
                if showsChapters {
                    ChapterList(chapters: chapters, player: player)
                        .frame(width: 320)
                        .background(.thinMaterial)
                }
            }
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Chapters", systemImage: "list.bullet") { showsChapters.toggle() }
                }
            }
        }
    }
}

struct Chapter: Identifiable {
    let id: Int
    let title: String
    let start: Double
}

struct PlaybackControls: View {
    let player: AVPlayer
    var body: some View {
        HStack(spacing: 40) {
            Button("Back 15", systemImage: "gobackward.15") { player.seek(by: -15) }
            Button("Play", systemImage: "play.fill") { player.play() }
            Button("Forward 15", systemImage: "goforward.15") { player.seek(by: 15) }
        }
        .labelStyle(.iconOnly)
        .font(.title)
    }
}

struct ChapterList: View {
    let chapters: [Chapter]
    let player: AVPlayer
    var body: some View {
        List(chapters) { chapter in
            Button(chapter.title) { player.seek(to: CMTime(seconds: chapter.start, preferredTimescale: 600)) }
        }
    }
}

private extension AVPlayer {
    func seek(by seconds: Double) {
        seek(to: currentTime() + CMTime(seconds: seconds, preferredTimescale: 600))
    }
}
