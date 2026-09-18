import SwiftUI

@main
struct DuoProbe: App {
    var body: some Scene {
        WindowGroup {
            GeometryReader { p in
                Color.black.onAppear { dump(p) }
                    .onChange(of: p.size) { _, _ in dump(p) }
            }
        }
    }
    @MainActor static func nothing() {}
}

@MainActor func dump(_ p: GeometryProxy) {
    let i = p.safeAreaInsets
    var out = "DUOPROBE size=\(p.size.width)x\(p.size.height)"
    out += " safeArea(t:\(i.top) l:\(i.leading) b:\(i.bottom) tr:\(i.trailing))"
    let div = p.reservedRegions(kind: .division, options: .includeInactive)
    let occ = p.reservedRegions(kind: .occlusion, options: .includeInactive)
    out += " divisions=\(div.map { "\($0.frame)|active=\($0.isActive)" })"
    out += " occlusions=\(occ.map { "\($0.frame)|active=\($0.isActive)" })"
    if let s = UIApplication.shared.connectedScenes.first as? UIWindowScene {
        out += " scale=\(s.screen.traitCollection.displayScale) screenBounds=\(s.screen.bounds)"
        out += " verticalBarEdge=\(s.keyWindow?.traitCollection.verticalBarEdge.rawValue ?? -1)"
        out += " hSize=\(s.keyWindow?.traitCollection.horizontalSizeClass.rawValue ?? -1)"
        out += " vSize=\(s.keyWindow?.traitCollection.verticalSizeClass.rawValue ?? -1)"
    }
    print(out)
}
