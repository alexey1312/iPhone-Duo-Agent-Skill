---
name: iphone-duo-displays
description: >-
  Use iPhone Duo's hinge, multiple displays and multiple windows in SwiftUI and
  UIKit apps. Use when a developer asks about the hinge angle or fold state,
  onHingeChange or UIHingeInteraction, interactions driven by folding, Split View
  multitasking or the stacked video layout on iPhone Duo, supporting multiple
  scenes or windows on iPhone, requestSceneSessionActivation errors on the outer
  display, UIWindowSceneActivationAction, scene accessories, sceneAccessory,
  CameraCaptureAccessory, showing content on the outer display while the camera UI
  runs inside, or a teleprompter or subject preview for a camera app. Based on
  Apple's "Leverage multiple displays and scenes on iPhone Duo". Not for column
  widths, safe areas or content around the fold (layout) or toolbar items (bars).
---

# iPhone Duo displays, hinge and scenes

Code: `references/displays-code.md`. Availability: `references/api-availability.md` —
the hinge APIs and `CameraCaptureAccessory` need the **iOS 27.1 SDK**; `sceneAccessory`,
`onAvailabilityChange` and `UIWindowScene.ActivationAction` exist earlier. Which half
carries the outer display and the inner camera, and how each pose faces:
`references/device-geometry.md`.

## Hinge (Tech Talk 111464, 0:49–2:35)

- SwiftUI `onHingeChange { previous, context in … }`; UIKit `UIHingeInteraction`.
- Reports a status — closed, partially open, fully open — and a continuous angle.
- `context.hinge == nil` means the device has no hinge: every hinge feature must
  degrade to nothing on other devices.
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

### Before proposing a camera accessory

An accessory is only available with an active camera session, so check the session
really runs: a camera usage description (`NSCameraUsageDescription`), an authorization
request, inputs added without swallowed errors, and outputs for what the app records.
Missing prerequisites come first in the plan — otherwise the accessory silently never
appears and looks like an iPhone Duo bug. Recording itself must never wait on the
accessory being available.

## Workflow

1. From the scan inventory: `AVCaptureSession` → camera accessory candidate;
   `multiple scene requests` or `UIApplicationSupportsMultipleScenes` → scene
   handling review; custom gesture or sensor-driven features → hinge candidates.
2. Correctness first: scene request errors, Split View sizes. Then opportunities:
   accessory, hinge.
3. Recommend with `references/recommendation-format.md`; mark 27.1 APIs *blocked* when
   the SDK lacks them; apply after approval; build.
4. Verify poses P7, P8, P9, P10 in `references/pose-test-matrix.md`.

## Guardrails

- Never gate core functionality on the hinge or an accessory.
- Don't read hinge state once and cache it; it is live.
- Don't present a new-window affordance you have not checked is available.
