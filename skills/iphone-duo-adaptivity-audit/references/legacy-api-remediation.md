# Legacy API remediation

Before/after pairs for the rules this skill owns. UIKit samples follow WWDC26 278;
SwiftUI equivalents are standard SwiftUI APIs. Check anything newer than iOS 26 with
`scripts/sdk_api_check.py`.

## DUO001 — Main screen scale

```swift
// Before
func updateThumbnail(from image: UIImage) {
    let screenScale = UIScreen.main.scale
    // ...
}

// After — UIView / UIViewController (Tech Talk 111461, 9:25)
func updateThumbnail(from image: UIImage) {
    let screenScale = traitCollection.displayScale
    // ...
}
```

Inside `layoutSubviews`, `draw(_:)`, `updateProperties` and other tracked methods,
UIKit calls the method again when `displayScale` changes — no observation needed
(278, 3:49). Elsewhere, observe explicitly:

```swift
registerForTraitChanges([UITraitDisplayScale.self]) { (view: GalleryView, _) in
    view.cache.invalidate()
}
```

SwiftUI:

```swift
@Environment(\.displayScale) private var displayScale
```

## DUO001 — Main screen as a screen

```swift
// Access the correct screen through the window scene
let screen = window?.windowScene?.screen

// No view at hand: pass the screen in (278, 3:24)
func generateThumbnail(_ image: UIImage, screen: UIScreen) -> UIImage { /* ... */ }
```

When a public API loses its implicit screen, keep the old signature as a deprecated
forwarder so callers get a migration path instead of a break.

## DUO002 — Screen bounds as available space

```swift
// Before
let width = UIScreen.main.bounds.width

// After — the view's own space (278, 5:35)
override func viewDidLayoutSubviews() {
    super.viewDidLayoutSubviews()
    let availableSpace = view.bounds.size
    // ...
}

// After — scene-level space (278, 5:19)
func windowScene(_ windowScene: UIWindowScene,
                 didUpdateEffectiveGeometry previousEffectiveGeometry: UIWindowScene.Geometry) {
    let availableSpace = windowScene.effectiveGeometry.coordinateSpace.bounds
    // ...
}
```

SwiftUI:

```swift
// Before
.frame(width: UIScreen.main.bounds.width * 0.8)

// After
.containerRelativeFrame(.horizontal) { length, _ in length * 0.8 }

// Or, when the value feeds logic
.onGeometryChange(for: CGFloat.self) { $0.size.width } action: { width = $0 }
```

## DUO003 — Idiom

```swift
// Before
if traitCollection.userInterfaceIdiom == .pad { showSidebar() }

// After — room, not device (111461, 2:46)
if traitCollection.horizontalSizeClass == .regular { showSidebar() }
```

```swift
// SwiftUI
@Environment(\.horizontalSizeClass) private var horizontalSizeClass
var body: some View {
    if horizontalSizeClass == .regular { TwoColumnLayout() } else { StackedLayout() }
}
```

Better still, let a container adapt (`NavigationSplitView`, `TabView` with
`.sidebarAdaptable`, `ViewThatFits`) and delete the branch.

## DUO004 — Orientation

```swift
// Before
if UIDevice.current.orientation.isLandscape { layoutSideBySide() }

// After
if view.bounds.width > view.bounds.height { layoutSideBySide() }
// or, for "is there room for two columns":
if traitCollection.horizontalSizeClass == .regular { layoutSideBySide() }
```

Orientation that is genuinely needed (not layout):

```swift
// Scene interfaceOrientation is deprecated in the iOS 27 SDK
let orientation = view.window?.windowScene?.effectiveGeometry.interfaceOrientation
```

Sensor data in the view's coordinate space (278, 8:12):

```swift
override func viewDidLoad() {
    super.viewDidLoad()
    motionManager.deviceMotionBody = view
    locationManager.headingBody = view
}
```

## DUO005 — Scene lifecycle

Minimum shape for a UIKit app:

```xml
<key>UIApplicationSceneManifest</key>
<dict>
    <key>UIApplicationSupportsMultipleScenes</key>
    <false/>
    <key>UISceneConfigurations</key>
    <dict>
        <key>UIWindowSceneSessionRoleApplication</key>
        <array>
            <dict>
                <key>UISceneConfigurationName</key>
                <string>Default Configuration</string>
                <key>UISceneDelegateClassName</key>
                <string>$(PRODUCT_MODULE_NAME).SceneDelegate</string>
            </dict>
        </array>
    </dict>
</dict>
```

