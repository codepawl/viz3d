# Clay reveal film (beauty, clay, beauty)

Reading map: When · Grammar · Build it (any software) · Sound · Checks · Traps.
Learned 2026-11-07 from a Blender + Claude station film (Tripo for a few props, everything else modelled by script,
procedural shaders, AI foley). The flow works in any 3D tool and any editor: two passes, wipes joined afterwards.

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
beauty aerial to 25.7, cut to clay at the opening spot, wipe 28.5-29.5, beauty to the end.

Pacing: the opening beauty runs long, about a third of the film, with the mover's
whole action in it; after that time follows detail, slow where there is structure to read, quick through empty
space. A 21 s metro cut: beauty 0-7.5, wipe to 8.5, clay 8.5-16, wipe to 17, beauty section to 21. A 3 s opening
(the first city proof) was too short.

Everyday places read best (a metro station over a city): build the place by script in a DCC as one GLB or FBX and cut
it with a section plane, as in "Cutaways under ground" in the 3d-generalist skill's `references/clay-reveal.md`,
which also holds subframe blur for the train and the dark-mass trap at the opening camera.

## Build it (any software)

The flow is not tied to one tool: Blender, Cinema 4D, Maya, Houdini, Unreal, Unity, Godot, three.js or 67js all
work, and the wipe can be made in Resolve, Premiere, After Effects, CapCut, Kdenlive or FFmpeg. The per-tool table
(clay override and two-pass render in each) is in the 3d-generalist skill's `references/clay-reveal.md`, "Build it".
The rules that hold everywhere:

- One scene, one camera that is a function of time, two passes rendered with the same frames and size, joined
  afterwards; nothing in the scene knows about the wipe.
- Clay pass: every material replaced by flat colour, no maps: warm grey for built things (about 0.6 linear), darker
  for roads, ground and cut faces, flat green for plants with their leaf alpha kept. Neutral white key, high
  ambient, blurred overcast sky, no bloom, grain, vignette or emissive.
- Render pass: a puresky HDRI with its sun turned to where the key light is, light haze thinned with camera height
  (an eye-level haze washes out an aerial), AgX or filmic.
- Wipe: hard linear wipe at 45 degrees from one corner, about 1 s, no feather. FFmpeg, render A and clay B:
  `blend=all_expr='if(lt(T,B0),if(lt((X/W+Y/H)/2,clip((T-A0)/1,0,1)*1.02),B,A),if(lt((X/W+Y/H)/2,clip((T-B0)/1,0,1)*1.02),A,B))'`.
- Iterate on the whole film in whatever renders a full pass in minutes; keep slow path tracing for the final.
- Worlds that suit it: open city tiles (clean shapes, no bases), a place built by script in a DCC, kitbashed library
  assets; hero props from CC0 libraries or an image-to-3D service.

When the renderer is 67js (measured on an RTX 3060): ten city tiles, 960x540, 4x MSAA, 360 frames per pass in
4 to 17 s. Turn the sky with `loadHdri(url, { rotation })`, `rotation = atan2(sunZ, sunX) of the HDRI's sun -
atan2(z, x) of the wanted azimuth` (67js maps `u = atan(x, -z) / 2pi + 0.5`), check by the brightest pixel of a
still; per-frame `environment: { fogDensity }` for the haze; import `src/view-transform-shader.js` for AgX.

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
- Very heavy CC0 trees (millions of vertices) crash a browser tab or stall a viewport; check the vertex count in the glTF before placing many.
- glTF with KHR_materials_unlit and black factors renders black in some renderers (67js); skip or fix the material.
- A camera looking almost straight down yaws hard for small moves: the crane smeared and snapped at the top in the
  first proof. End the crane on a high oblique (about 60 degrees down), keep it moving through the wipe back, and let
  the last shot drift on at the crane's speed instead of starting from rest.
- Look for the map edge behind the subject: the tallest buildings sat 160 m from the edge of the tiles, so the backlit
  view (camera on the far side from the sun) looked into empty ground. Load the ring of tiles around the area and
  lay a wide ground disc under everything, coloured like the ground in each pass.
