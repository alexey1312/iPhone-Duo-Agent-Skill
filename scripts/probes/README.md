# Probes

Throwaway programs that produced the measured numbers in
`references/device-geometry.md` and `references/api-availability.md`.
They are here so those numbers can be re-derived rather than taken on trust.
None of them is part of the skills; nothing imports them.

## `api_shapes_probe.swift` — do the shapes the skills teach compile?

Every iOS 27.1 API these skills recommend, written the way the references write it.

```bash
xcrun --sdk iphonesimulator swiftc -typecheck \
  -target arm64-apple-ios27.1-simulator scripts/probes/api_shapes_probe.swift
```

Clean against Xcode 27.1 (27A9269) on 2026-09-19, and again on 2026-10-01 after adding
`onHingeChange(isEnabled:)` with a `switch` over `DeviceHinge.Status`,
`.overlay.axes(_:)`, the per-axis `splitArrangementLayoutRatio` and
`splitArrangementFixedLayoutSize`.

## `deployment_gate_probe.swift` — does the sub-27.1 gate compile?

The `@ToolbarContentBuilder` extension from
`skills/iphone-duo-bars/references/vertical-bars.md`, with the real
`axisBehavior` rather than a stand-in.

```bash
xcrun --sdk iphonesimulator swiftc -typecheck \
  -target arm64-apple-ios18.0-simulator scripts/probes/deployment_gate_probe.swift
```

Clean: an iOS 18 deployment target against the 27.1 SDK.

## `duo_geometry_probe.swift` — what does a booted iPhone Duo actually report?

Prints scene size, `displayScale`, `safeAreaInsets`, reserved regions with their
margins, `verticalBarEdge` and the size classes, on every layout pass, from two
readers — one inset 50 pt inside the other — and every `onHingeChange` call with the
old context next to the new one.

```bash
xcrun simctl boot "iPhone Duo"
mkdir -p /tmp/DuoProbe.app && cp scripts/probes/DuoProbe-Info.plist /tmp/DuoProbe.app/Info.plist
xcrun -sdk iphonesimulator swiftc -target arm64-apple-ios27.1-simulator \
  -parse-as-library scripts/probes/duo_geometry_probe.swift -o /tmp/DuoProbe.app/DuoProbe
xcrun simctl install booted /tmp/DuoProbe.app
xcrun simctl launch booted com.example.duoprobe
xcrun simctl spawn booted log show --last 1m --style compact \
  --predicate 'eventMessage CONTAINS "DUOPROBE"'
```

This probe uses `NSLog`, not `print`:
the numbers then carry timestamps and survive a plain `simctl launch`,
which returns as soon as the app is up.
`print` is not lost — with `--console-pty` attached it delivers every pass,
populated regions included — so the empty list the earlier run recorded
was the `onAppear` sampling alone, not a console that went away.

On the **outer display in portrait**, re-measured 2026-09-19 on Xcode 27.1 (27A9269):

```
DUOPROBE pass=1 outer    size=382.0x644.0 safeArea(t:0.0 l:0.0 b:34.0 tr:84.0)
         divisions=[] occlusions=[]
…                                          (passes 2–6: still empty)
DUOPROBE pass=7 outer    size=382.0x644.0 safeArea(t:0.0 l:0.0 b:34.0 tr:84.0)
         global=(0.0, 0.0, 382.0, 644.0) divisions=[]
         occlusions=[(399.667, 29.333, 37.0, 37.0)|active=true,
                     (382.0, 0.0, 84.0, 170.0)|active=true]
         scale=3.0 screenBounds=(0.0, 0.0, 466.0, 678.0) verticalBarEdge=2 hSize=1 vSize=2
DUOPROBE pass=8 inset+50 size=282.0x544.0 safeArea(t:0.0 l:0.0 b:0.0 tr:0.0)
         global=(50.0, 50.0, 282.0, 544.0) divisions=[]
         occlusions=[(349.667, -20.667, 37.0, 37.0)|active=true,
                     (332.0, -50.0, 84.0, 170.0)|active=true]
…                                          (passes 9–10: both stay populated)
```

The two readers alternate, so each gets every other pass —
the outer reader the odd ones, the inset reader the even.
Neither the total number of passes nor the ordering within a pair is fixed;
this run logged ten.

`verticalBarEdge=2` is `.trailing`; `hSize=1`/`vSize=2` are compact/regular.

Re-run on 2026-10-01 with margins and the hinge in the log, same build:

```
DUOPROBE pass=7 outer    … occlusions=[(399.667, 29.333, 37.0, 37.0)|margins(t:0.0 l:0.0 b:0.0 tr:0.0)|active=true,
                                       (382.0, 0.0, 84.0, 170.0)|margins(t:0.0 l:0.0 b:0.0 tr:0.0)|active=true]
DUOHINGE old=nil new=closed@0.0deg
```

