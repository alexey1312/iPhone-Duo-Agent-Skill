import SwiftUI
import UIKit

// NSLog rather than print, so the numbers carry timestamps and survive a plain `simctl launch`, which
// returns straight away. `print` reaches the console too, for as long as `--console-pty` stays attached.
// Two readers, one inset 50 pt inside the other, so a proxy-local coordinate space can be told from a
// display one. `pass` counts body evaluations across both readers — they alternate — and the reserved
// regions are empty for the first few, so a probe that samples only `onAppear` reports `occlusions=[]`
// and misses them entirely. The hinge is logged separately, on every `onHingeChange` call, with the old
// context next to the new one, so the first call shows what the action receives before any change.

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
            .onHingeChange { old, new in
                NSLog("DUOHINGE old=%@ new=%@", describe(old.hinge), describe(new.hinge))
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
    out += " divisions=\(div.map(describe))"
    out += " occlusions=\(occ.map(describe))"
    if let s = UIApplication.shared.connectedScenes.first as? UIWindowScene {
        out += " scale=\(s.screen.traitCollection.displayScale) screenBounds=\(s.screen.bounds)"
        out += " verticalBarEdge=\(s.keyWindow?.traitCollection.verticalBarEdge.rawValue ?? -1)"
        out += " hSize=\(s.keyWindow?.traitCollection.horizontalSizeClass.rawValue ?? -1)"
        out += " vSize=\(s.keyWindow?.traitCollection.verticalSizeClass.rawValue ?? -1)"
    }
    NSLog("%@", out)
    return Pass.n
}

func describe(_ r: ReservedRegion) -> String {
    let m = r.margins
    return "\(r.frame)|margins(t:\(m.top) l:\(m.leading) b:\(m.bottom) tr:\(m.trailing))|active=\(r.isActive)"
}

func describe(_ hinge: DeviceHinge?) -> String {
    guard let hinge else { return "nil" }
    let status = switch hinge.status {
    case .closed: "closed"
    case .partiallyOpen: "partiallyOpen"
    case .fullyOpen: "fullyOpen"
    default: "unknown"                     // DeviceHinge.Status is a struct, not an enum
    }
    return "\(status)@\(hinge.angle.degrees)deg"
}
