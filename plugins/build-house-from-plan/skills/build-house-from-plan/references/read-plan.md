# Reading a house plan into `plan.json`

You read the drawing yourself, with your eyes, in crops. No detector or vectoriser: scans have stains, dimension lines and
lettering across the walls, and a wrong wall that looks plausible costs more than the reading does.

## Reading map

- Get a drawing worth reading: "Sources". Fix the scale: "Calibrate".
- Walls, openings, rooms in order: "Read". What to do with what the plan does not say: "Infer and state it".

## Sources

Licence first, then resolution. What worked:

- HABS and HAER on Wikimedia Commons or the Library of Congress (public domain): the full TIF is 5000-10000 px, walls measured,
  and the same record often holds 1930s photographs and elevations. Search `<place> HABS` and read the sheet list.
- USDA farmhouse plans from the 1950s-60s (public domain): printed dimensions, sections, room names, furniture drawn in.
- A sheet under 3000 px across a whole house is too coarse for wall thickness. Look for the TIF.
- Save the sheet untouched as `<project>/source/`, and record its URL and licence in `source`.

Pick a sheet with a floor plan **and**, if you can, an elevation and a section. Each one saved turns inferred items into sourced.

## Calibrate

1. Find the scale bar and the longest printed dimensions. Open crops at their ends and write down exact pixels.
2. Use at least 3 `{px, plan}` pairs far apart, ideally four outer corners. Scans stretch: x and y often differ by a percent, so
   the affine matters. Never derive the scale from one dimension.
3. Copy at least 3 `printed_dimensions` that are not the ones you calibrated on, and let `plan_check.py check` compare them.
4. Choose the origin at the outer front-left corner, and `units` as the drawing's own (feet stay feet: `26'-0"` is 26).

## Read

Open crops at 100%, one wing at a time, with 10-15% overlap. Do not read a whole sheet downsized: thin partitions vanish.

1. **Outer walls**, a counter-clockwise loop on the wall centreline. Thickness is measured from the ink, not assumed: a 1670
   frame house and a 1958 stud wall differ by a factor of three.
2. **Inner walls** next, joined to the wall they meet. Dashed lines are later or removed walls: mark them `dashed`.
3. **Openings** by wall, as distances from `a`. A swing arc gives the hinge and side. Two parallel lines across a wall with no arc
   are a window. Read its sash from the elevation or photos. Note what the arc's absence means, for example a drawing
   that gives no swing for a closet door: put that under `provenance.inferred`.
4. **Stairs**: count treads, read the arrow. **Fireplaces**: the hatched mass is the chimney.
5. **Rooms**: names as lettered. Polygon on the finished faces. Mark open edges, cupboards with `no_access`.
6. **Fixtures** drawn in the plan (tub, sink, range, cabinets) go in at their drawn place. That is sourced, not furnishing.
7. Run `check`, then `overlay`, and open `check_plan_overlay.png` at full size. Fix the plan, not the threshold. A wall whose faces
   score low is usually a wrong thickness or a wall on the wrong side of its ink.

## Infer and state it

A floor plan does not say these. Decide each one and list it in `provenance.inferred`, and repeat that list in the report:

| Question | Where the answer comes from, best first |
|---|---|
| Roof shape, pitch, ridge | section sheet, elevation, photo, then the era and region |
| Ceiling and storey heights | section, elevation, printed note, then 2.4 m modern or 2.1-2.3 m pre-1800 |
| Facade cladding, its exposure | elevation note, photo, then era and region |
| Window sash and panes | elevation, photo, then era |
| Colours and finishes | photo (black and white gives value only), then era |
| Furniture | fixtures from the plan first, then the room's use and era |
| Upper storeys with no plan | exterior shell only, say so |

Era and region matter more than taste: a 1958 USDA farm cottage gets battens and roll roofing, not a stone chimney.
