# Plan file format

`plan.json` is the only input to the build. `scripts/plan_check.py` validates it. Worked example:
`examples/cabin-plan.json`, a one-room cabin from a public domain HABS sheet.

<!-- skill-navigation:start -->
- [Plan file format](#plan-file-format)
- [Frame](#frame)
- [Walls](#walls)
- [Levels](#levels)
- [Openings](#openings)
- [Rooms](#rooms)
- [Roof and frame](#roof-and-frame)
- [Fitted and furnished](#fitted-and-furnished)
- [Site, shots, films](#site-shots-films)
- [Streets](#streets)
- [Gates](#gates)
<!-- skill-navigation:end -->

## Frame

`units` is `ft` or `m`. Every length in the file uses it. Origin is usually the outer front-left corner, x along the
front, y into the house, z up from the finished floor. `calibration.pairs` lists at least 3 `{px, plan}` pairs in
source image pixels. They fit an affine, so a drawing scanned with different x and y scale still lines up.
`ink_threshold` overrides the automatic ink level. `source` needs `image`, `url`, `license`.
`printed_dimensions` lists at least 3 `{label, a, b, value}` copied from the drawing or scale bar.
`provenance.sourced` and `provenance.inferred` are required: every roof, facade, height and finish you did not read
goes in `inferred`, and the report repeats that list.

## Walls

`{id, a, b, t, kind: "ext"|"int", outside: 1|-1, top: "roof", h, z0, free_end, dashed}`. `a` and `b` are the
centreline. `outside` says which side of the a-to-b direction faces out: +1 is its left, so a counter-clockwise outer
loop uses -1. Without `top: "roof"` a wall stops at `h` or `levels.ceiling`. `free_end` marks a stub that touches
nothing. `dashed` marks walls the drawing shows dashed (later or removed): they are built but not scored. Ends resolve
themselves: at an L the earlier wall runs through and the later one butts. At a T the stem butts.

## Levels

For more than one storey, rooms take `level` and `floor_z`. Walls take `level` (or `levels: [1, 2]`) and `z0`. A sheet
that draws the upper floor beside the first uses `calibration.level_offsets: {"2": [dx, dy]}` in plan units, so each
wall is scored against its own drawing. `style.roof_union: true` makes a wall top the highest plane above it, for
crossing gables. The as-built section is taken 1.6 m above each wall's own `z0`.

## Openings

`{id, wall, kind: "window"|"door"|"cased"|"fireplace", from, to, sill, head}`, distances along the wall from `a`.
Stacked storeys may share `from`/`to` when their heights do not overlap.
Windows: `sash: "fixed"|"double_hung"`, `sections`, `panes_x`, `panes_y`, `transom_at`, `shutters` (leaf width).
Doors: `panels: "slab"|"six"|"four"|"two"|"sheathing"`, `leaves`, `swing` (+1|-1 side), `hinge: "start"|"end"`, `open`
(degrees), `material`, `frame_material`, `hardware`. Fireplaces: `room_side`, `depth`, `firebox` (real recess depth), `brick`, `hearth`, `surround`.

## Rooms

`{name, kind, poly, floor, wall, ceiling, ceiling_material, baseboard, crown, chair_rail, trim, open_edges, open_to,
no_access}`. `poly` runs along the finished wall faces. No `ceiling` means open to the roof. `open_edges` lists polygon
edge indices with no wall (edge i runs from point i to i+1). `open_to` names rooms joined with no door.
`no_access` marks a closed cupboard. The check walks doors, cased openings and `open_to` from outside.

## Roof and frame

`roof.planes[]`: `{corners, cover: "shingle"|"roll"|"none", thickness, exposure, course, fascia_depth, fascia, under,
top_material, rafters: {spacing, first, w, d, material}}`. `corners` are the deck underside in this order: eave start,
eave end, ridge end, ridge start, each `[x, y, z]`, overhang included. Walls with `top: "roof"` rise to the lowest plane
above them, which also makes the gable fill. `beams[]`: `{a, b, w, d, material}` where `a`, `b` are bottom-centre
points. `posts[]`: `{at, w, d, z0, z1, material}`. `chimneys[]`: `{at, w, d, z0, z1, material, cap_material, flue, cap}`.
`slabs[]`: `{poly, z, t, material, side_material}`.
`style`: `siding: "clapboard"|"batten"`, `siding_material`, `batten_material`, `exposure`, `wall_base`, `interior_wall`,
`interior_trim`, `window_material`, `door_material`, `reveal`, `end_cap`, `soffit`, `fascia`, `corner_board`,
`corner_material`, `exterior_casing`, `interior_casing`, `baseboard`, `shutter_material`.
Material names live in `TEXTURED_MATERIALS` and `PLAIN_MATERIALS` in `scripts/house_core.py`: add a line there with the
Poly Haven or ambientCG folder and real tile size for a new finish.

## Fitted and furnished

`casework[]`: `{kind: "base"|"wall", a, b, depth, z0, z1, doors, side, counter, material, hardware}`. Doors face the
left of a-to-b when `side` is 1. `stairs[]`: `{start, heading, width, run, rise, steps, z0, material, riser_material}`.
`panelling[]`: `{a, b, z0, z1, cols, rows, side, material, stile, offset}`. `curtains[]`: `{a, b, z0, z1, folds, material}`.
`rugs[]`: `{a, b, material}`. `boxes[]`: `{origin, x, y, z, material}` for shelves and anything plain.
`furnish[]`: `{asset, at, rot, z, scale, fit_w, fit_h, fit_max, fit_size: [x, y, z], hang, part, paint, name}`. `paint` puts every part of a model in one named material, for models with missing textures. `fit_size` stretches
to a measured size, `hang` is the gap below the ceiling for a pendant, `part` keeps one model from a file that holds a
row of variants (Poly Haven plants). At `rot: 0` a model's front faces -y, so it faces `(sin rot, -cos rot)`. `asset` is `ph:<Poly Haven id>` (from
the asset library's `models` folder) or `obj:<Objaverse uid>` (from `site.objaverse_folder`). `at` is the footprint centre. `lamps[]`:
`{at, z, watts, kind, colour, soft}`.

## Site, shots, films

`site`: `hdri`, `sun: {azimuth, elevation, strength, angle, colour}`, `sky_strength`, `sky_clamp`, `centre`,
`flat_radius`, `ground_size`, `ground`, `grass_radius`, `grass_density`, `grass_scale`, `paths[]`, `no_grass[]`,
`plants[]` (same keys as `furnish`), `treeline: {count, radius, assets}` or a list of those for several rings, `window_sky` (brightness of the lamp filling each window on interior shots, default 1.0), `ground_level`, `objaverse_folder`. Azimuth is degrees from +x, counter-clockwise. The sky's own
sun is turned to match and clamped, so the lamp casts the sharp shadow.
`shots[]`: `{name, kind: "interior"|"exterior", pos, look, lens, exposure, meter, meter_target, level, cut}`. Interiors meter
themselves to a median (`meter_target`, default 0.26) the way a camera does; `exposure` adds stops on top. `level` (default on) keeps
verticals vertical with lens shift. `cut` slices the house at that height above the floor, caps the walls in dark
poché and hides the roof and ceilings. `films[]`: `{name, frames, path: [{pos, look}], lens, exposure, cut, interior, level, build_up}`.
`build_up: {walls: [start, end], roof: [start, end], furnish: [start, end]}` (fractions of the film) lays the source sheet
on the floor, aligned by the calibration pairs, grows the walls off its lines from the centre out, lands the roof and
brings in the furniture.

## Streets

`scripts/build_street.py <street.json> <out.blend>` sets finished houses along a road. Keys: `units`, `house_types:
{name: {plan, blend}}` (paths relative to the file), `lots: [{type, at, rot}]`, `paints: {material: [[position, [r, g, b]]]}`
(per-lot colour multiply), `surfaces: [{poly, material, z}]` for road, pavements and drives, then `site`, `shots`, `films`
as above. Render with `render_house.py` as for a house.

## Gates

`plan_check.py check` needs walls joined, openings on their wall, no overlaps, plausible door and window sizes, room
edges on walls, every room reachable, printed dimensions matched within 10 cm and provenance filled in.
`overlay` and `asbuilt` score the fraction of wall faces with ink within 7 cm, require a score of at least 0.70, a
best-fit offset of at most 16 cm over a 60 cm sweep, and a clear win over a 50 cm shifted control. They write
`check_plan_overlay.png` and `check_asbuilt_overlay.png` next to the plan.
