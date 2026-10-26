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

## Growing the lists

When the user or the main session finds a fault this loop missed, add it to the matching mode's fault list in the
same turn, with the case. Add it to the generic list above when it can happen in any mode.

## Previews and the final render

Show the user fast previews while the cut is still changing: half size, 30 fps, no motion-blur subframes. Run the
full final render (full size, subframes, master and web copy) only after the user approves the cut.
