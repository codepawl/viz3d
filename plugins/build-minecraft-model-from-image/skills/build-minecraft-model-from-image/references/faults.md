# Faults found, and what fixed them

Measured on the test run of 2026-10-31: iron kettle, armchair, rubber duck and fire hydrant. Go through this list when looking at `compare.png`.

## The look

| Fault | Fix |
| --- | --- |
| Fine voxel grid at 40+ blocks tall looks jagged and ugly. Rounded forms become staircases and the block grid fights the object | Box model: few cuboids, detail in paint. The old voxel engine is not coming back |
| Texture looks like ore or camouflage: dark iron with bright orange specks, cushion in big two-tone patches | Close ramp steps, speckle colours near the base, share under 0.1 |
| Smooth things look like sponge: rubber and paint with a noisy texture | `noise` around 0.15 on paint and glossy plastic |
| A `round` part from above shows a plus-shaped notch at each corner | `round` and `disc` now fill the notches once `corner` is 3 or more |
| Legs too chunky at the Minecraft-default size | Raise total height (32 to 40 units) so the same 2 x 2 leg is slenderer |
| A one-cube head reads as a box with a beak | Chamfered `round` tiers, with a small flat front for the painted face |

## Reading the picture

| Fault | Fix |
| --- | --- |
| Parts named from the blueprint alone were wrong: a white "bib" was a collared shirt, a die was a playing card, a "dark neck" was a port's shadow | Look at the full picture first and name parts from that. The blueprint is only for coordinates |
| `read_image.py` mask keeps the background inside handles and between slats | `--clear-background 18` on plain backgrounds (24 for pale ones) |
| A thin object crossing the box border was counted as background and ate the mask | Only colours with a 12% share of the box border count. Keep the box loose around the object |
| Busy backgrounds: colour clearing is not safe | Tight `--box` only. The blueprint fades pixels outside the mask, rather than hiding them, so a bad mask still leaves the object readable |

## Building

| Fault | Fix |
| --- | --- |
| A nut placed at the rim's depth vanishes inside the recess | The core's front is at `low_z + depth - recess`. Put the nut from there outward |
| Side ports built long and at a wide angle looked like wings | Aim them nearer the front and keep them short. Check overall width against the picture |
| Arm boards and cushions share a plane with posts and legs, and flicker | Butt the part against the post instead of passing through it. The coplanar warning catches these |
| The picture's view looks right and the back is lazy | `compare.png` has back and side panels on purpose. Look at them as hard |
| A blind reader took the pink hydrant for a pig: raised side ports were ears, the front port a snout, the tiered skirt a costume. The model matched the photo and still read wrong | Add the cues that name the object, even past what the picture stresses: level ports with flanged collars, a bolted flange, an operating nut. Then read it blind again. Result: hydrant became the top guess, though only at 40%, so a recoloured or unusual object stays the hard case |
| Very fine pixel art is noise: card and die pips at 3 units wide read as checkers | Give that detail 4 to 5 units or drop it |
| Brand text from the picture | Leave it out and say so in the docstring |

## Rendering

| Fault | Fix |
| --- | --- |
| Horizon line across the background | Shadow catcher and transparent film. `compare.png` flattens over one backdrop colour |
| Grainy shadow on the floor | Denoising on. The pixel texture stays sharp with sampler Closest |
| A render pass took over 500 s, at about 30 s per view instead of 5 | Not a bug: the GPU was at 100% with another Blender and a game. Check `nvidia-smi` first, and lower samples and resolution when it is busy |
