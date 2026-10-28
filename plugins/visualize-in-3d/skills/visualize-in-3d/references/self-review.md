# Self-review loop

Every pass that produces something to watch (an app, a film, a documentary, an action short) runs this loop
itself before it reports. Run up to three rounds. The goal is that the main session and the user find nothing a
measurement or a look at the frames could have found.

## Each round

1. **Measure.** Copy `{{SKILL_DIR}}/scripts/frame-guard.js` into the project. In the frame function, log
   `measureSubjects` for each thing the viewer must follow. Examples: actors, the selected unit, a moving vehicle,
   a figure. List smoke, steam, beams, captions and panels that can cover them as occluders. After a fast draft
   render, run `findFaults` and fix every fault outside an `allowed` window (a planned exit, a cut to another place).
2. **Look.** Render a fast preview (half size, 30 fps, no motion-blur subframes) and make timestamped frame sheets:
   `bash {{SKILL_DIR}}/scripts/contact-sheet.sh <film> <sheet folder> 4` (the last argument is frames per second;
   use 4 for action, 1 for a slow documentary). Look at every sheet in order, then at full-size stills of each peak
   moment (a hit, a reveal, a click result, the last shot), cut with `ffmpeg -ss <time> -i <film> -frames:v 1
   <png>`. An app also gets screenshots at the real window size.
3. **Judge.** Check the film against:
   - the plan file: a viewer reads every beat or feature it promises at phone size, without a caption
   - the fault list of the mode (`film.md` Checks, `action.md` Faults seen, `brief.md` checks)
   - the generic faults below.
4. **Write and fix.** Write the round's findings to `notes/review-<n>.md` with times, fix them, and render again.
   Stop when a round finds nothing new. Report the remaining gaps honestly.

## Generic faults

- The subject the viewer follows leaves the frame or shrinks under about 40 pixels tall.
- An effect or a panel covers that subject for more than 0.3 s.
- A colour, material or texture breaks for a few frames (a flat tint, a missing texture, z-fighting flicker).
- An action or change happens off camera, or too fast to read at the playback speed.
- Weak motion: effects, impacts and camera moves too small to read on a phone.
- The ending is small, far away, cut early or covered.
- Programmer art: a placeholder box, a default material or a model from memory where a real one belongs.
- Stale outputs: sheets or stills older than the film they claim to show.
- Ghost copies of the whole frame: a camera shake or jump that differs between the motion-blur subframes of one
  frame. Camera offsets are set once per output frame.
- A colour cast added by the encode grade: compare one raw render frame with the same frame of the encoded film. Run
  `eq` and `vignette` on YUV and the blend on gbrp. An `eq` on gbrp frames before a screen blend turned a whole film
  purple.
- A cut that leaves part of the scene standing: a custom ShaderMaterial ignores `clippingPlanes` unless its shaders
  include the clipping_planes chunks. Shoot every cut view and look for water, sky domes or effects left in front of
  the section.
- A surface that looks right headless and wrong in a real browser (a moat gone white from sky reflection). Check the
  published page in Chrome at the default hour before reporting.
- Too many controls on an interactive page: panels in several corners, labels on every object at once, controls over
  the subject. Use one dock at the bottom, one menu open at a time, and labels only for the current step. A phone card
  must leave the subject in view.
- A symbol in the frame centre: an emblem at the vanishing point, or wall parts that line up into a cross. A statue's
  raised arm can also read as a salute. Check every documentary shot about a regime for these.
- A close shot from inside the subject's own clutter: tall dark parts (pylons, racks, masts) fill the frame.
  Nothing reads as one object. Pull back until each part has space around it. In an app film, shrink
  the dashboard so the world fills most of the frame.
- A pop-up page that reads as a greeting card: one flat cut-out on one plane in front of a wall of text. A pop-up
  needs depth layers at different distances, box folds with volume and a scenic backdrop. Its layers rise in a
  staggered order and shadow each other.
- Stiff programmer drawing on painted textures: straight strokes, hard polygon edges, flat fills. Illustrated art
  needs curved, tapered ink lines, soft washes and organic shapes.
- Close-ups that go soft or show only part of the detail. Paint each texture at 1.5 times the texels of the closest
  shot, and draw text at that size. Use maximum anisotropy and frame the whole detail.
- Loud, hissy foley on a gentle action, such as leaf-rustle recordings used for page turns. Keep paper foley soft and
  low-passed under the music, with few snaps, never louder than the beat it marks.
