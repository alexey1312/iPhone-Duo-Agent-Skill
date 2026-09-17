# Displays, hinge, scenes and cameras — code

Samples as published on the session page of Tech Talk 111464 and in Apple's
documentation (each section says which). APIs marked **27.1** were absent from the
iOS 27.0 SDK; confirm with `scripts/sdk_api_check.py`.

## Hinge-driven effect — 27.1 (1:33–2:17)

```swift
struct InstrumentView: View {
    /// Normalized bend, 0 is no bend, 1 is deepest bend
    @State private var pitchBend: Double = 0

    var body: some View {
        GuitarView(pitchBend: pitchBend)
            .onHingeChange { _, context in
                // A nil hinge means the device doesn't have one
                if let hinge = context.hinge, hinge.status == .partiallyOpen {
                    pitchBend = calculatePitchBend(angle: hinge.angle)
                } else {
                    pitchBend = 0
                }
            }
    }

    private func calculatePitchBend(angle: Angle) -> Double { /* ... */ }
}
```

UIKit — reproduced from the `UIHingeInteraction` documentation (27.1). The angle is in
radians; a `nil` hinge means the view left a hierarchy that provides hinge updates
(or the device has none):

```swift
override func viewDidLoad() {
    super.viewDidLoad()

    let interaction = UIHingeInteraction { [weak self] _, update in
        guard let self else { return }
        guard let hinge = update.hinge else {
            resetPitchBend()
            return
        }
        switch hinge.status {                       // .closed, .partiallyOpen, .fullyOpen, .unknown
        case .partiallyOpen: applyPitchBend(radians: hinge.angle)
        default: resetPitchBend()
        }
    }
    view.addInteraction(interaction)
}
```

## Scene requests that can fail (3:38)

```swift
// ✗ silently fails on the outer display
UIApplication.shared.requestSceneSessionActivation(nil, userActivity: activity,
                                                   options: nil, errorHandler: nil)

// ✓ handle the failure
let request = UISceneSessionActivationRequest(role: .windowApplication, userActivity: activity)
UIApplication.shared.activateSceneSession(for: request) { error in
    // Tell the user, or fall back to opening the content in the current window.
}

// ✓ or let the action hide itself when new windows aren't available.
// Objective-C name: UIWindowSceneActivationAction; in Swift it is nested.
let newWindow = UIWindowScene.ActivationAction { _ in
    UIWindowScene.ActivationConfiguration(userActivity: activity)
}
```

## Camera capture accessory — 27.1 (5:43–6:25)

```swift
struct CameraRootView: View {
    @State private var model = TeleprompterModel()

    var body: some View {
        CameraView(model: model)
            .sceneAccessory {
                CameraCaptureAccessory(isEnabled: $model.isEnabled) {
                    TeleprompterView(model: model)
                }
                .onAvailabilityChange { newValue in
                    model.isAvailable = newValue
                }
            }
            .toolbar {
                TeleprompterToggle(isEnabled: $model.isEnabled)
                    .disabled(!model.isAvailable)
            }
    }
}
```

Requirements to state in the recommendation: the app is full screen on the inner
display, a camera session is active, and the accessory is registered on the camera
view itself.

UIKit — reproduced from *Registering a camera capture accessory on iPhone Duo*
(27.1). Register on the capture view controller, keep the registration, and read its
observable `isAvailable` where the UI updates:

```swift
class CameraViewController: UIViewController {
    private let script = ScriptModel()
    private var registration: UISceneAccessoryRegistration?

    override func viewDidLoad() {
        super.viewDidLoad()
        let configuration = UISceneConfiguration()
        configuration.delegateClass = ScriptSceneDelegate.self
        let accessory = UISceneAccessory.cameraCapture(sceneConfiguration: configuration,
                                                       userInfo: script)
        registration = registerSceneAccessory(accessory)
    }

    override func updateProperties() {
        super.updateProperties()
        scriptControls.isHidden = !(registration?.isAvailable ?? false)
    }

    @objc private func toggleScript(_ sender: UISwitch) {
        registration?.isEnabled = sender.isOn      // turning it off is not unregistering
    }
}

class ScriptSceneDelegate: NSObject, UIWindowSceneDelegate {
    var window: UIWindow?

    func scene(_ scene: UIScene, willConnectTo session: UISceneSession,
               options connectionOptions: UIScene.ConnectionOptions) {
        guard let windowScene = scene as? UIWindowScene,
              let script = connectionOptions.sceneAccessoryUserInfo as? ScriptModel else { return }
        let window = UIWindow(windowScene: windowScene)
        window.rootViewController = ScriptViewController(model: script)
        window.makeKeyAndVisible()
        self.window = window
    }
}
```

No scene-manifest entry applies to accessory scenes; if one delegate serves several
scene kinds, compare `session.role` with `.windowCameraCaptureAccessory`.

## Cameras that change direction — 27.1 (Tech Talk 111465; *Choosing a camera by the direction it faces*)

