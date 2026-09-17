# Device geometry

What iPhone Duo physically is, where its cameras and hinge sit, and how to draw it.
Use it to reason about poses, to read a screenshot, or to draw a mockup. **Do not
use these numbers for layout code**: layout comes from size classes, safe areas and
reserved regions, never from a display size (`SKILL.md` of `iphone-duo-layout`).

Every fact carries its provenance. Never present a lower grade as a higher one.

| Label | Meaning |
| --- | --- |
| **Apple spec** | [iPhone Duo tech specs](https://www.apple.com/iphone-duo/specs/), checked 2026-09-13, re-checked 2026-09-17 |
| **HIG** | [Designing for iPhone Duo](https://developer.apple.com/design/human-interface-guidelines/designing-for-iphone-duo) (new page, September 9, 2026) |
| **App Store Connect** | [Screenshot specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications), iPhone Duo row added September 9, 2026, checked 2026-09-17 |
| **Derived** | Arithmetic on Apple's figures; exact only as far as the inputs are |
| **Inference** | A reading of Apple's figures that Apple has not stated; the entry says what it rests on |
| **Measured** | Read off the HIG illustrations; approximate (a few percent), not dimensions |
| **Unverified** | Third-party claim; replace it with what an iPhone Duo simulator reports |

## Displays

| | Inner display | Outer display | Source |
| --- | --- | --- | --- |
| Diagonal | 7.6 in (7.58 in as a rectangle) | 5.4 in (5.36 in as a rectangle) | Apple spec |
| Type | OLED folding display, nano-texture finish | OLED | Apple spec |
| Pixels | 1878 × 2670 | 1398 × 2034 | Apple spec |
| Density | 430 ppi | 460 ppi | Apple spec |
| Aspect (long ÷ short) | 1.42 | 1.45 | Derived |
| Active area | ≈ 110.9 × 157.7 mm | ≈ 77.2 × 112.3 mm | Derived (pixels ÷ ppi) |
| Size classes | regular × regular in every pose | like other iPhones: regular height × compact width in portrait, compact × compact in landscape | Tech Talk 111461 3:07; HIG |
| Front camera | Under-display FaceTime camera, ƒ/1.8, 1080p at 30/60 fps | 12MP Center Stage, ƒ/2.2, up to 4K Dolby Vision at 60 fps | Apple spec |
| Capture through AVFoundation | `builtInInnerUltraWideCamera`: square ultrawide sensor, 1080p up to 60 fps | `builtInOuterUltraWideCamera`: square ultrawide sensor, up to 4K at 120 fps | Tech Talk 111465 0:39, 2:16 |
| Virtual Front Camera | One `AVCaptureDevice` (`.front`, wide or ultra wide type) that streams from whichever front camera faces the app; only the common subset (1080p, 60 fps, no depth) | | Tech Talk 111465 1:14, 2:28 |
| Biometrics | Touch ID in the side button on both — no Face ID | | Apple spec |

Both displays (Apple spec): Dynamic Island, Always-On, ProMotion up to 120 Hz, HDR,
1000 nits typical, 1600 nits peak (HDR), 3000 nits peak (outdoor), 2,000,000:1
contrast, Apple Pencil (USB-C) support. Corners are rounded within a standard
rectangle; the viewable area is smaller than the rectangle.

### Points

Apple has not published point sizes, but App Store Connect has published screenshot
sizes for both displays, and those are the closest thing to one.

| | Inner display | Outer display | Source |
| --- | --- | --- | --- |
| Screenshot pixels | 2007 × 2853 (2853 × 2007 landscape) | 1398 × 2034 (2034 × 1398 landscape) | App Store Connect |
| Points at @3x | **669 × 951** | **466 × 678** | Derived: screenshot ÷ 3. Apple has not published a scale for iPhone Duo; @3x is assumed because every current iPhone renders at @3x. Device Hub's `displayScale` will confirm or correct it |
| Relation to the panel | ≈ 6.9 % more than 1878 × 2670 in each dimension | equal to the panel | Derived |
| Rendering | 669 × 951 pt rendered and scaled down ≈ 6.4 % to the panel, as the 5.5-inch Plus iPhones were (414 × 736 pt at @3x, 1242 × 2208 screenshots on a 1080 × 1920 panel — App Store Connect still asks for that size) | 1:1 | Inference |
| Density in points | ≈ 153 pt/in on both displays, so text and controls keep one physical size as the device opens | | Inference |

The product bezel pack on [Apple Design Resources](https://developer.apple.com/design/resources/)
reportedly agrees: its inner-display cutout is 2853 × 2007 px inside a 3093 × 2247
frame, the App Store Connect size to the pixel (third-party measurement of the PNG
alpha channel; *Unverified*).

The earlier third-party figure of **626 × 890 pt** for the inner display (the panel
divided by 3; [MacRumors roundup](https://www.macrumors.com/roundup/iphone-duo/),
Wikipedia) contradicts the App Store Connect sizes and is superseded. The point
arithmetic above was first published by Blake Crosley
([*iPhone Duo for developers*](https://blakecrosley.com/blog/iphone%2Dduo-for-developers));
the inputs are Apple's, the inference is his and ours.

Use 669 × 951 and 466 × 678 as the working shapes for Device Hub resize mode
(`pose-test-matrix.md`) until an iPhone Duo simulator (Xcode 27.1) reports scene
bounds and `displayScale`, then replace them. Code must not care either way: layout
comes from size classes, safe areas and reserved regions.

## Aspect-ratio consequences

Derived from the pixel counts above unless labelled otherwise. None of this is a
layout input; it explains what a screen shape does to content.

- **Both displays have nearly the same aspect ratio** — 1.42 inner, 1.45 outer,
  about 2 % apart. Apple: "Both displays share the same aspect ratio, so content
  scales proportionally" ([newsroom](https://www.apple.com/newsroom/2026/09/apple-unveils-iphone-duo/)).
  An image or video frame composed for one display fits the other with a sliver of
  margin. Layout does not carry over, because the displays report different size
  classes.
- **1.42 is within half a percent of √2**, the A-series paper ratio that keeps its
  proportions when halved. Folded like a book, each half of the inner display has
  ≈ 1.41 : 1 proportions, the shape of the whole display rotated.
- **16:9 video in landscape on the inner display** fills the width and leaves
  1 − (9⁄16) × 1.42 ≈ 20 % of the height as letterbox (≈ 134 of 669 pt if the point
  inference holds), while the picture is ≈ 6.2 in wide against ≈ 4.7 in on an
  iPhone 18 Pro in landscape, about 77 % more area. Video apps get a bigger picture
  and a bigger border at once: design the letterbox area (controls, metadata,
  artwork) instead of leaving it black. Games should change their aspect ratio
  instead (HIG › Best practices).
- **Neither shape exists on another iPhone** (Inference, from the point figures
  above). Against iPhone 18 Pro (1206 × 2622 px, 402 × 874 pt) the outer display is
  ≈ 64 pt wider and ≈ 196 pt shorter, a short wide slab. The inner display in
  portrait is ≈ 229 pt wider than an iPhone 18 Pro Max (440 × 956 pt), and in
  landscape it is taller than any iPhone is in landscape; its 1.42 ratio is nowhere
  near the 2.17 of the Pro line. A phone-width column centered on it wastes most of
  the screen.

## Body

| | Value | Source |
| --- | --- | --- |
| Open | 164.6 × 117.8 × 5.2 mm (body aspect ≈ 1.40 landscape) | Apple spec; aspect derived |
| Closed | 84.1 × 117.8 × 11.3 mm (body aspect ≈ 0.714 portrait) | Apple spec; aspect derived |
| Weight | 254 g | Apple spec |
| Materials | Titanium foldable design; 3D-printed hinge cover in 100 % recycled titanium; Ceramic Shield 2 front, Ceramic Shield back; IP68 | Apple spec |
| Finishes | Night Sky, Star White | Apple spec |
| Rear camera | 48MP Dual Fusion: Fusion Main (26 mm, ƒ/1.6) and Fusion Ultra Wide (13 mm, ƒ/2.2) | Apple spec |
| Buttons and ports | Side button with Touch ID, Camera Control, volume up/down, USB-C | Apple spec |

Bezel around the inner display ≈ 3.4 mm per side (derived: body minus active area)
— the diagrams show ≈ 1.8 % of body width, which agrees within measuring error.

## Hinge, cameras and reserved regions

- **Hinge:** in the centre; when partially open it divides the inner display and the
  centre becomes the **folding region**, which content avoids. (HIG; Tech Talk 111463
  1:29, 7:50)
- **Outer front camera:** in the corner, always visible, vertically aligned with the
  controls on the side; its reserved region is always present and expands into the
  Dynamic Island for Live Activities. (HIG)
- **Inner front camera:** behind the display, hidden until the camera is active; then
  its region appears and the UI moves aside. (HIG; occlusion region, Tech Talk 111463
  7:50)

### Where they are (measured from the HIG illustrations)

- **Closed, outer display facing you:** the hinge spine is on the **left** edge. The
  outer display's corners are tight on the hinge side (≈ 2 % of body width) and large
  on the free side (≈ 15 %). The camera is a **round hole at the top right**, centre
  ≈ (88.5 % W, 8 % H) of the outer display, diameter ≈ 7.7 % of its width — not a
  Dynamic Island pill.
- **Open flat, landscape, inner display facing you:** uniform rounded corners
  (≈ 7 % of body width). The folding region is a vertical band at the centre,
  ≈ 2.8 % of the display width (≈ 4 mm, derived from that estimate). The inner camera,
  drawn only when active, sits in the **right half**, centre ≈ (70 % W, 8 % H),
  diameter ≈ 3.5 % of the width.
- **It opens like a book.** Put those together: the outer display is on the back of
  the **left** half, the inner camera is in the **right** half. (Measured + derived)

## Poses

The HIG illustrates six, left to right. The pose names are descriptive labels, not
Apple's terms, except *book* and *tabletop* which the talks use (Tech Talk 111463 4:00).

| # | Pose | What faces the user |
| --- | --- | --- |
| 1 | Closed | Outer display, portrait, camera at the top corner |
| 2 | Tent (standing on its edges) | One slope shows a display — the outer one, since the device folds inward (derived) |
| 3 | Open flat, landscape | Inner display, fold vertical |
| 4 | Partially folded like a book | Inner display in two halves, fold vertical |
| 5 | Open flat, portrait | Inner display, fold horizontal |
| 6 | Laptop / tabletop (bottom half flat on a surface) | Inner display, portrait, fold horizontal |

Consequences for pose 6 (derived from the measured positions): with the camera half
on top, the device has been turned **counter-clockwise** from pose 3, so the inner
camera sits near the **leading (left) edge, ≈ 30 % down** the display, and the outer
display faces the table. Each half is wider than tall (≈ 1.41 : 1).

Design with size classes rather than per pose: compact width for the outer display,
regular width for the inner display. (HIG; Tech Talk 111466 3:42)

## App Store assets

App Store Connect lists iPhone Duo screenshot sizes of 1398 × 2034 and 2034 × 1398 px
(outer display) and 2007 × 2853 and 2853 × 2007 px (inner display); app previews use
the same device resolutions. "Support for uploading assets for this device in App
Store Connect will be available later this year" (checked 2026-09-17). Apple's
product bezel pack for iPhone Duo is on the
[Design Resources](https://developer.apple.com/design/resources/) page. Screenshots
are a Tier 3 item in the readiness report, not a code change.

## Drawing iPhone Duo mockups

1. **Proportions first.** Closed ≈ 0.71 : 1 portrait (a short, wide slab), open
   ≈ 1.40 : 1 landscape. It is not a tall 19.5 : 9 phone cut in half like a clamshell
   flip phone.
2. **Outer display:** hinge spine on the left, tight corners on the hinge side, large
   corners on the free side, a round camera hole at the top right. Toolbars, tab bars
   and navigation controls sit on the side, stacked top to bottom as Dynamic Island,
   status bar, toolbar, tab bar. (HIG)
3. **Inner display:** uniform rounded corners, no visible camera cutout and no
   permanent pill. Draw the inner camera only when the camera is active, in the right
   half of the landscape display. The spec lists Dynamic Island for both displays, so
   a Live Activity may appear there — as software, not as a hardware notch.
4. **Bars:** vertical on the outer display and on the inner display in landscape;
   horizontal only on the inner display in portrait. (HIG; Tech Talk 111466 5:07)
5. **Folding:** in book pose show the fold as a band content avoids, not as a gap;
   sheets and alerts slide clear of it. (HIG; Tech Talk 111466 8:36)
6. **Opening shots must be physically possible.** The outer display is on the back of
   the left half. In laptop pose with the camera half on top, the lifting half's
   outside is the device back — a lid-lift shot cannot show outer-display content on
   the lid while the camera sits in the same lid.
7. **Label estimates.** Numbers from the *Measured* and *Unverified* rows are good
   enough for a drawing, not for a spec sheet or code.

Apple's own artwork is a better base than a hand-drawn frame: the HIG illustrations
are served at `https://developer.apple.com/tutorials/images/com.apple.HIG/designing-for-iphone-<name>@2x.png`
(`~dark@2x` for dark), with names such as `device-layout-outer`,
`device-layout-inner`, `poses`, `safe-area-outer-camera`, `safe-area-inner-camera`,
`tab-bar-toolbar-layout`, `multitasking`. The `/images/com.apple.HIG/…` path written
in the page data returns 404; the `/tutorials/images/` prefix works. Check
[Apple Design Resources](https://developer.apple.com/design/resources/) for device
templates before drawing one.
