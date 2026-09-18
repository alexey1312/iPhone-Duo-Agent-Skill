---
type: llm
weight: 1
---

The response must make availability depend on the **installed toolchain**, not on a
remembered fact. A successful response:

1. Says that both symbols need the **iOS 27.1 SDK**, and that the iOS 27.1 SDK ships
   with **Xcode 27.1** — so the answer is "yes" on Xcode 27.1 and "blocked" on
   Xcode 27.0. It must not state flatly that these APIs are unavailable, unreleased,
   or "coming later this month".
2. Names how to check rather than asserting from memory — running
   `scripts/sdk_api_check.py`, or reading the measured table in
   `references/api-availability.md`.
3. Distinguishes the **SDK** question from the **deployment target** question: with
   the 27.1 SDK installed and a lower deployment target, the work is not blocked, it
   needs `if #available(iOS 27.1, *)`.

It must NOT claim that `builtInOuterUltraWideCamera` is missing from the iOS 27.1
SDK. AVFoundation declares it, but only under the Objective-C constant
`AVCaptureDeviceTypeBuiltInOuterUltraWideCamera`, so a plain text search for the
Swift name finds nothing. A response that mentions this Objective-C/Swift spelling
trap, or that simply reports the camera type as available, is correct; a response
that reports it as absent from a 27.1 SDK fails.

Partial credit: getting (1) right but missing the deployment-target distinction in
(3) is a pass with reservations. Asserting a hard "no, not yet available" is a fail
regardless of the rest.
