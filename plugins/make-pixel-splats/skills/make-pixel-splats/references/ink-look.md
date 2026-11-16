# Ink look, showcase and "how it's made" film

The crisp pixel-splat diorama look that trends on X, rebuilt from its published method with our own code. The
example is the windmill island (`windmill.js`). A showcase render and a 36 s explainer of the method both shipped from
it on 2026-11-17.

## Reading map

- Making a scene in this look: "The look" and "Build the scene".
- Effects that move (smoke, water, birds, clouds): "Effects".
- Picking splat density: "Detail levels".
- Turning parts that must not cut through others (sails, wheels, doors): "Clearance check".
- The finished clip: "Showcase render".
- The explainer of the method: "How it's made film".
- Posting both: "Posting".

## The look

1. Every splat carries one colour picked from a short dark-to-light ramp of the scene palette, never a smooth shade.
   Give a material `surface: { ramp: [palette indices], mottle }`. `voxel-splats.js` picks the step from half-Lambert
   light times the shadow, darkened in creases, plus small noise:
   - `light.rampShadowFloor` (0.3 in the windmill): how dark the shadowed side gets.
   - `light.rampOcclusion` (0.65): how dark creases get.
   - `light.rampJitter` (0.16) and `light.rampMottle` (0.2): random steps, so faces do not look printed.
   - `light.rampGain` (1.08): pushes the whole ramp up or down.
2. Render with `style: { ink: true }`. The page draws the splats at twice the pixel grid. Each art pixel reads its
   2x2 samples. Inside an object it takes the colour most samples agree on, snapped to the palette. Where the samples
   disagree it paints a contour in a darker tone of that body colour, never black. Options: `inkContour`,
   `inkContourStrength` (0.65), `inkDither` (0.03) and `inkPalette`.
3. Coverage under alpha 128 counts as background, so anything translucent disappears. Every effect is opaque.
4. Upscale with nearest neighbour only. 1200 px out from 400 px is 3x. It stayed clean at crf 12 with `-tune animation`.

## Build the scene

- Perfect geometry reads as fake. Give each repeated part
  its own small faults. Each windmill sail has its own angle, length, warp, missing slats and tip.
  About 1 in 5 boards uses a rotten ramp. Courses of stone wander and vary in width.
- A copy of someone's scene gets flagged. Add and remove elements until it is a different place. The windmill
  dropped the fence and the ripe field. It added a cottage with a chimney, a pond and waterfall, a gallery, a cart
  and a path.
- Noise in a distance function is slow. Add it only near the surface, behind a bound check. At spacing 0.024 the
  windmill build went from 15.7 s to 0.6 s.
- Turn a small building's gable end to the camera, with the door and windows on it. A roof slope facing the camera
  reads as a box.

## Effects

- A big single splat renders as a smooth capsule. Fill each puff with many small opaque splats, and dither their
  tone with hash noise (`fillPuff` in `windmill.js`).
- Smoke is separate puffs (16, lifetime 8 s, growing with age), not one stream. One stream merges into a tube.
- `dynamic(time)` returns the turning sails and these effects:
  - chimney smoke and waterfall drops that break up, with foam at the lip
  - glints on the water, chaff and motes
  - 4 birds with 4-segment wings and 7 cloud banks of 7 puffs.

## Detail levels

Each row has 1200 px out. The build runs once per scene, then each frame takes about 0.5 to 1 s.

| Grid | Upscale | Spacing | Splats | Build |
| --- | --- | --- | --- | --- |
| 200 | 6x | 0.006 | 355k | 22 s |
| 240 | 5x | 0.005 | 517k | 60 s |
| 300 | 4x | 0.004 | 817k | 128 s |
| 400 | 3x | 0.003 | 1.46M | 194 to 296 s |

An picked 400 after 200 looked blurry. `plans/windmill-density.mjs` renders the four side by side. Send them as one
sheet and let the owner pick.

## Clearance check

A turning part that passes through another part is the first thing people notice. The windmill fix was a longer windshaft (`SHAFT_REACH` 0.1) and an upward tilt (0.12 rad).
`node tools/check_sail_clearance.mjs` turns the sails through 72 angles. It reports the smallest gap to the rest of the
scene, skips the hub, and exits non-zero at or below half the splat spacing. Write the same kind of check for any new
turning part before a film render.

## Showcase render

`plans/showcase.mjs`: 15 s at 24 fps with `SHOWCASE_GRID` and `SHOWCASE_SPACING`, scene time starting at 2 s. The
camera swings about 0.8 rad, pushes in over 6 s, holds, and pulls back. Check the sails stay in frame at the push-in
by measuring bright pixels on the frame edges. The first push-in cropped them.

## How it's made film

36 s explainer built from layers, then composited:

1. `plans/howto-layers.mjs` renders four layers over time into `<out>/howto/{ink,clay,raw,samples}`. `HOWTO_GRID`,
   `HOWTO_SPACING` and `HOWTO_FPS` set the size. The final run had 1,080 layer frames at grid 400.
   - `look: 'clay'` turns every splat grey by brightness, so shapes read before colour. `splatKeep` draws only a share
     of the splats, each bigger, so the dots are visible.
   - The camera orbits slowly. It holds still during the before and after of step 4, or the two halves do not match.
2. `tools/howto_compose.py <layers> <out> --scale 2 --grid 400` composites the layers. It adds these overlays:
   - step labels, a code panel that types the distance functions and palette chips
   - the 2x2 sample grid zoom and an edge zoom with a wipe
   - a blinking highlight on contour pixels (without it the contour was invisible) and a credit pill.

    Fonts come from
   `HOWTO_FONT_BOLD`, `HOWTO_FONT_REGULAR` and `HOWTO_FONT_CODE`, or the first system font found.
3. The sound is a lo-fi bed with wind, sail creak, water and birds, plus a pop on each step label. Mix it to
   -14 LUFS with the `design-sound` skill. Use the same mix for the showcase, without the pops.

## Posting

A flow that worked:

1. The showcase goes out alone first with a casual caption ("finally figured out how these are made"). A reply in the
   same scheduled thread says "will post the workflow soon".
2. A few hours later, a quote of that post carries the tutorial video. Its caption lists the steps in plain lines and
   credits the method's author.
3. One reply under the showcase links Crucible.

Source: JungleSilicon (ink studio method, posts on X, November 2026)
