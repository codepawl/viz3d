# Method and API

Reading map: Reading the view, Choosing boxes, API, Materials, Paint, Inferring the unseen sides. Read the whole section you need.

## Reading the view

Convention: x is width (+x is the viewer's right when facing the object's front), y is up, z is depth (+z is the front).
`yaw` 0 looks at the front. Positive yaw moves the camera to the object's right, so the object seems to point left in the picture.
`pitch` is the camera's height above the horizon. Both go in `SOURCE`.

A side-on or front-on picture is yaw 0 and a small pitch. For a three-quarter picture of something with feet, solve from the feet on the blueprint.
With near-front foot as the origin: moving to the near-back foot shifts the picture by (a, b), and moving to the far-front foot shifts it by (-c, d). Then:

- `tan(yaw) * sin(pitch) = d / c`
- `sin(pitch) / tan(yaw) = b / a`
- `depth = a / sin(yaw)`, `width = c / cos(yaw)`
- real heights = picture heights / `cos(pitch)`

The chair's four feet gave yaw 57, pitch 25-ish and width about equal to depth this way. Without feet, estimate from how far the centre line (beak, front port) sits off the middle of the silhouette.

## Choosing boxes

One box per real part, then ask whether the part can be merged and painted. Height in units comes from the thinnest thing that must show:
chair legs of 2 x 2 looked clumsy at 32 tall and right at 40. A kettle needed only 28.

| Shape in the picture | Build it with |
| --- | --- |
| Turned body (kettle, barrel) | `round` tiers following the silhouette rows: narrow, wide, wide, narrow |
| Ball-like head | `round` tiers with a large `corner`, plus a flat front for the painted face |
| Port, lens, wheel | `disc` with `recess=1` for a real dent, then a small box for the nut |
| Handle, brace, wire | `beam`s between points. 4 to 7 segments make a clean arch |
| Thin frame | plain boxes at 1 to 2 units, set between the posts so faces never share a plane |
| Lettering, eyes, screws, patterns | `paint` on a face, never boxes |

## API

`build(kit)` returns a `kit.BlockModel(materials, seed=...)`. All sizes are whole units. `low` may be a half unit, to centre odd sizes.

- `model.box(low, size, material, top=, bottom=, sides=, rotation=(x, y, z), pivot=, name=)` returns a `Box`. Rotation is in degrees, applied z, then x, then y, around `pivot` (default: the box's centre).
- `model.round(center_x, center_z, low_y, height, diameter, material, corner=, top=, bottom=, name=)` returns 5 boxes: core, back slab, front slab, left slab, right slab. So index `[2]` is the front.
- `model.disc(center_x, center_y, low_z, depth, diameter, material, corner=, recess=, core=, rotation=, pivot=, name=)` is a round part facing +z. Rotate it to aim it: a rotation of (-12, 50, 0) aims it right, forward and slightly up. Returns `(core_box, rim_boxes)`.
- `model.beam(start, end, (across, deep), material, name=)` is a bar between two points.

Odd diameters need a centre ending in .5 and even ones a whole centre, or the texels land on half units.

## Materials

`kit.Material(ramp, style="plain", noise=0.5, rim=True, roughness=0.85, metallic=0.0)`

- `ramp`: hex colours lightest first, from `palette.png` and the picture. Keep the steps close. Far-apart steps look like camouflage or ore.
- `style`: `plain` scatters texels, `wood` draws grain lines along the long side, `metal` shades top to bottom, `fabric` flecks.
- `noise`: 0.15 for paint and glossy plastic, 0.3 to 0.5 for wood and fabric, 0.5 to 0.7 for rough iron.
- `rim=True` lightens the top row and darkens the bottom row of side faces, which is what makes a part read as a part. Turn it off for tiny pieces and recesses.

## Paint

- `box.paint(face, rows, legend, at=(column, row))` draws pixel art. Faces are `front back left right top bottom`, and rows read as seen from outside that face. On `top`, the front edge is the bottom row.
- `box.band(row, colour)` draws a line round the four sides, counted from the top: seams and stripes.
- `box.speckle(colours, share, faces=)` scatters texels: rust, wear. Keep the colours close to the base, and the share under 0.1 unless the object is truly that worn.
- On a `round`, paint the core or a slab, as they are separate boxes. A face that needs to span wider than the core goes on its own box.

## Inferring the unseen sides

Say the reasoning in the docstring, so it can be checked against later references.

- A turned object repeats itself all the way round. Don't turn its ports with it: decide how many there are.
- Furniture mirrors left to right, and the back rail or stretcher is what shows through the frame.
- Animals and toys: the body is usually longer than wide, and the tail and back continue the visible curve. Clothes wrap round.
- A part that needs support must have it: a handle has lugs, an arm board has a post.
