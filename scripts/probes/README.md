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
`verticalBarEdge` and the size classes, on launch and on every geometry change.

```bash
xcrun simctl boot "iPhone Duo"
mkdir -p /tmp/DuoProbe.app && cp scripts/probes/DuoProbe-Info.plist /tmp/DuoProbe.app/Info.plist
xcrun -sdk iphonesimulator swiftc -target arm64-apple-ios27.1-simulator \
  -parse-as-library scripts/probes/duo_geometry_probe.swift -o /tmp/DuoProbe.app/DuoProbe
xcrun simctl install booted /tmp/DuoProbe.app
xcrun simctl launch --console-pty booted com.example.duoprobe
```

On the **outer display in portrait** it printed:

```
DUOPROBE size=382.0x644.0 safeArea(t:0.0 l:0.0 b:34.0 tr:84.0) divisions=[] occlusions=[]
         scale=3.0 screenBounds=(0.0, 0.0, 466.0, 678.0) verticalBarEdge=2 hSize=1 vSize=2
```

`verticalBarEdge=2` is `.trailing`; `hSize=1`/`vSize=2` are compact/regular.

**The inner display and the folded poses are not covered.** `simctl` has no fold or
pose subcommand and an app launched this way comes up on the outer display, so those
numbers need Device Hub's on-screen controls and a person watching the console.
That is why `device-geometry.md` carries runtime numbers for one pose only.
