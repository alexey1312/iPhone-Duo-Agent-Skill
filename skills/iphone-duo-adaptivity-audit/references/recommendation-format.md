# Recommendation format

Use this shape for every recommendation, whether it comes from the scanner or from
reading code. It keeps the developer in control: each item has a stable ID they can
approve, and nothing is changed until they do.

## Per item

```markdown
### DUO-07 · Move the export actions out of the custom UIToolbar

- **Finding:** `DUO007:Sources/Editor/EditorViewController.swift:88` — `let toolbar = UIToolbar()`
- **Why it matters on iPhone Duo:** content of standalone bars is not considered for
  vertical bars, so on the inner display these actions stay horizontal while the
  navigation bar moves to the side.
- **Source:** Raise the bar with iPhone Duo (Tech Talk 111462) 2:00
- **Change:** set `toolbarItems` on the view controller and show the navigation
  controller's toolbar; delete the manual bar and its constraints.
- **SDK:** available in the selected SDK (iOS 27.0) · or: *blocked on iOS 27.1 SDK*
- **Risk:** low — layout-only; one screen.
- **Verify:** Device Hub, iPhone Duo outer display and inner display in landscape:
  actions appear in the vertical bar; inner display in portrait: horizontal.
- **Status:** proposed
```

## Rules

- **IDs are stable** across a session (`DUO-01`, `DUO-02`, …). A scanner finding keeps
  its own ID (`DUO007:path:line`) in the *Finding* line so it can be re-located.
- **One source per item, with a timestamp** (or, for the Human Interface Guidelines,
  the page section). No source, no recommendation — if the advice is your own
  inference, label it *inference* and say what it rests on.
- **Say what you did not verify.** "Builds with Xcode 27.0" is not "works on iPhone
  Duo". If no iPhone Duo simulator was available, the *Verify* line is a step for the
  developer, not a claim.
- **Group by tier** (see the orchestrator): blockers, correctness, bars, richer
  adoption. Inside a tier, order by user impact, not by file.
- **Status values:** `proposed`, `approved`, `applied`, `verified`, `blocked`
  (with reason), `declined`, `kept` (legitimate use left in place, with reason).
- **Batch approval is fine** when the developer names it ("apply DUO-01 to DUO-05",
  "all tier 1"). A general "fix everything" before a plan exists means: produce the
  plan.

## Report skeleton

```markdown
# iPhone Duo readiness — <app>

Toolchain: Xcode <version> (<build>), iOS <sdk> SDK · Scan: duo_scan 1.0.0, <n> files
Lifecycle: <swiftui-app | scene | app-delegate-only>

## Summary
<3–5 sentences: what breaks today, what is cheap, what waits for 27.1.>

## Tier 0 — Blockers
## Tier 1 — Correctness on the inner display
## Tier 2 — Bars
## Tier 3 — Richer adoption
## Kept as is
## Not verified
```
