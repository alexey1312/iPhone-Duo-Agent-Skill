import SwiftUI
import Testing
@testable import FoldKit

@Test func modifierBuilds() {
    _ = Text("x").foldMeter(isHalfOpen: .constant(false))
}