```swift
final class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?

    func scene(_ scene: UIScene, willConnectTo session: UISceneSession,
               options connectionOptions: UIScene.ConnectionOptions) {
        guard let windowScene = scene as? UIWindowScene else { return }
        let window = UIWindow(windowScene: windowScene)
        window.rootViewController = RootViewController()
        window.makeKeyAndVisible()
        self.window = window
    }
}
```

Move from the app delegate: window creation, `open url` handling
(`scene(_:openURLContexts:)`), user activity continuation, foreground/background
transitions (`sceneDidBecomeActive`, `sceneWillResignActive`, …) and state restoration
(`stateRestorationActivity(for:)`). Keep launch-time, process-wide work in the app
delegate. Projects generating the Info.plist can set
`INFOPLIST_KEY_UIApplicationSceneManifest_Generation = YES` and name the delegate in
`application(_:configurationForConnecting:options:)`.

## DUO009 — Global window state

```swift
// Before
let window = UIApplication.shared.connectedScenes
    .compactMap { $0 as? UIWindowScene }.first?.windows.first

// After — the window this view lives in
let window = view.window
let scene = view.window?.windowScene
```

With several windows on iPhone Duo, "the first scene" is whichever the system lists
first. If code has no view (a service presenting UI), pass the presenting view
controller or scene in.

## DUO013 — Biometric copy and symbols

iPhone Duo has Touch ID in its side button and no Face ID (Apple tech specs), and
Tech Talk 111461 (2:34) asks apps not to assume device capabilities. `LAContext`
already reports what the device has; the words, the SF Symbol and the onboarding
text should come from it. Written against LocalAuthentication's long-standing API
(iOS 11); typecheck it in the project when you apply it.

```swift
// Before
Button("Unlock with Face ID", systemImage: "faceid") { unlock() }

// After — ask LocalAuthentication, then pick words and symbol
import LocalAuthentication

struct Biometry {
    let name: String
    let symbol: String

    /// `biometryType` is only meaningful after `canEvaluatePolicy` has run.
    static var current: Biometry? {
        let context = LAContext()
        guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: nil) else {
            return nil
        }
        switch context.biometryType {
        case .faceID: return Biometry(name: "Face ID", symbol: "faceid")
        case .touchID: return Biometry(name: "Touch ID", symbol: "touchid")
        default: return nil          // .none, and .opticID on visionOS
        }
    }
}

if let biometry = Biometry.current {
    Button("Unlock with \(biometry.name)", systemImage: biometry.symbol) { unlock() }
} else {
    Button("Unlock with passcode") { unlockWithPasscode() }
}
```

UIKit: the same `Biometry.current` feeds `UIButton.Configuration.title` and
`.image = UIImage(systemName: biometry.symbol)`; `localizedReason` for
`evaluatePolicy` and error alerts take the name the same way.

Keep `NSFaceIDUsageDescription` in Info.plist — Face ID devices still require it and
Touch ID needs no usage string. Sentences that hard-code the words ("Enable Face ID"
in onboarding, a settings toggle, an error alert) often live in `.strings` or
`.xcstrings` catalogs the scanner does not read: grep them and turn the sentence into
a format string that takes `biometry.name`. In a file that already reads
`biometryType`, `DUO013` reports the remaining strings at `low` severity: confirm each
one sits in the `.faceID` branch (*kept*) or fix it; a `medium` finding is in a file
that never asked.

## DUO020 — UIRequiresFullScreen

Non-game apps: remove the key and adapt. Games: keep it — from iOS 27 the key no
longer opts out of resizing but gives discrete resizing that respects supported
orientations, so the game renders at full quality at each size and the scene only
changes size when a drag ends (278, 5:46; TN3192). iPhone Duo still resizes the game
when the device opens or closes and scales it on the inner display, including in
Split View (111461, 4:37). It is not an exemption from iPhone Duo's inner display
layout. Games that update expensive assets per size should read
`windowScene.effectiveGeometry.isInteractivelyResizing` (SwiftUI:
`onInteractiveResizeChange`) and `UIRequiresFullScreenIgnoredStartingWithVersion`
lets an app keep the old behavior on earlier iOS while it adapts.
