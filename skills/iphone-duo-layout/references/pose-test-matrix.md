# Pose test matrix

iPhone Duo is several devices in one. Test the states people actually use, not
just "it launches". Sources: Tech Talk 111461 1:17, 6:06 and 7:44, 111462 0:28 and
11:40, 111463 1:29–5:12, 111464 2:59–5:00, 111465 2:53–8:08, 111466 5:07–9:28, WWDC26
278 8:19, and HIG *Designing for iPhone Duo*. Which way each pose faces, and where the
cameras and fold sit: `device-geometry.md`.

## Tooling

- **iPhone Duo simulator** (Xcode 27.1): it exists. Confirm, then boot it:

  ```bash
  xcrun simctl list devicetypes | grep -i duo
  # iPhone Duo (com.apple.CoreSimulator.SimDeviceType.iPhone-Duo)
  xcrun simctl boot "iPhone Duo" && open -a Simulator
  xcrun simctl io booted enumerate    # both integrated framebuffers, 1398x2034 and 2007x2853
  ```

  It requires the **iOS 27.1 runtime** (`minRuntimeVersion 27.1`); a 27.0 runtime will
  not pair with it. If `simctl list devicetypes` matches nothing, the installed Xcode
  cannot simulate iPhone Duo — say so in the report instead of claiming the pose was
  tested.
- **Poses are Device Hub's on-screen controls, not a command.** `simctl` has no fold,
  pose or hinge subcommand, and an app launched with `simctl launch` comes up on the
  **outer** display. Opening, folding and rotating are done by hand in Device Hub, so
  every pose below P1–P2 is a manual step. Automate the launch, not the pose.
- **First launch can take several minutes** (Xcode 27.1 known issue 187708500). Wait
  it out; a slow first boot is not a broken runtime.
- **What the simulator cannot do** — report these as *not run* with the radar number,
  never as *passed*:
  - **StandBy is unavailable** in the iPhone Duo runtime (187708663), so the StandBy
    check cannot be satisfied there.
  - **Most app extensions cannot be run or debugged** in it (187708767) — widgets and
    Live Activities included, which is exactly how the StandBy check would otherwise
    be met. Verify the widget on another simulator or a device.
  - **No camera**, unchanged: anything camera-dependent is device-only.
- **Mac Catalyst**: if the app ships a Catalyst target, check it still builds after
  adopting any 27.1 API. iOS 27.1 APIs do not compile for Catalyst (185924957,
  workaround `#if !targetEnvironment(macCatalyst)`), and a target on iOS 27.1 loses
  its Catalyst run destination (187046347, workaround: a Mac Catalyst 27.0 minimum
  deployment). This breaks a shipping Mac build, so treat it as Tier 1.
- **Previews**: Xcode 27.1 adds a **Display** group to the canvas overrides picker
  (182598534), so a preview can render on a device's alternative display without
  booting a second scene.
- **Resize mode** in Device Hub and Xcode Previews: the fallback for anyone still on
  Xcode 27.0. The target shapes are no longer derived — they are what the simulator
  reports: **669 × 951** and **951 × 669** pt for the inner display, **466 × 678** and
  **678 × 466** pt for the outer display, plus half the inner width (≈ 475 × 669) for
  Split View (`device-geometry.md`).
- **Split View in Device Hub** (Tech Talk 111461, 7:50): preview on the inner
  display, drag the app by the home indicator to one side of the screen until a drop
  area appears, then to the other side — vertical bars can end up on either side.
- **Real devices** remain the check for iPhone Mirroring on the Mac and iPhone apps
  on iPad, and the only check for anything that depends on a camera: Simulator has
  none.

## Matrix

| # | State | What to look for |
| --- | --- | --- |
| P1 | Closed, outer display, portrait | Compact width × regular height, but toolbar, tab bar and navigation controls sit on the side below the corner camera; content is offset by the safe area, not hidden behind them; sheets can present with vertical controls. Read from a booted simulator with no app bars (`device-geometry.md`, *Booted*): 466 × 678 pt, safe-area insets top 0 / leading 0 / bottom 34 / trailing 84, `verticalBarEdge == .trailing` — so a layout that halves a horizontal inset loses 84 pt of width. |
| P2 | Closed, outer display, landscape | Toolbar and tab bar overflow sooner; the right items stay visible; keyboard up makes it worse. |
| P3 | Open flat, inner display, landscape | Regular × regular; vertical bars on the side; sidebar if opted in; content uses the width (no centered phone column); no layout keyed off orientation. |
| P4 | Open flat, inner display, portrait | Bars horizontal — the one state where the system keeps horizontal bars (HIG); layout still uses size classes. |
| P5 | Partially folded, book pose | Nothing important spans the fold; alerts, menus, popovers and sheets sit clear of it; split views split evenly; custom controls displaced with small adjustments, not rearranged. |
| P6 | Partially folded, tabletop pose | Viewing content on top, interactive controls on the bottom where it applies. |
| P7 | Transitions: close ↔ open, fold ↔ flat | State survives; no jump to root; no stale geometry cached from the previous display; hinge-driven effects reset when not partially open; games stay playable and fill each new shape (change the aspect ratio rather than letterbox). |
| P8 | Split View multitasking on the inner display | Asymmetric safe areas handled; narrow widths collapse cleanly; the stacked video-plus-apps layout. |
| P9 | Multiple windows (if the app supports scenes) | New window requests from the outer display fail gracefully; activation action hidden when unavailable. |
| P10 | Camera app with a capture accessory | Accessory appears on the outer display only while full screen on the inner display with an active session; toggle disabled when unavailable. |
| P11 | Right-to-left language on the inner display | Vertical bar stays on the same hardware side; content mirrors as usual. |
| P12 | Reduce Transparency on | Vertical bars gain a background; custom bar views remain legible. |
| P13 | Camera direction changes (camera apps, device only) | Open and close while capturing: the preview keeps streaming from a forward-facing camera; the rear camera works as a selfie camera when the open device is turned around; mirroring follows the direction the camera faces, not its position; the preview and captured media stay upright after every switch (a new rotation coordinator per device); the virtual front camera falls back cleanly to the common feature set. |
| P14 | StandBy on the outer display | A widget or Live Activity appears when the device is folded or tented. **Not verifiable in the iPhone Duo simulator** (187708663, 187708767): check the widget renders on another simulator, verify StandBy on a device, and report this pose as *not run*. |
| P15 | Mac Catalyst build (only if the app ships one) | The Catalyst target still builds after adopting 27.1 APIs (185924957, 187046347). |

## Reporting

For each pose, record *passed*, *failed* (with a screenshot path and the item ID it
maps to) or *not run* (with the reason — e.g. "StandBy unavailable in the iPhone Duo
simulator runtime, Xcode 27.1 known issue 187708663", or "no iPhone Duo device type,
Xcode 27.0 installed"). Never collapse *not run* into *passed*.
