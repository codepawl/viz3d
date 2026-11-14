---
name: make-pixel-splats
description: Make pixel art scenes out of gaussian splats written by code, with no 3D model, rendered in 67js. Shapes come from signed distance functions, every surface voxel becomes one round splat with sun, shadow and ambient light baked into its colour, and a post pass adds glow, haze, a small palette and ordered dither before a nearest-neighbour upscale. Includes three haunted medieval scenes, three cozy islands, eased motion helpers, a headless frame renderer and a 24 s film plan cut on lightning. Use for pixel art splats, voxel splat dioramas, code-built gaussian splat scenes, scenes like a haunted crag or a witch swamp.
license: MIT
---

# Pixel art from code-built gaussian splats

No mesh and no capture go in. A script writes every splat: position, round scale and a colour that already holds its
light. 67js draws them at a low internal size, then the page turns the frame into pixel art.

## Set up

`{{SKILL_DIR}}` is this skill's folder and `{{WORK_DIR}}` the folder where projects live.

1. Copy `{{SKILL_DIR}}/scripts/` to `{{WORK_DIR}}/pixel-splats/` and run `npm install` there. It installs
   `@codepawlhq/67js`, which brings `playwright-core`. Rendering needs Chrome installed.
2. Stills: `node render.mjs plans/stills.mjs out/stills`. Film frames: `node render.mjs plans/haunted-film.mjs out/film`
   (`FILM_FPS`, `FILM_SIZE`, `FILM_UNTIL` set rate, output size and a cut-off), then
   `ffmpeg -framerate 30 -i out/film/frame_%04d.png -c:v libx264 -pix_fmt yuv420p film.mp4`.
3. A frame takes 0.3 to 1 s on a mid-range GPU at 60k to 80k splats.

## Files

| File | Holds |
|---|---|
| `voxel-splats.js` | SDF shapes (sphere, box, capsule, cone, torus, floating island), `voxelizeModel`, `placeSplats`, `packSplatData` |
| `motion.js` | easing, walk-then-hold steps, struck pendulum that rings down, smooth wobble |
| `page.js` | scene setup, mist and wisps, assemble and dissolve, camera, glow halos, haze, palette and Bayer dither |
| `medieval.js`, `medieval2.js` | haunted chapel crag, witch swamp, gallows with the Reaper |
| `scenes.js` | lighthouse, snail meadow, koi pond, and `SCENE_BUILDERS`, the registry `render.mjs` names scenes from |
| `plans/` | a stills plan and the 24 s film plan with eased keyframed cameras |

## Make a scene

1. Write a builder `(spacing) => scene` like the ones in `medieval2.js` and add it to `SCENE_BUILDERS`.
2. Each static part is a model `{ distance, material, bounds }` passed to `voxelizeModel(model, spacing, light,
   { shadowModel })`. `material(x, y, z, nx, ny, nz)` returns `[r, g, b, emission, alpha]`. Give every part the whole
   scene as `shadowModel` so parts shadow each other.
3. Moving parts are voxelized once around their own pivot and moved each frame with `placeSplats(list, { x, y, z,
   heading, scale, deform })`. Small things (bats, bubbles, ash, eyes) are point lists built in `dynamic(time)`.
4. The scene object also carries `palette`, `background`, `camera`, `mist`, `haze`, `glows(time)` and
   `contactShadows(time)`. Read [references/method.md](references/method.md) for the fields and the numbers that worked.
5. Render one still in each look, read it, fix, and only then render a film.

## Looks

- A: internal 216 px, spacing 0.02, dither 0.12. Chunky, good on bright scenes, muddy on dark ones.
- C: internal 360 px, spacing 0.015, dither 0.06, `paletteSteps: 3`. Holds detail at night. The haunted films use it.
- Reveal: raise `internalSize` to 1080 and set `style.palette` to `'none'` to show the single round splats.

## Matching a crisp reference

Sharp pixel art is decided by the shapes and colours you build, not by the post pass. Rounded SDF shapes with smooth
baked light and noisy materials give many close tones side by side, and that reads as blur at any pixel size. Flags
that harden alpha, drop haze, thin the palette or median the tones made it cleaner but never crisp (three rounds,
then dropped).

- Before building, put a reference frame beside a first still at the same scale, zoom both 3x, and send that pair to
  the owner. Do it at the first still, not after several film previews, and send it whenever they ask to compare.
- Build for flat pixels from the start: boxy parts with flat faces, one or two hues per scene in 4 to 6 steps, material
  colour picked from that ramp with no noise, light quantized into bands, dither used as texture on large faces.
- Plain dark background: no gradient, moon halo, clouds or dense stars. No glow halos, haze, mist or translucent
  splats; a light is a hard bright pixel cluster.
- Internal size near 190 to 216 px with an integer upscale.
- The cozy and haunted scenes here are the soft, painterly look. Do not promise the crisp look from them.

## Rules that came from mistakes

- Never mutate cached static lists in a frame. Copy before scaling, or splats shrink a little every frame.
- Keep mist alpha near 0.02 to 0.04 and its splats low and outside the subject, or it buries the scene.
- Keep haze soften at 1 px at any size, or the high resolution reveal turns to blur.
- Dark scenes need moonlit sun colour near white and an ambient near 0.4. A green ambient makes green soup.
- A face in a dark hood needs a pale, slightly emissive skull and small eye splats with a tight glow, or it reads as a
  red blob.
- A thin blade swung in the plane that faces away from the camera reads as a bar. Swing it in the plane facing the
  viewer.
- Linear motion looks dead: ease every move, hold between moves, let swings ring down, and key the camera.
- Lightning is many filled steps with a soft wide twin, plus a sky flash and a glow on the ground, not a dotted line.
