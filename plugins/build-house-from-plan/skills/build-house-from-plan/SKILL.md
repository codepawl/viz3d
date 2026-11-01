---
name: build-house-from-plan
description: Turn a 2D house plan into a photoreal 3D house in Blender Cycles, checked by overlaying the build on the drawing. Stills, a film of the walls rising off the drawing, and whole streets of houses. Use for a floor plan, a house plan or a blueprint that should become a real-looking 3D house or street.
license: MIT
---

# Build a photoreal 3D house from a 2D plan

A plan file is read off the drawing, checked against the drawing, built with real wall thickness and real frames, then
dressed with scanned materials and models and rendered in Cycles. The drawing stays the judge: nothing ships unless the
built floor plan lands on its ink.

## Order of work

1. **Find the sheet and its sources.** Licence-clear plan, plus photos of the same building or its type and period.
   Read `references/read-plan.md` in full: sources, calibration, reading order, the table of what may be inferred.
2. **Write `plan.json`.** `references/plan-format.md` holds every key. Read the sections you need. Everything not read
   off the drawing goes in `provenance.inferred`, and the final report repeats that list.
3. **Check before building.** Stop and fix on any failure:
   ```bash
   uv run --no-project --with pillow --with numpy --with scipy python scripts/plan_check.py check plan.json
   uv run --no-project --with pillow --with numpy --with scipy python scripts/plan_check.py overlay plan.json
   ```
4. **Build.** One Blender at a time:
   ```bash
   blender -b --factory-startup -t 6 -P scripts/build_house.py -- plan.json out/house.blend
   ```
   It writes the as-built section next to the blend. Score it with `plan_check.py asbuilt <section.json>`.
5. **Preview small.** `--samples 48 --scale 50`, then look at every shot beside the reference photos:
   ```bash
   blender -b out/house.blend -t 6 -P scripts/render_house.py -- plan.json out/preview --samples 48 --scale 50
   ```
6. **Hunt what looks fake.** Read `references/realism-faults.md` before judging: the faults this pipeline actually
   produced, how each one looked and what fixed it. Add each new fault there the same turn.
7. **Final.** 1920x1080 at about 512 samples, each still at full size beside a real photo. Look at each one.
8. **Films.** `--film <name>`. A `build_up` film rises the walls off the sheet itself. Streets: "Streets" in
   `references/plan-format.md`.

## Hard rules

- Gate: at least 0.70 of wall faces within 7 cm of ink, best-fit offset at most 16 cm, a clear win over a 50 cm shifted
  control, on both the plan and the as-built section. A fail means the plan or the build is wrong. Never loosen it.
- Sizes are measured or printed, never guessed by eye: wall thickness, ceiling height, sill and head. A height the drawing
  does not give is inferred from the type and period and listed as inferred.
- Roof and facade without elevation drawings are inferred. Say so in the report.
- Real materials only: Poly Haven or ambientCG scans with their true tile size. No flat colour on a visible surface.
- Furniture comes from real PBR models placed by how the room is used, with walking space kept and fronts facing the
  room. `scripts/fetch_assets.py` downloads the CC0 scans, `scripts/find_objaverse.py` and `scripts/fetch_objaverse.py` find and fetch CC BY models.
- Credit every CC BY model and every source sheet in `CREDITS.md` beside the plan.
- Check orientation on a grid (`scripts/preview_assets.py`) before placing a new model. Check native size too, since
  Objaverse models come in odd units.

## Speed

A glTF import is the slow step, so `build_house.py` caches each model as a linked `.blend` in the asset library
(`HOUSE_ASSET_LIBRARY`, default `~/house-assets`). Avoid scanned pines and firs: their importer takes many minutes. Grass and trees take long to
sync, so renders keep persistent data between shots. Any step over 5 minutes gets profiled and fixed.

## Done means

Check, overlay and as-built gates pass and are quoted with their numbers. Interior and exterior stills hold up at full
size beside real photos. The report states what was sourced, what was inferred and what still looks weak.