Reproduced from Apple's AVKit article. The virtual front camera needs no new code:

```swift
final class DeviceLookup {
    // On iPhone Duo these device types return the Virtual Front Camera.
    private let frontCameraDiscoverySession = AVCaptureDevice.DiscoverySession(
        deviceTypes: [.builtInWideAngleCamera, .builtInUltraWideCamera],
        mediaType: .video,
        position: .front
    )

    var frontCamera: AVCaptureDevice? { frontCameraDiscoverySession.devices.first }

    // The physical camera a virtual device streams from; nil until the session runs.
    func streamingCamera(for camera: AVCaptureDevice) -> AVCaptureDevice? {
        camera.isVirtualDevice ? camera.activePrimaryConstituent : camera
    }
}
```

Apps that capture from the physical cameras follow the direction they face. The
coordinator lives on the main actor with the preview view; list every built-in camera
the app uses, rear cameras included, and the two physical front types instead of the
virtual one:

```swift
import AVKit

@MainActor
final class DirectionObserver {
    private let captureService: CaptureService          // an actor that owns the session
    private var coordinator: AVCaptureDeviceDirectionCoordinator?
    private var activeCameraDescriptor: AVCaptureDeviceDescriptor?

    init(captureService: CaptureService) { self.captureService = captureService }

    func startObserving(previewView: UIView) {
        coordinator = AVCaptureDeviceDirectionCoordinator(
            view: previewView,
            deviceTypes: [.builtInOuterUltraWideCamera, .builtInInnerUltraWideCamera, .builtInDualWideCamera]
        ) { [weak self] deviceDirections in
            self?.cameraDirectionsDidChange(deviceDirections)
        }
    }

    // Called on the main actor, once right away and again on every change.
    func cameraDirectionsDidChange(_ deviceDirections: AVCaptureDeviceDirectionMap) {
        let forwardFacing = deviceDirections.forwardFacingDeviceDescriptors
        if let activeCameraDescriptor, forwardFacing.contains(activeCameraDescriptor) { return }
        guard let replacement = forwardFacing.first else { return }   // nothing faces forward
        activeCameraDescriptor = replacement
        Task { try await captureService.selectCamera(with: replacement) }
    }
}
```

Apple's sample records `replacement` before the actor confirms the swap. If
`selectCamera` can fail in your app (a `nil` device, `canAddInput` false, a thrown
error), have it return the descriptor it actually installed and assign
`activeCameraDescriptor` from that result; otherwise a failed switch looks done and is
never retried while the direction map stays the same.

Resolve the descriptor where the session lives, and handle a `nil` device — the set
of cameras can change while dispatching:

```swift
actor CaptureService {
    private let captureSession = AVCaptureSession()
    private var activeVideoInput: AVCaptureDeviceInput?

    func selectCamera(with descriptor: AVCaptureDeviceDescriptor) throws {
        guard let device = AVCaptureDevice(uniqueID: descriptor.uniqueID) else { return }
        let newInput = try AVCaptureDeviceInput(device: device)

        captureSession.beginConfiguration()
        defer { captureSession.commitConfiguration() }
        if let activeVideoInput { captureSession.removeInput(activeVideoInput) }
        guard captureSession.canAddInput(newInput) else {
            if let activeVideoInput { captureSession.addInput(activeVideoInput) }
            return
        }
        captureSession.addInput(newInput)
        activeVideoInput = newInput
        // Also create a new AVCaptureDevice.RotationCoordinator for `device` here.
    }
}
```

Mirroring follows the direction map, not `position`; call this after every map and
after every reconnected input:

```swift
private func applyVideoMirroring(from directionMap: AVCaptureDeviceDirectionMap) {
    guard let connection = previewConnection, connection.isVideoMirroringSupported else { return }
    let uniqueID = activeDevice.uniqueID
    let isFacingForward = directionMap.forwardFacingDeviceDescriptors.contains { $0.uniqueID == uniqueID }
    let isFacingBackward = directionMap.backwardFacingDeviceDescriptors.contains { $0.uniqueID == uniqueID }
    let isFrontCamera = activeDevice.position == .front

    // Take over only when position and direction disagree.
    guard (isFacingForward && !isFrontCamera) || (isFacingBackward && isFrontCamera) else { return }
    connection.automaticallyAdjustsVideoMirroring = false     // assigning while it adjusts raises
    connection.isVideoMirrored = isFacingForward
}
```

The early return assumes the input is replaced whenever a camera turns away, which
gives a fresh connection with automatic mirroring on. An app that keeps streaming
from a camera the coordinator no longer lists as forward-facing must also restore
`automaticallyAdjustsVideoMirroring = true` in the "agree" case, or the override from
the previous pose sticks to the connection.

State in the recommendation: the coordinator, `AVCaptureDeviceDescriptor` and the
physical front camera types are 27.1 SDK; camera behavior is verified on a device
only (pose P13).
