# Documentary film mode

For an event, a case or a piece of history told in order: a 2-4 minute film in the dark documentary look (or
another look the subject suggests), made from a fact file, a real map, block-built scenes and flat glowing figures.
It was built first for a 1950s criminal case and then generalized. Reading map: Fact file, Respect rules, Project
shape, Script, Scenes, Maps, Sound, Long-form craft, Render and checks, Passes.

## Fact file

Write `{{WORK_DIR}}/<slug>/facts.md` before anything is built, and build only from it.

- Every fact has a date, a place, a source and a confidence label: `[2S]` two independent sources, `[1S]` one
  source, `[D]` sources disagree (give both), `[SEC]` only secondary or derivative. Prefer dated primary sources
  (newspapers of the day, court records, official reports); archived copies (the Wayback Machine) count.
- Places get coordinates and the source of each; distances say how they were measured (straight line or by road).
- A "do not state" list: popular claims that are wrong or unsupported, so the script never repeats them.
- Quotes only when read verbatim in a primary source; otherwise paraphrase without quotation marks.

## Respect rules

Write them at the top of the fact file and treat them as binding for every pass:

- Victims and their families are people with names and dates, never props. No remains, wounds, weapons in use or
  gore; violence is shown by a red light pool or a red mark on the map, never by bodies.
- No nicknames the press invented to sell the story; the person's name is enough.
- Something only suspected is captioned as suspected or as the official finding ("ruled asphyxiation").
- Keep private family suffering to one plain line.

## Project shape

A Vite + React + React Three Fiber app with a `film.html` page that plays the film on a virtual clock:

- `script.js`: the shot list. Each shot has a scene name, a caption (and an optional title line for date and place),
  a camera for 16:9 and one for 9:16 (`from`/`to` position and target, optional depth-of-field pull), and sound cues
  `[kind, start, duration, gain]`. Shot length is computed from its text (see `film.md`, Pacing).
- `scenes.jsx`: one component per scene, built from blocks and the GLB kit; `Mannequin.jsx` for figures; a map scene
  that draws roads, marks, routes and labels from the data file.
- `tools/film.mjs`: renders frames with Playwright on the virtual clock (both layouts), with `FROM`/`TO` seconds to
  re-render one range; `tools/sfx.py` and a mix step for sound; an encode step for a master and a web copy.

## Script

- Chronological, one idea per shot, 3-7 s each. Open on the place, close on the place.
- A title line carries the date ("29 DEC 1945"); the caption is one plain sentence of fact.
- Every few shots, return to the map to show where the next thing happens and how far it is.
- Plan the camera move for each shot from the list in `film.md` so no two neighbours move the same way.

## Scenes

- Exteriors: the real building types of the period at real size, with trim, sills, chimneys, porches and signage
  plates; the building the shot is about outlined in the highlight colour.
- Interiors the story mentions (a shop, a bar, a courtroom, an interview room, a ward): a few block-built pieces, two
  or three practical lights and small moving details.
- Figures: one colour per role (the subject warm amber, authorities blue, townspeople grey, the person in focus
  white), joined silhouettes with bloom, period clothing shapes; poses for walking, sitting, standing still, carrying.
- Doors open onto a cut-out doorway with a lit vestibule behind it; figures walk through, never into walls.

## Maps

- Road and water lines from open data (OpenStreetMap extracts, national road files such as US Census TIGER/Line) or
  traced from a public-domain historical map of the period; thin light lines on black.
- The map extent covers every place the film names; extend the data rather than leave an empty frame.
- Marks: glowing red X for events, a pin for other places; routes draw on in red; labels on dark plates.

## Sound

Follow `film.md`, Sound: real CC0 recordings for footsteps (placed on footfalls), doors, cars and ambience; no
constant noise bed; a score in sections (for example childhood, losses, the event, the aftermath, the end).

## Long-form craft

Measured on 22 long documentaries of one large channel (2016 to 2025), for films over about 10 minutes. Build methods are
inferred from frames. These are defaults; the user's own rules win.

- Most of what reads as 3D is flat: a scanned page or photo on a tilted plane, shallow depth of field, a vignette, a dolly of 6
  to 12 s. Only the biggest films had built environments. Spend modelling on 2 or 3 anchor scenes that return, and make every
  document a tilted plane first.
- One accent colour on a charcoal ground. Any other colour has one fixed meaning for the whole film.
- A highlighter wipes over a phrase as the voice reads it (multiply plane, reveal uniform along `uv.x`). Blur everything but
  the line that matters.
- Maps: a dark base, a route that draws on, chip labels with a leader line. The same framing returns with the route longer.
- People are flat silhouettes coded by role, with no built faces; real faces appear only in archive photos.
- Put evidence side by side so viewers can compare by eye. These comparisons, turns in the story, chilling small details,
  quotable thesis lines and chapter starts are where most-replayed peaks sat. Lists without a person sat in the dips.
- Motion: stills drift 1 to 3% over about 5 s; a 3D shot holds 1.5 s and then moves. Typed text runs 30 to 70 characters per
  second, faster than the voice. A quote card builds in about 1.9 s inside a gap in the voice. A long quote lights word by word
  from the transcript's word start times (31 words within about one frame); a shorter one fades in phrase by phrase.
- Evidence the viewer can hear or read for themselves holds the most-replayed peaks on three comparable channels: real audio,
  a message read in full over a card held 30 s or more. Replace shock adjectives with counts and understatement.
- Sound: music starts before the voice (median voice entry 13 s). Voice sits 13 to 16 dB over music, whole mix -16 to -18.5
  LUFS. On a heavy transition the music or hit jumps 0.25 to 0.65 s before the picture changes, after a dip of 0.75 to 1.9 s.
  Before a reveal: fade down, 1.2 to 3.2 s of silence, a hit, then the text, only a few times a film. Archive audio is
  band-limited to about 300 Hz to 4 kHz with on-screen text, over a bass bed.

## Render and checks

- Render both layouts, mix, encode, then make contact sheets and open every one. Check against `film.md`, Checks,
  and against the fact file: every caption must match a fact and its confidence.
- Fix in one round, re-render only the changed ranges, and check those ranges again.

## Passes

1. Research and fact file (no code).
2. Map, scene kit and figures, with a contact sheet of every scene.
3. Script, cameras, sound and the full render.
4. Review against the fact file and `film.md`; one polish pass.
