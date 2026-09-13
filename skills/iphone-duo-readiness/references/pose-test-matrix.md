# Pose test matrix

iPhone Duo is several devices in one. Test the states people actually use, not
just "it launches". Sources: Tech Talk 111461 1:17 and 6:06, 111462 0:28 and 11:40,
111463 1:29–5:12, 111464 2:59–5:00, 111466 5:07–9:28, WWDC26 278 8:19, and HIG
*Designing for iPhone Duo*. Which way each pose faces, and where the cameras and fold
sit: `device-geometry.md`.

## Tooling

- **Device Hub** (Xcode 27.1): the iPhone Duo simulator has on-screen controls to
  open, close, rotate and fold. Check for it with
  `xcrun simctl list devicetypes | grep -i duo`; if nothing matches, the installed
  Xcode cannot simulate iPhone Duo — say so in the report instead of claiming the
  pose was tested.
- **Resize mode** in Device Hub and Xcode Previews (Xcode 27): drag the device edges
  to test continuous sizes.
- **Real devices** remain the check for iPhone Mirroring on the Mac and iPhone apps
  on iPad.

## Matrix

| # | State | What to look for |
| --- | --- | --- |
| P1 | Closed, outer display, portrait | Compact width like other iPhones, but toolbar, tab bar and navigation controls sit on the side below the corner camera; content is offset by the safe area, not hidden behind them; sheets can present with vertical controls. |
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

## Reporting

For each pose, record *passed*, *failed* (with a screenshot path and the item ID it
maps to) or *not run* (with the reason — e.g. "no iPhone Duo device type in Xcode
27.0"). Never collapse *not run* into *passed*.
