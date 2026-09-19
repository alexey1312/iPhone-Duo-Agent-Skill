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

Clean against Xcode 27.1 (27A9269) on 2026-09-19.

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

Prints scene size, `displayScale`, `safeAreaInsets`, reserved regions,
`verticalBarEdge` and the size classes, on every layout pass, from two readers —
one inset 50 pt inside the other.

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

**The inner display and the folded poses are not covered.** `simctl` has no fold or
pose subcommand and an app launched this way comes up on the outer display, so those
numbers need Device Hub's on-screen controls and a person watching the log.
That is why `device-geometry.md` carries runtime numbers for one pose only.
