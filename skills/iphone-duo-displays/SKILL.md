---
name: iphone-duo-displays
description: >-
  Use iPhone Duo's hinge, two displays, two front cameras and multiple windows in
  SwiftUI and UIKit apps. Use when a developer asks about the hinge angle or fold
  state, onHingeChange or UIHingeInteraction, interactions driven by folding, Split
  View multitasking or the stacked video layout on iPhone Duo, multiple scenes or
  windows on iPhone, requestSceneSessionActivation errors on the outer display,
  UIWindowSceneActivationAction, scene accessories, sceneAccessory,
  CameraCaptureAccessory, a teleprompter or subject preview on the outer display,
  the virtual front camera, AVCaptureDeviceDirectionCoordinator and cameras that
  change direction when the device opens or closes, preview mirroring, or a widget
  so the app appears in StandBy on the outer display. Based on Apple's "Leverage
  multiple displays and scenes" and "Build a great camera experience for iPhone
  Duo". Not for column widths, safe areas or content around the fold (layout) or
  toolbar items (bars).
---

# iPhone Duo displays, hinge, scenes and cameras

Code: `references/displays-code.md`. Availability: `references/api-availability.md` —
the hinge APIs, `CameraCaptureAccessory`, the direction coordinator and the physical
front camera types need the **iOS 27.1 SDK**; `sceneAccessory`, `onAvailabilityChange`,
`UISceneAccessory` and `UIWindowScene.ActivationAction` exist earlier. Which half
carries the outer display and the inner camera, how each pose faces, and what each
camera can do: `references/device-geometry.md`.

## Hinge (Tech Talk 111464, 0:49–2:35)

- SwiftUI `onHingeChange { previous, context in … }`; UIKit
  `UIHingeInteraction { _, update in … }` added to a view with `addInteraction`.
- Reports a status — closed, partially open, fully open (UIKit also `unknown`) — and
  a continuous angle (`UIHinge.angle` is in radians; the SwiftUI sample uses `Angle`).
- `context.hinge == nil` (UIKit: `update.hinge == nil`) means the device has no hinge
  or the view left a hierarchy that provides hinge updates: every hinge feature must
  degrade to nothing on other devices. `UIHingeInteraction.isEnabled` pauses updates.
- Filter for `.partiallyOpen` when reading the angle, and **reset in the else branch**
  so the effect does not stick when the device opens flat or closes.
- **Hinge data drives interactions and effects, not layout.** Layout uses arrangements
  and reserved regions (`iphone-duo-layout`).
- Good fits: instruments, games, camera and media controls, playful physical
  interactions. Poor fits: anything essential — it must be reachable without folding.

## Split View multitasking (2:59)

- **All apps participate**: two apps side by side on iPhone Duo, plus a new layout
  that stacks video and apps. There is no opt-out to lean on.
- Apps that already resize on iPad or in iPhone Mirroring start in good shape. Handle
  it with size classes and scene geometry, and the asymmetric safe areas it produces.
- Verify: pose P8 in `references/pose-test-matrix.md`.

## Multiple scenes (3:38)

- iPhone Duo is the first iPhone that shows multiple instances of an app's UI; apps
  that support multiple scenes on iPad get this too.
- **New windows cannot be created on the outer display.** Every scene request must
  handle failure (scanner rule `DUO010` flags `errorHandler: nil`).
- Prefer `UIWindowSceneActivationAction` (Swift: `UIWindowScene.ActivationAction`) for
  "Open in New Window" controls: it hides itself when new windows are not available.
- Apps that enable `UIApplicationSupportsMultipleScenes` must not rely on global
  window state (`iphone-duo-adaptivity-audit`, rule `DUO009`).
- An iPhone app that set the key to `false` to avoid coordinating state across
  windows now leaves Split View pairs and "open in new window" on the table. Treat it
  as a Tier 3 item: enable it only if the app tolerates several windows, test two
  windows on an iPad first, then on iPhone Duo. The scanner reports the key's value
  under `project.supports_multiple_scenes`.

## Scene accessories (4:22–6:25)

- Show content on more than one display at once, paired with the main UI — like a
  phone acting as a controller for a game on an external display.
- **The system controls availability** and it can change at any time; accessories are
  enabled by default and can be toggled. Observe availability and update any control
  that turns the accessory on.
- **Camera capture accessory** (camera apps): extra UI on the outer display while the
  main UI stays on the inner display — show the subject a preview, a countdown, a
  teleprompter. Available only when the app is **full screen on the inner display with
  an active camera session**. Register it on the **same view as the camera UI**, so it
  appears only while that view is visible.
- Pattern: `.sceneAccessory { CameraCaptureAccessory(isEnabled: $model.isEnabled) { … }
  .onAvailabilityChange { model.isAvailable = $0 } }` and a toolbar toggle disabled when
  unavailable (for example when the device is closed).
- UIKit: `UISceneAccessory.cameraCapture(sceneConfiguration:userInfo:)` passed to
  `registerSceneAccessory(_:)` on the capture view controller; keep the returned
  `UISceneAccessoryRegistration` (`isAvailable` is observable — read it in
  `updateProperties()`; set `isEnabled` from the toggle) and call
  `unregisterSceneAccessory(_:)` when the app stops offering the content. The
  accessory scene's session role is `windowCameraCaptureAccessory`; the shared model
  arrives as `connectionOptions.sceneAccessoryUserInfo`. No scene-manifest entry is
  needed or honored. (Apple documentation › Registering a camera capture accessory)