- Stacked sounds on one action, and "magic" stingers: a page turn with a creak, snaps, chimes and marimba at once.
  Use one sound per action, and no wind chimes or sparkle on a reveal.
- Falling water drawn as opaque white sprites or a row of identical streaks. At phone size it reads as foam clumps or
  a barcode. Draw clear falling water as a thin, mostly transparent sheet that catches light on its edges.
  It turns white only where it breaks, and its width varies.
- The main event is missing from the picture while the numbers say it happens: a flood stage that shows dry rooms
  with "46 cm" in the HUD. Shoot every stage and check that the event (water, fire, smoke) is drawn in every
  view, the section view included.
- A state that contradicts itself on screen: corridor lamps and bulbs still lit in a "Blackout" stage. Check every
  light source against the state that should switch it.
- A result or end card drawn translucent over a busy scene, so its text mixes with the rooms behind. A card with
  more than one line of text sits on an opaque surface.
- A cut-away neighbour faded with a coarse dither reads as a ghost polka-dot block. Fade it to a clean low alpha or
  cut it to stub height like the main building.
- A town or site with no streets: houses and cars standing on grass because the layout had lots but no road graph.
  Every built place gets its circulation first (roads with curbs, sidewalks and lane paint, driveways, yard paths),
  and every vehicle drives on it.
- A map layer toggle that draws nothing readable: thin world-width lines vanish at overview zoom. Shoot each layer at
  overview and close, and draw network overlays with screen-space width lines and moving particles.
- Dark puddle ellipses scattered on grass read as holes, and street-lamp light pools drawn as huge orange discs.
  Puddles only on paving, few and sky-reflective; a lamp pool about the lamp's height in radius.
- Vehicles that ignore the ground and the road: a car keeps its flat height and yaw on a hill, so it sinks into the
  slope going up and floats going down, or points off the lane. Sample the ground under the front and rear axles every
  frame, set height and pitch from them (and roll from both sides), yaw from the lane tangent, wheels spinning with
  distance; check the gap at each wheel on the steepest road (under 5 cm). A site also needs believable traffic
  density for its size, not a handful of cars.
- Bare ground in the frame: neighbours cut low so the subject stays visible leave a flat empty field behind them.
  Put a next row of full-height buildings behind the subject (behind it as seen from the camera, so it hides
  nothing) with facades turned toward the camera, never plain rear walls, then low plots out to the distance fade.
- A transition clip played on loop: a "sit" clip that is really the sit-down motion stands people up and sits them
  down every cycle. Check each clip's first and last root pose; a clip that ends in a different pose plays once and
  holds its last frame, or the model gets a separate held pose.
- A result card or toasts over the last beat of a film that should end on the world itself. End on the simulation
  unless the plan asks for a card.
- A silent input: a click, wheel step, key press or drag in an app film with no sound on its frame. Check the
  recorder's input log against the cue list.
- A flashlight beam drawn as a straight translucent cone: hard edges, even brightness, frozen in the hand. Draw it
  from the lens, fade it along its length and toward its edge, add faint haze noise and motes, and let the hand drift
  a little. Guard the shader against NaN (pow of a negative, normalize of zero): one NaN pixel through bloom turns the
  whole frame black.
- Rain that falls as one uniform slant: every streak tilted by the same wind vector, same length and brightness. Keep
  rain near vertical, give each drop its own lean, speed, length and brightness, and let gusts move across the scene.
- A rain bed that hisses, sounds dull or rings. A distant rain wash is a band of hiss, low-passing it sounds cheap,
  and offset copies of a mono bed comb-filter into a ringing room. Pick a close recording whose energy sits mostly
  at 250 Hz to 4 kHz at a steady level, measure its band shares before mixing, and keep it quiet under the cues.
- Sound tails that read as reverb in fast stretches (a howling wind bed, a clank left ringing, a thunder with a long
  fade) and a low tone under the whole film (a bed whose loudest band sits at 80-250 Hz). Keep wind thin, cut one-shots
  to their dry attack, drop ambience with no picture event, high-pass rain near 500 Hz and water near 150 Hz.

## Growing the lists

When the user or the main session finds a fault this loop missed, add it to the matching mode's fault list in the
same turn, with the case. Add it to the generic list above when it can happen in any mode.

## Previews and the final render

Show the user fast previews while the cut is still changing: half size, 30 fps, no motion-blur subframes. Run the
full final render (full size, subframes, master and web copy) only after the user approves the cut.