Both occlusion regions have zero margins, and the hinge action runs once at launch
with no previous hinge — the initial state, before anything has changed.

Three results, two of which an earlier version of this probe got wrong:

1. **The outer display reserves two occlusion regions, not none.** The 37 × 37 camera
   hole at (399.7, 29.3) and an 84 × 170 strip at (382, 0) for the status bar and
   Dynamic Island. The earlier probe sampled `onAppear` and reported `occlusions=[]`,
   which was a timing artefact: each reader is **empty for its first three layout
   passes and populated on its fourth** — about 9 ms after its first pass,
   and in the same millisecond as its third.
   An app that wants one specific region — the lens, say — must not take `.first`;
   the order is not documented and a bar strip is on the list.
   Area separates them.
2. **SwiftUI re-lays out by itself when the regions arrive**, so nothing needs
   observing. That is what the outer reader's third pass → its fourth shows —
   5 → 7 in the log's numbering, which counts both readers.
3. **Frames are in the querying proxy's own coordinate space.** The reader inset 50 pt
   inside the first reports every frame shifted by exactly (−50, −50) — the camera hole
   at (349.7, −20.7), the strip at (332, −50). Regions outside the proxy give negative
   coordinates rather than being clipped.

### The inner display, open and folded

`simctl` has no fold or pose subcommand, so the hinge is set with the third-party
[`hinge`](https://github.com/artemnovichkov/hinge) CLI
(`pose-test-matrix.md` › Tooling) — always with `-d`, or it picks the first booted
simulator — and the app is launched after the pose is set:

```bash
hinge -d <udid> open      # or: hinge -d <udid> 90
xcrun simctl launch --console-pty <udid> com.example.duoprobe
```

2026-10-01, Xcode 27.1 (27A9269), inner display in landscape:

```
open, 180°  DUOPROBE pass=9 outer size=867.0x635.0 safeArea(t:0.0 l:0.0 b:34.0 tr:84.0)
            divisions=[(455.5, 0.0, 40.0, 669.0)|margins(t:0.0 l:20.0 b:0.0 tr:20.0)|active=false]
            occlusions=[(677.333, 21.0, 58.0, 37.0)|margins(…0…)|active=false,
                        (867.0, 0.0, 84.0, 120.0)|margins(…0…)|active=true]
            screenBounds=(0.0, 0.0, 951.0, 669.0) verticalBarEdge=2 hSize=2 vSize=2
            DUOHINGE old=nil new=fullyOpen@180.0deg
book, 90°   the same, except divisions=[…|active=true]
            DUOHINGE old=nil new=partiallyOpen@90.0deg
```

The fold's frame is 40 pt flat and folded; only `isActive` changes.
The inner camera is there while off, inactive.

To watch the hinge while the app runs, keep `--console-pty` attached and step the
angle: `for a in 175 178 179 180 150 120 60 30 20 15 10 5 2 1 0; do hinge -d <udid> $a;
sleep 1.2; done`. The run reported 170.3°, 173.1° and 174.1° — all *partially open* —
for 175°, 178° and 179°; *fully open* only at 180°; *closed* already at 19.2°; and
seven to ten calls per step whose old and new contexts were equal.
Closed at 0°, the app moved to the outer display and reported the two outer
occlusion regions again. Tabletop is not covered: rotation has no command.

## `arrangement_probe.swift` — where do an arrangement's environment values reach?

Reads `overlayArrangementZIndex` and `splitArrangementAxis` twice per view — in the
view written directly in the `primary` or `secondary` closure (`Pane`) and in a view
nested inside it (`Leaf`) — and logs each view's global frame. `-mode` picks the case.

```bash
mkdir -p /tmp/ArrProbe.app
sed -e 's/DuoProbe/ArrProbe/g' -e 's/com.example.duoprobe/com.example.arrprobe/' \
  scripts/probes/DuoProbe-Info.plist > /tmp/ArrProbe.app/Info.plist
xcrun -sdk iphonesimulator swiftc -target arm64-apple-ios27.1-simulator \
  -parse-as-library scripts/probes/arrangement_probe.swift -o /tmp/ArrProbe.app/ArrProbe
xcrun simctl install booted /tmp/ArrProbe.app
xcrun simctl launch --console-pty booted com.example.arrprobe -mode overlay
xcrun simctl io booted screenshot --display=1 /tmp/arr-overlay.png   # the outer display
```

On the **outer display in portrait**, 2026-10-01, Xcode 27.1 (27A9269),
last value of each line:

| `-mode` | Primary: pane / leaf | Secondary: pane / leaf | Frames |
| --- | --- | --- | --- |
| `overlay` | zIndex 0 / **1** | zIndex 0 / 0 | both 382 × 644, primary drawn on top |
| `overlayModified` (`.padding(0)` on the pane) | zIndex 0 / **1** | 0 / 0 | as `overlay` |
| `overlayWrapped` (pane inside a `VStack`) | zIndex **1** / **1** | 0 / 0 | as `overlay` |
| `overlaySmall` (200 × 120 primary) | zIndex 0 / **1** | 0 / 0 | primary at (0, 0), 200 × 120 — the top leading corner |
| `split` | axis `nil` / **vertical** | `nil` / **vertical** | 382 × 322 each, primary on top |
| `splitV` (`.axes(.vertical)`) | `nil` / **vertical** | `nil` / **vertical** | as `split` |
| `splitH` (`.axes(.horizontal)`) | `nil` / **vertical** | `nil` / `nil` | only the primary is visible; the hidden secondary is still laid out at 382 × 644 |

Four results:

1. **The view written directly in the closure reads the environment's defaults** —
   zIndex 0, axis `nil` — and a modifier on it does not change that. A view one level
   down reads the real values, and so does the same view once it is wrapped in a
   `VStack`. Apple's samples for both values read them at that root.
2. **The overlay's primary is the foreground**: it gets z-index 1 and is drawn over the
   secondary; a primary smaller than the container sits at its top leading corner.
3. **A split that cannot split shows only the primary**, as the talk says, but the
   secondary is not removed: it is laid out at full size, so its geometry callbacks
   fire. Its nested axis reads `nil` while the primary's reads `vertical`.
4. The primary's axis reads `vertical` under `.axes(.horizontal)`:
   the container's own axis, not one the style allows.

On the **inner display in landscape**, with the hinge set by `hinge`, last value of
each line (`overlaySmall` and `overlayWrapped` behave as on the outer display):

| `-mode` | Open flat, 180° | Book, 90° |
| --- | --- | --- |
| `overlay` | layered: primary leaf zIndex **1**, both 867 × 635 | side by side: secondary (0, 0, 455.5 × 635), primary (495.5, 0, 371.7 × 635), both zIndex 0 |
| `overlayLeading` | as `overlay` | the sides swap: primary (0, 0, 455.5), secondary (495.5, 0, 371.5) |
| `split` | 433.5 \| 433.5, axis **horizontal** | 455.5 \| 371.5 — the divider on the fold, the 40 pt frame left empty |
| `splitRatio` (0.3) | 260.1 \| 606.9 — the ratio | first 0.3, then 455.5 \| 371.5: the fold wins over the ratio |
| `splitV` (`.axes(.vertical)`) | only the primary, 867 × 635; its leaf axis `horizontal` | the same |

In book pose both styles first lay out as if flat — layered, or split evenly or by the
ratio — and move to the fold a few passes later, when the reserved regions arrive.
Tabletop is not covered: the simulator cannot be rotated from a script.

## `forum_samples_probe.swift` — do the forum-derived samples compile?

The samples `layout-code.md` and `vertical-bars.md` took from the Developer Forums
answers, written as those files write them.
Everything that needs iOS 27.x sits behind `-D FORUM_27_1`,
so the corner-margins sample can also be checked at an iOS 26 deployment target, ungated:

```bash
xcrun --sdk iphonesimulator swiftc -typecheck -D FORUM_27_1 \
  -target arm64-apple-ios27.1-simulator scripts/probes/forum_samples_probe.swift
xcrun --sdk iphonesimulator swiftc -typecheck \
  -target arm64-apple-ios26.0-simulator scripts/probes/forum_samples_probe.swift
```

Both clean against Xcode 27.1 (27A9269) on 2026-10-05.

## `forum_probe.swift` — do the forum answers hold on the simulator?

A UIKit app with one mode per launch.
It checks the answers Apple engineers gave on the Developer Forums
(`references/sources.md` › Developer Forums Q&A)
where an answer describes behavior rather than an API.
`run` below is the same flat → book → flat sequence for every mode:
launch flat, wait 4 s, `duo_pose.py set book`, wait 3 s, screenshot `--display=3`,
`duo_pose.py set flat`, wait 3 s, read the log.

```bash
mkdir -p /tmp/ForumProbe.app
cp scripts/probes/ForumProbe-Info.plist /tmp/ForumProbe.app/Info.plist
xcrun -sdk iphonesimulator swiftc -target arm64-apple-ios27.1-simulator \
  -parse-as-library scripts/probes/forum_probe.swift -o /tmp/ForumProbe.app/ForumProbe
xcrun simctl install <udid> /tmp/ForumProbe.app
xcrun simctl launch <udid> com.example.forumprobe -mode layout   # or sheet, grid, web
xcrun simctl spawn <udid> log show --last 1m --style compact \
  --predicate 'eventMessage CONTAINS "FORUMPROBE"'
```

2026-10-05, Xcode 27.1 (27A9269), iOS 27.1 runtime, inner display in landscape
(951 × 669 pt, safe area bottom 34 / trailing 84), hinge set with `hinge` through `duo_pose.py`.

**`-mode layout`** — a view that reads `reservedRegions` in `layoutSubviews`,
over a control view that reads nothing:

```
flat   LAYOUT control pass=1 · LAYOUT reader pass=1, 2  fold=nil
book   LAYOUT reader pass=3  bounds=(951.0, 669.0) safe=(t:0 l:0 b:34 r:84) fold=(455.5, 0.0, 40.0, 669.0)
flat   LAYOUT reader pass=4  fold=nil
       (no new control pass; one SCENE didUpdateEffectiveGeometry, at launch)
REGIONS margins=(t:0 l:0 b:34 r:84)
        marginsH=(t:0 l:16 b:34 r:84)   marginsV=(t:16 l:0 b:34 r:84)
        barTrailing56=(t:120 l:875 b:34 r:20)   barBottom56=(t:593 l:16 b:20 r:84)
```

1. **A view that reads the regions during layout gets a layout pass when they change.**
   Bounds and safe area stay the same, and the control view gets no pass,
   so the fold reaches only the view that reads the regions.
   This is the observation tracking that Forums 848035 and 847876 describe.
2. **Folding does not call `windowScene(_:didUpdateEffectiveGeometry:)`.**
   The scene geometry does not change.
   Forums 848021 guarantees the call only when the scene moves between screens.
3. **`cornerAdaptation` names the axis along which the region moves in from a corner.**
   `.horizontal` adds 16 pt on the leading edge, and `.vertical` adds 16 pt on the top.
   An edge that the safe area already insets (bottom 34, trailing 84) does not change.
4. **`bar(onEdge: .trailing, extent: 56)` is the system's vertical-bar slot.**
   It is 56 pt wide at x 875–931, inside the 84 pt trailing inset,
   and starts at y 120, under the 84 × 120 status-bar strip.
   `bar(onEdge: .bottom, extent: 56)` sits 20 pt above the bottom edge.

**`-mode sheet`** — a `.pageSheet` with medium and large detents:

| | Flat | Book | Flat again |
| --- | --- | --- | --- |
| Default placement | x 149–802, centred on the display | x 8–467, leading side of the fold | centred |
| `-fold-placement YES` | centred (`.automatic`) | x 483.5–943, `.trailing` | centred |

The sheet stays presented through every step (Forums 848034).
Folded, the default sheet goes to the leading side (Forums 847797).
The fold-driven placement works when the presenting view controller
reads the regions in `viewWillLayoutSubviews` and sets `preferredPlacement`
in `animateChanges`.
That method runs again when the device folds.

**`-mode grid`** — a compositional layout.
Section 0 has two cards that put their gap on the fold, and section 1 is a 6-column grid that scrolls:

```
flat   cards=(0.0, 0.0, 425.3, 120.0) (441.3, 0.0, 425.3, 120.0)  safe=(t:0 l:0 b:34 r:84) adjusted=(t:0 l:0 b:34 r:0)
book   fold=(455.5, 0.0, 40.0, 669.0)
       cards=(0.0, 0.0, 455.7, 120.0) (495.7, 0.0, 371.7, 120.0)  safe and adjusted unchanged
```

The division region adds nothing to the collection view's safe area or content insets
(Forums 847879).
The layout environment's insets stay at leading 0 / trailing 84.
In book pose the gap between the cards falls on the fold's frame.
The scrolling grid keeps six columns and crosses the fold, which is what the forum answer recommends.

**`-mode web`** — a `WKWebView` page with `viewport-fit=cover`
and `padding-left/right: env(safe-area-inset-*)`.
A fixed button moves to the middle of the trailing half
when the host passes the fold in as CSS custom properties:

```
flat   paddingLeft 0px · viewportSegments false · devicePosture false · env(viewport-segment-width) unsupported
book   fold=(455.5, 0.0, 40.0, 669.0) · paddingLeft 0px · paddingRight 84px · innerWidth 951
       button left 663.25, right 783.25 — centred on 723.25 = 495.5 + (951 − 495.5) / 2
flat   button centred on 475.5
```

The division region never reaches `env(safe-area-inset-*)`
or the scroll view's adjusted insets (Forums 848036).
WKWebView does not expose the Viewport Segments and Device Posture APIs.
The fold's frame in the web view's coordinates matched CSS pixels 1 : 1 here:
the page renders at scale 1 and the scroll view has no leading inset.
Between the first report and the fold, the right inset moved
from the scroll view's adjusted inset (84, `innerWidth` 867)
to `env(safe-area-inset-right)` (84 px, `innerWidth` 951).
The cause is not determined; folding back did not reverse it.
