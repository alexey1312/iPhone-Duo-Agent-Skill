import SwiftUI

/// Reports the hinge posture to a binding, on devices that have one.
public struct FoldMeter: ViewModifier {
    @Binding var isHalfOpen: Bool

    public init(isHalfOpen: Binding<Bool>) {
        _isHalfOpen = isHalfOpen
    }

    public func body(content: Content) -> some View {
        if #available(iOS 27.1, *) {
            content.onHingeChange { _, context in
                isHalfOpen = context.hinge?.status == .partiallyOpen
            }
        } else {
            content
        }
    }
}

public extension View {
    func foldMeter(isHalfOpen: Binding<Bool>) -> some View {
        modifier(FoldMeter(isHalfOpen: isHalfOpen))
    }
}