- The system presents the top-most registration of a kind, withdraws content when
  capture stops, the app leaves the foreground or the device closes, and lets
  different accessory kinds coexist (a connected external display and the outer
  display at once). Share one model between the capture UI and the accessory instead
  of passing messages; the outer display accepts touch, so a single control (pause
  the script, tap to focus) is fine, a second interface is not.
- Simulator has no camera: previews and Simulator check the accessory's layout,
  only a device shows it.

### Before proposing a camera accessory

An accessory is only available with an active camera session, so check the session
really runs: a camera usage description (`NSCameraUsageDescription`), an authorization
request, inputs added without swallowed errors, and outputs for what the app records.
Missing prerequisites come first in the plan — otherwise the accessory silently never
appears and looks like an iPhone Duo bug. Recording itself must never wait on the
accessory being available.

## Cameras (Tech Talk 111465; Apple documentation › Choosing a camera by the direction it faces)

iPhone Duo has two front cameras, both square ultrawide sensors: the outer camera and
the under-display inner camera. Which way a camera faces depends on the display the
app is on, and opening or closing the device moves the app to the other display.

- **Existing front-camera code keeps working.** A `DiscoverySession` with position
  `.front` and the wide or ultra wide type returns the **Virtual Front Camera**, one
  `AVCaptureDevice` that streams from the inner camera when open and the outer camera
  when closed (`isVirtualDevice == true`; `activePrimaryConstituent` names the
  streaming camera). It offers only what both cameras share — 1080p, 60 fps, no
  depth. (1:01, 2:28)
- **Capture-first apps use the physical cameras.** `builtInOuterUltraWideCamera`
  (up to 4K at 120 fps) and `builtInInnerUltraWideCamera` (1080p up to 60 fps) expose
  each camera fully, and switching on open/close becomes the app's job. (1:53)
- **`position` is where a camera sits, not where it points.** Both front cameras
  report `.front`; a front camera can face away from the person looking at the app,
  and the rear cameras face the person when the open device is turned around.
  Create an `AVCaptureDeviceDirectionCoordinator(view:deviceTypes:)` on the preview
  view, listing every built-in camera the app captures from — rear types included,
  the two physical front types instead of the virtual one — and keep it alive while
  the view is on screen. Its handler reports an `AVCaptureDeviceDirectionMap`; pick
  from `forwardFacingDeviceDescriptors` when the active camera is no longer in it.
  (2:53–4:49)
- **The handler runs on the main actor and never touches AVFoundation.** It hands an
  `AVCaptureDeviceDescriptor` (Sendable) to the actor that owns the session, which
  resolves it with `AVCaptureDevice(uniqueID:)`, handles a `nil` result, and swaps
  the single video input inside `beginConfiguration` / `commitConfiguration`. Two
  displays showing a preview (a capture accessory) mean two coordinators, one per
  view. (5:37–6:16)
- **Mirror by direction, not position.** A forward-facing rear camera is a selfie
  camera and needs a mirrored preview; a backward-facing front camera does not. Set
  `automaticallyAdjustsVideoMirroring = false` before assigning `isVideoMirrored`
  (assigning while it adjusts raises), only when position and direction disagree, and
  reapply after reconnecting an input. Mask the preview while the new camera starts.
- **Rotation.** Adopt `AVCaptureDevice.RotationCoordinator`; it updates when the app
  moves displays, and it is created per device, so make a new one on every camera
  switch. Then disable camera-sensor-orientation compensation, which is on for every
  front camera on iPhone Duo, to save work. (8:08)
- **Preview polish.** A full-field-of-view rear preview on the inner display leaves
  room around it: offset the preview and put controls in the remaining space, or
  fill with `videoGravity`. `dynamicAspectRatio` lets the square front sensors deliver
  a landscape frame on the inner display. (7:03)
- Verify on a device — Simulator has no camera (pose P13).

## StandBy on the outer display (Apple newsroom; HIG › Live Activities)

StandBy runs on either display "even when it's not charging": a folded or tented
iPhone Duo on a desk is a screen facing the room, filled with widgets and Live
Activities. An app with neither is absent from it. For apps that have a natural
glanceable state (next event, timer, score, order status), a widget or Live Activity
is a Tier 3 item; the scan inventory reports `WidgetKit` and `Live Activities`
adoption. The Dynamic Island on the side stack expands vertically for Live Activities
(HIG › Reserved regions), so nothing extra is needed there.

## Workflow

1. From the scan inventory: `AVCaptureSession` → camera accessory candidate, and
   with `front camera discovery` or `video mirroring` → camera direction review;
   `multiple scene requests` or `UIApplicationSupportsMultipleScenes` → scene
   handling review; custom gesture or sensor-driven features → hinge candidates;
   no `WidgetKit` / `Live Activities` → StandBy presence item.
2. Correctness first: scene request errors, Split View sizes, cameras that face the
   wrong way after opening or closing. Then opportunities: accessory, hinge, widget.
3. Recommend with `references/recommendation-format.md`; mark 27.1 APIs *blocked* when
   the SDK lacks them; apply after approval; build.
4. Verify poses P7, P8, P9, P10 and P13 in `references/pose-test-matrix.md`.

## Guardrails

- Never gate core functionality on the hinge or an accessory.
- Don't read hinge state once and cache it; it is live.
- Don't present a new-window affordance you have not checked is available.
- Don't infer which way a camera faces from its type or `position`; ask a direction
  coordinator, and write one code path that also runs on single-display iPhones
  (there the coordinator reports once and never changes).
