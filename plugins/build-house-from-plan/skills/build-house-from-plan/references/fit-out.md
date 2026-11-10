# Fit-out: mixed units and equipment fit

For a shop, café, roastery, brewery, workshop or kitchen fit-out: several sheets from different hands (architect, equipment
supplier, MEP), dimensions written in m, mm, ft-in and inches, and equipment that has to fit with its service space.
`scripts/fitout_check.py` reconciles the units, then checks each item against its room, the doors, the ceiling and the
other items. It runs on plain Python (pillow only for the card) and needs no Blender.

## Reading map

- Keys to add to `plan.json`: "Sheets and dimensions", "Equipment".
- What the check does and how it rates: "Units check", "Fit check".
- Commands, outputs and the 3D highlight: "Run it".

## Sheets and dimensions

`sheets[]`: `{id, name, default_unit}`. `default_unit` (`m`, `mm`, `cm`, `ft`, `in`) is how the sheet writes a bare
number: an architect's `6100` is millimetres, a US supplier's `48` is inches.

`dimensions[]`: `{id, sheet, text, label, a, b}`. Copy `text` exactly as written on that sheet. The same physical
dimension read off several sheets shares one `id`. Readable forms: `6.10 m`, `6100 mm`, `610 cm`, `6100` (sheet default),
`20'-0"`, `20' 0"`, `13'-9 1/2"`, `165"`, `5 ft 6 in`, and a written conversion beside the value, `20'-0" (6.40 m)` or
`6.10 m [20'-0"]`. On one reading, `a` and `b` are the two plan points the dimension spans (finished faces, plan units):
the check then compares the built geometry with what the drawings say.

`unit_tolerance_m` (default 0.02) is how far two readings may differ before they conflict.

## Equipment

`equipment[]`: `{id, name, room, at, rot, size: [w, d, h], clear: {front, back, left, right, top}, z0, asset, asset_rot, paint, material, fit_size}`.
`at` is the footprint centre. At `rot: 0` the front faces -y, as for `furnish`. Lengths are plan-unit numbers or strings
with a unit (`"42\""`, `"600 mm"`), so a supplier's imperial cut sheet goes in as written. Clearances come from the
maker's installation manual: service access, door swing of the unit, combustibles distance for a roaster or oven,
hood or flue space in `top`. Write the manual's numbers, never a guess, and note the manual in `CREDITS.md`.
`asset` (`ph:` or `obj:`) builds the real model stretched to `size` (`fit_size: false` keeps its own proportions);
`asset_rot` turns a model whose front is not -y (check on the `preview_assets.py` grid), `paint` as for `furnish`;
without an asset the item is a plain box in `material` (a name from `house_core.py`); `material: "none"` draws
only its zones, for an item dressed from several `furnish` models (a pallet with sacks on it).
`fit_tight_m` (default 0.10) is the margin under which an item is "tight".

## Units check

Each reading becomes metres. A written conversion that disagrees with its own value by more than the tolerance is a
**wrong conversion**: the value is kept, the conversion is dropped and named. Readings of one `id` that still disagree
are a **conflict**: the smallest is used for fit checks (the safe side) until a person settles it. A dimension whose
`a`-`b` distance in the plan differs from the resolved value is **model off**: the plan was drawn from the wrong
number, so fix the walls and rooms, then rerun.

## Fit check

Every item is checked for: footprint inside its room, each service zone inside its room, footprint clear of each door's
swing and 0.9 m approach on both faces, footprint and each zone clear of every other item's footprint, and height plus
`top` under the room's `ceiling` (or `levels.ceiling`). Service zones may overlap each other: a shared aisle is normal.
The margin is the tightest of those checks in metres. Below zero is **clash**, below `fit_tight_m` **tight**, else
**fits**. The report names the binding check, so the fix is obvious: move the item, swap the model, or change the room.

## Run it

```bash
uv run --no-project --with pillow python scripts/fitout_check.py all plan.json
```

`units` or `fit` alone skip the card. Outputs beside the plan: `fitout_units.md` (reconciliation table),
`fitout_coordination.md` (one row per item: status mark, margin, binding check, action), `fitout_card.png` (the same
as a card with shape-coded marks: circle fits, triangle tight, square clash) and `fitout_report.json`. Exit 1 on any
unit fault or clash. Fix the plan and rerun before modelling further, unless the clash is the point of the piece.

`build_house.py` reads `fitout_report.json`: it builds the equipment into `furnish` and each service zone into a
`fitout` collection, a floor patch in green or amber, and a red volume up to the clear height where a zone clashes (a cut trims it 2 cm above the wall poché, so it reads as
red across the wall it runs into). Shots and films
show them unless they set `fit_zones: false`. A `build_up` film brings the zones in after the equipment lands. Rerun
`fitout_check.py` before every build, since the builder trusts the report as it is.

Tests: `uv run --no-project --with pillow python scripts/test_fitout_check.py` on `examples/fitout-fixture.json`, a
roastery whose supplier sheet writes `20'-0" (6.40 m)` and whose roaster was laid out for 6.40 m.
