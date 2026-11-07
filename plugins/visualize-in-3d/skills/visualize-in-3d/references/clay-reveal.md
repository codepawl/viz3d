# Clay reveal film (beauty, clay, beauty)

Reading map: When · Grammar · Build in 67js · Where Blender still earns its place · Sound · Checks · Traps.
Learned 2026-11-07 from a Blender + Claude station film (Tripo for a few props, everything else modelled by script,
procedural shaders, AI foley). This is the light version: one 67js scene, two passes, wipes joined in ffmpeg.

## When

A place, city or built world where the making is part of the wow: "this was all built", a pack showcase, a
procedural scene. The clay pass is the explanation, so the film needs no titles.

## Grammar

1. Open on the finished beauty shot from a human vantage (eye level, a rooftop), low sun in front of the camera
   (backlight, haze, bloom). One mover crossing close (a train, a car) sells scale; a slow push is the minimum.
2. A hard diagonal wipe, about 1 s, revealed from the top-left, turns the same frame into clay. The camera keeps moving
   through it. Every wipe in the film is the same one; never a dissolve.
3. In clay the camera leaves the human eye line: crane up and pull back until the whole world reads as one map.
4. Wipe back to beauty from the air (scale), and if there is time return to the opening spot and repeat its action
   (closure), ending on a held backlit frame.
5. Sound only while the picture is rendered: the bed fades just before the first wipe, the clay section is digital
   silence, sound cuts back in hard on the wipe back. No music.

Times for a 36 s cut (measured on the reference): beauty 0-10.5, wipe 10.5-11.5, clay crane 11.5-22, wipe 22-23.25,
beauty aerial to 25.7, cut to clay at the opening spot, wipe 28.5-29.5, beauty to the end. A 12 s proof keeps
beauty 0-3, wipe 3-4, clay crane 4-8.6, wipe 8.6-9.6, beauty aerial to 12.

## Build in 67js

- One page, `?pass=beauty|clay`, one camera function of time. Render each pass to its own MP4 with the same frames,
  then join them; nothing in the page knows about wipes.
- Clay pass: the same parts with `material` replaced by flat colour, no maps: one warm grey for built things
  (about 0.6 linear), darker for roads and ground, flat green for plants (keep the leaf alpha map and its
  `alphaMode`, or leaves become solid cards). Neutral white key, high ambient, a blurred overcast sky, no bloom,
  grain or vignette. Beauty pass: a puresky sunset HDRI, warm key from the sun side, light fog, AgX view transform
  (import `src/view-transform-shader.js`, or the page throws).
- Wipe in ffmpeg, beauty as input A and clay as B:
  `blend=all_expr='if(lt(T,B0),if(lt((X/W+Y/H)/2,clip((T-A0)/1,0,1)*1.02),B,A),if(lt((X/W+Y/H)/2,clip((T-B0)/1,0,1)*1.02),A,B))'`
  with A0 the first wipe's start and B0 the second's. Sound envelope with `volume='...':eval=frame` on the bed.
- Worlds that suit it: city tiles from an open dataset (clean shapes, no bases), or a scene built from recipe
  parts with material `pattern` for procedural looks. Hero props can come from Tripo (Studio credits, commercial use
  on paid plans) or CC0 libraries.

- Put the sun in frame behind the subject: find the HDRI's sun (brightest texel; 67js maps `u = atan(x, -z) / 2pi + 0.5`),
  set the key light's azimuth to where you want it, and turn the sky with `loadHdri(url, { rotation })` in radians,
  `rotation = atan2(sunZ, sunX) of the HDRI's sun - atan2(z, x) of the wanted azimuth`. Check it by the brightest
  pixel of a still, not by eye.
- Haze for an eye-level shot washes out an aerial. Pass `environment: { fogDensity }` to `renderer.render` per frame
  and thin it with camera height (`fog / (1 + height / 300)` worked for a city).
- Measured 2026-11-07 on an RTX 3060: ten city tiles (about 1.5 M triangles), 960x540, 4x MSAA, 360 frames per pass
  in 4 to 17 s. Both passes plus the join take under a minute, so iterate on the whole film, not on stills alone.

## Where Blender still earns its place

The reference modelled hundreds of parts by script with procedural node shaders and wear. Use Blender only for a
hero asset that needs that (modifiers, bevels, node-graph wear, a baked texture), exported as GLB into the 67js
scene. Lighting, camera, both passes and the wipes stay in 67js: they render in seconds per frame and need no bake.

## Sound

The `design-sound` skill: one real ambience bed fitting the place (CC0/CC BY), or AI foley from the frames when that
tool is set up. Nothing under the clay section.

## Checks

- Same frame count and size for both passes (ffprobe) before joining; a one frame offset shows as a jump at the wipe.
- `watch-video` on the result: the wipes rarely register as cuts or moves (slow diagonal edge between similar
  frames); read them from 8 fps sheets instead.
- One still per pass at the opening, mid crane and aerial before rendering the film.

## Traps

- Sketchfab or Objaverse buildings often ship standing on their own diorama base (a plinth, snow, a scanned patch of
  ground) inside the same mesh. In clay those bases show as white islands. Measure the base first (vertex spread per
  height slice); if it cannot be cut, pick another source.
- Very heavy CC0 trees (millions of vertices) crash the tab; check the vertex count in the glTF before placing many.
- glTF with KHR_materials_unlit and black factors renders black in 67js; skip or fix the material.
- A camera looking almost straight down yaws hard for small moves: the crane smeared and snapped at the top in the
  first proof. End the crane on a high oblique (about 60 degrees down), keep it moving through the wipe back, and let
  the last shot drift on at the crane's speed instead of starting from rest.
- Look for the map edge behind the subject: the tallest buildings sat 160 m from the edge of the tiles, so the backlit
  view (camera on the far side from the sun) looked into empty ground. Load the ring of tiles around the area and
  lay a wide ground disc under everything, coloured like the ground in each pass.
