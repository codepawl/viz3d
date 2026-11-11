# Method and scene fields

Reading map: [Pipeline](#pipeline), [Scene object](#scene-object), [Frame options](#frame-options),
[Film plans](#film-plans).

## Pipeline

1. **Shapes.** Each part is a signed distance function built from the helpers in `voxel-splats.js`. Combine with
   `Math.min` (union), `Math.max(a, -b)` (cut) and `smoothUnion`. Add `valueNoise` to a distance for rough rock.
2. **Voxelize.** `voxelizeModel` walks a grid of `spacing` inside `bounds` and keeps cells on the surface. Each cell
   becomes one round splat of radius `spacing * splatScale` (0.62 by default).
3. **Bake light.** For each splat it computes the normal from the distance field, a sun term, a soft shadow by
   marching toward the sun through `shadowModel`, ambient occlusion and a rim term. The result goes into the colour.
   Splats are drawn unlit, so the light never changes after this step. `material` can return an emission above 0 to
   keep a colour bright in shadow (candles, windows, a skull in a hood).
4. **Draw.** `packSplatData` packs lists into the 67js splat data (`positions`, RGBA `colors`, linear `scales`,
   `rotations` with w first). `createGaussianSplats` and `attachGaussianSplats` from
   `@codepawlhq/67js/addons/gaussian-splats` put them in a `Renderer67` with a transparent background.
5. **Post.** `page.js` reads the canvas back and composites, in order: background gradient, stars, moon with halo,
   cloud band, lightning flash, glow halos, then haze (bloom over a threshold, lift toward a haze colour, a mist band
   near the bottom, vignette, a 1 px soften), then the palette with a 4x4 Bayer dither, then a nearest-neighbour
   upscale to the output size.

## Scene object

| Field | Meaning |
|---|---|
| `palette`, `paletteExtra` | colours as `[r, g, b]` 0..1, and extra hex strings merged in at setup |
| `background` | `{ inner, outer, stars, moon: { x, y, radius, color, halo }, clouds }`, moon position in 0..1 of the frame |
| `camera` | `{ target, distance, height, startAngle }` |
| `mist` | `{ color, alpha, low, high, wispColor, wispHeight, trails }`: 320 faint splats and 7 glowing wisps |
| `haze` | `{ color, lift, bloom, bloomThreshold, soften, mistTop, mistStrength, vignette }` |
| `staticLists` | voxelized parts that never move |
| `dynamic(time)` | lists made or placed this frame |
| `glows(time)` | `{ position, color, radius, strength }` halos drawn in screen space |
| `contactShadows(time)` | `{ x, z, radius, strength }` darkening on the ground under moving things |

Numbers that worked on night scenes: haze lift 0.08 to 0.15, bloom 0.8 to 0.9, bloomThreshold 0.55 to 0.6,
mistStrength 0.08 to 0.1, vignette 1.1 to 1.2, mist alpha 0.02 to 0.035.

## Frame options

`window.renderFrame({ time, internalSize, outputSize, style, camera, assemble, dissolve, fadeToBlack, flash })`.

- `style`: `{ dither, paletteSteps, splatScale, palette: 'none' }`.
- `camera`: `{ angleOffset, zoom, orbitSpeed, heightOffset, targetOffset }` on top of the scene camera. Set
  `orbitSpeed: 0` and drive the rest from eased keyframes.
- `assemble` 0..1: splats fall into place. `dissolve` 0..1.25: splats fly apart as ash. `flash` 0..1: lightning.

## Film plans

A plan module exports `frames`, each `{ file, scene, spacing, options }`. `plans/haunted-film.mjs` shows shots as
functions of local time, cuts placed on flashes, a push in that raises `internalSize` for the reveal, and a camera
jolt that decays after an impact. Export event times from the scene (`REAPER_TIMING`, `GALLOWS_BOLTS`) so cuts,
flashes and sound land on them.
