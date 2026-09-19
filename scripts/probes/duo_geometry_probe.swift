import SwiftUI
import UIKit

// NSLog rather than print, so the numbers carry timestamps and survive a plain `simctl launch`, which
// returns straight away. `print` reaches the console too, for as long as `--console-pty` stays attached.
// Two readers, one inset 50 pt inside the other, so a proxy-local coordinate space can be told from a
// display one. `pass` counts body evaluations across both readers — they alternate — and the reserved
// regions are empty for the first few, so a probe that samples only `onAppear` reports `occlusions=[]`
// and misses them entirely.

@MainActor enum Pass { static var n = 0 }

@main
struct DuoProbe: App {
    var body: some Scene {
        WindowGroup {
            GeometryReader { outer in
                let _ = report("outer", outer)
                Color.black.overlay {
                    GeometryReader { inner in
                        let _ = report("inset+50", inner)
                        Color.clear
                    }
                    .padding(50)
                }
            }
        }
    }
}

@MainActor @discardableResult
func report(_ label: String, _ p: GeometryProxy) -> Int {
    Pass.n += 1
    let i = p.safeAreaInsets
    var out = "DUOPROBE pass=\(Pass.n) \(label) size=\(p.size.width)x\(p.size.height)"
    out += " safeArea(t:\(i.top) l:\(i.leading) b:\(i.bottom) tr:\(i.trailing))"
    out += " global=\(p.frame(in: .global))"
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
    NSLog("%@", out)
    return Pass.n
}
