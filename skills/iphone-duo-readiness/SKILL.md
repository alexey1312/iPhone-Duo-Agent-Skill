---
name: iphone-duo-readiness
description: >-
  End-to-end readiness workflow for iPhone Duo, Apple's foldable iPhone with an
  outer display and a regular-by-regular inner display. Use when a developer wants
  to prepare, audit, plan or test a SwiftUI or UIKit iOS app for iPhone Duo, the
  iOS 27 / 27.1 SDK resizable-app changes, foldable poses and the hinge, vertical
  bars, Device Hub pose simulation, or Apple's "Prepare your app for iPhone Duo"
  guidance. Runs a read-only scan and SDK check first, produces a tiered plan with
  session citations, changes code only after itemized approval by delegating to the
  iphone-duo specialist skills, and verifies against a pose matrix.
---

# iPhone Duo readiness

Coordinates the four specialist skills. It owns the order of work, the approval
gate and the final report; the specialists own the details.

| Specialist | Owns |
| --- | --- |
| `iphone-duo-adaptivity-audit` | Scene lifecycle, main screen, idiom, orientation, screen bounds, global window state, Face ID assumptions |
| `iphone-duo-bars` | Vertical bars: containers, ordering, titles and symbols, axis, overflow, priority, sheets, opt-out |
| `iphone-duo-layout` | Size classes, standard navigation, safe areas, corners, reserved regions, displacement, arrangements |
| `iphone-duo-displays` | Hinge, Split View multitasking, multiple scenes, scene accessories, cameras, StandBy presence |

## Contract

- **Phase 1 is read-only.** Scanning, SDK checks, reading code and writing the plan
  change nothing in the project. Keep scan output in a temporary directory, not the
  repository.
- **No edits without approval of item IDs** (see `references/recommendation-format.md`).
  "Make my app ready for iPhone Duo" before a plan exists is a request for the plan.
- **The SDK decides what can be written.** Run `scripts/sdk_api_check.py` before
  proposing any API from a talk. Never write code against a symbol the selected SDK
  lacks; mark it *blocked* with the SDK that introduces it
  (`references/api-availability.md`).
- **Cite a session and timestamp for every item** (`references/sources.md`).
- **Report verification honestly.** A green build proves it compiles. Only a pose
  run in Device Hub (or a device) proves layout, and only for the poses actually run.

## Phase 1 — Recommend

### 1. Preflight

```bash
xcodebuild -version
xcrun --sdk iphoneos --show-sdk-version
xcrun simctl list devicetypes | grep -i duo     # empty: no iPhone Duo simulator in this Xcode
```

As of 2026-09-17 the Xcode 27.1 beta — the first with the iPhone Duo simulator and
the 27.1 APIs — is "coming later this month", while Apple's *Preparing your app for
iPhone Duo* guide is already published; `references/api-availability.md` says what
each linked SDK gets on the device and `references/sources.md` keeps the calendar.

Identify the app targets, UI framework mix (SwiftUI, UIKit, both), deployment target,
and how the project is generated (Xcode project, Tuist, XcodeGen, SwiftPM). Read the
project's own agent instructions (`AGENTS.md`, `CLAUDE.md`) — documented decisions
about orientation, idiom or layout forks outrank a scanner match.

Check whether Xcode ships Apple's own modernization skill, which already performs
careful UIKit rewrites (`UIScreen.main`, orientation, scene lifecycle, safe areas):

```bash
out="$(mktemp -d)" && xcrun agent skills export --output-dir "$out" >/dev/null 2>&1; ls "$out"
```

Xcode 27.0 exports it as `uikit-app-modernization`; Xcode 27.1 renames it App
Resizability and adds SwiftUI and iPhone Duo. Note what exists and remove the
temporary directory when done.

### 2. Scan

```bash
python3 scripts/duo_scan.py <project-root> --format json > "$TMPDIR/duo-scan.json"
python3 scripts/duo_scan.py <project-root> --format markdown      # human summary
python3 scripts/sdk_api_check.py                                   # what this SDK can compile
```

`duo_scan.py` skips dependencies (`Pods`, SwiftPM checkouts, `vendor`) and hidden
directories such as worktrees; pass `--include-dependencies` only when the developer
owns that code. Its matches are heuristics — every one needs the surrounding code read
before it becomes a recommendation. Use the `inventory` block to size the bar and
layout work (how many toolbars, split views, custom bar items, camera sessions).

### 3. Triage into tiers

| Tier | Contents | Why first |
| --- | --- | --- |
| 0 — Blockers | App lifecycle without scenes (`DUO005`) | The app does not launch when built with the latest SDK. |
| 1 — Correctness | Main screen, screen bounds, orientation and idiom layout forks, symmetric safe-area math, global window state, Face ID copy (`DUO001–004`, `006`, `009`, `013`) | Wrong layout on the inner display, in Split View, in iPhone Mirroring and on iPad; wrong words on a Touch ID device. |
| 2 — Bars | Standalone bars, titles/symbols, ordering, overflow, priority (`DUO007`, `DUO011`, inventory) | Bars move to the side on the inner display with the 27.1 SDK; items without titles or with text-only labels land badly. |
| 3 — Richer adoption | Sidebar placement, reserved regions for top custom controls, arrangements, hinge effects, scene accessories, camera direction handling, multiple windows, a widget or Live Activity for StandBy on the outer display, App Store screenshots for both displays (`references/device-geometry.md`) | Makes the app good on iPhone Duo rather than merely correct; much of it needs the 27.1 SDK. |

Inside every tier, put items that compile with the installed SDK first and mark the
rest *blocked*. A toolchain upgrade is a prerequisite note on the blocked items, not a
step in front of work the team can ship today — waiting for Xcode 27.1 should never
delay removing `UIScreen.main` or adopting scene lifecycle.

Hand each tier to its specialist skill for the detailed recommendations. Classify
legitimate uses as **kept** with the reason (for example an orientation read that
answers a physical question no geometry can, documented in the code).

### 4. Present the plan

Write the report with the skeleton in `references/recommendation-format.md`: toolchain,
tiers, *kept*, *blocked*, *not verified*. Ask the developer which IDs to apply.

When the developer says "just do it" for something the SDK cannot compile, the useful
answer is still concrete: show the compiler error or SDK check that blocks it, apply or
offer the nearest change that does compile (for example size-class driven layout
instead of an arrangement), and keep the blocked change as a plan item.

## Phase 2 — Apply and verify

1. Apply approved items **one tier at a time**, through the owning specialist skill.
   For large UIKit legacy-API migrations, prefer Apple's exported modernization skill
   if present and review its diff against the plan.
2. Stay in scope: change only lines the approved items name. No drive-by reformatting.
3. Build after each tier with the project's own build command. Fix what you broke
   before moving on.
4. Re-run `duo_scan.py`; confirm resolved findings are gone and nothing new appeared.
5. Run the pose matrix (`references/pose-test-matrix.md`) for the screens touched, if
   an iPhone Duo simulator exists. Otherwise list the poses as *not run* and why.
6. Update each item's status and hand back the report.

## Guardrails

- Do not "fix" orientation, idiom or screen reads that a project documents as
  deliberate; report them as *kept* and let the developer decide.
- Do not wrap missing 27.1 symbols in `#available` hoping it compiles.
- Do not opt out of vertical bars (`toolbarVerticalBehavior(.disabled)`) to make a
  layout problem disappear; opt-out is for the cases in `iphone-duo-bars`.
- Snapshot references and UI tests may move when layouts change; say which ones and
  why rather than re-recording blind.
