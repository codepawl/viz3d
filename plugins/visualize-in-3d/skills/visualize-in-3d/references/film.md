# Film craft

Rules learned from fixing real films made with this skill. They apply to every look; the dark documentary look
leans on them most. Reading map: Pacing and text, Camera, Motion, Figures and places, Maps, Sound, Live app films, Checks.

## Pacing and text

- Every caption stays fully visible for at least 1.2 s + 0.07 s per character, with 0.3 s fades in and out. Compute
  shot lengths from the text the shot carries; a shot cut before its caption can be read is the most common fault.
- Cut hard between shots. Keep dips to black for real breaks in time (three or so in a three-minute film); a fade on
  every cut reads as sluggish and cheap.
- Dates and places go in a short title line above the caption ("29 DEC 1945"), not inside the sentence.

## Camera

- Give each shot its own move: truck, crane, pedestal, tilt, pan, orbit, rack focus. A film where every shot pushes
  in feels like one long zoom. Save the push-in for the one moment that needs it.
- A rack focus must resolve: pull to the subject within about a second and hold it sharp. A shot that stays soft
  reads as a rendering bug.
- Keep figures and key objects clear of the caption area in both layouts (16:9 and 9:16 frame differently).
- Move each camera on a smooth spline through three or more points, never a straight lerp between two. It is already
  moving at the cut (cut on motion, no ease from rest), carries a slight handheld drift, and looks from a hero angle:
  a low macro that tracks the action, an orbit, a crane that rises with what grows, a reveal that cranes down.

## Motion

- Nothing stops dead. A tool eases in, follows through and leaves the frame in an arc before the cut, and a held
  object keeps moving a little. A finished plant or figure keeps a slow sway, and each action overlaps the next.
- Growth starts tiny and swells. A plant is born as a small sprout on its line and grows over 1.5 to 4 s on an
  ease-in-out curve with a soft settle. Small plants lead and big ones follow. An easeOutBack over half a second
  makes things appear at full size at once, which reads as a pop.
- Check motion in a moving clip at full frame rate, not on a contact sheet. Stills hide pops and dead stops.

## Figures and places

- People are flat, emissive silhouettes in one colour per role, with gentle bloom. Limbs and joints are one joined
  shape; visible gaps at elbows, knees or fingers read as broken dolls.
- Seated figures sit on something: chair, bench, bed. Check the seat is under them for the whole shot.
- A figure never vanishes into a wall. Give the building a real door, cut the opening out of the wall (clipping
  planes or a boolean) with a shallow lit vestibule behind it, swing the leaf open before the figure arrives, hide
  the figure only once it is past the threshold, and close the door after.
- An open door shows a room or a hallway behind it, never the wall, glass or window quad the model keeps there. Glass
  sits inside a frame and muntins; a door that is all glass reads as a mistake.
- Vehicles face their direction of travel. Check the model's forward axis once and derive heading from motion.
- Buildings get enough detail to read at the closest shot (trim, sills, chimneys, signage plates), and the one the
  shot is about is outlined or lit in the highlight colour.
- Interiors the story mentions are worth building (a courtroom, an interview room, a ward, a bar): a few block-built
  pieces, two or three practical lights and small moving details (a flickering sign, dust, embers) carry a shot.

## Maps

- Labels sit on dark plates (about 85% opacity, a 1 px light border) so they read over roads.
- Frame each map shot on the marks, routes and labels it is about, with every label inside the frame and a margin.
  Large empty regions mean the camera or the map extent is wrong; extend the map data rather than leave black.
- Routes draw on over time with a soft sound; marks land with a low thump; distance labels tick in.

## Sound

- No constant noise bed. Brown-noise "air", tape hiss and synthesized wind gusts read as an annoying whoosh across
  the whole film. Use quiet real ambience per shot (CC0 recordings from Freesound), fading in and out on cuts, and let
  interiors be nearly silent.
- Footsteps are placed one by one on the figures' footfalls: log the time each foot lands from the walk cycle, slice
  single steps out of a real recording, and align each step's attack to its footfall. A looped walking recording
  never matches the feet on screen.
- Score by section of the story (an opening, a turn, the main event, the aftermath, the end), crossfading over a
  second or two at the section's first cut, instead of one loop under everything.
- Every mouse or keyboard input in a film gets its own small sound: a click, a wheel step, a key press, a drag. The
  recorder logs each input with its frame (`input_events.json`: frame, kind, target), and the sound script places
  one real recording per input and stops with an error on an input it has no sound for.
- Input sounds stay small and soft: a light click, a soft whoosh on a transition, a quiet tick. No hits, booms or loud
  UI blips. Showcase and app films carry a music bed under them, not effects alone.
- No repeated ticks: not one per drag step, not one per counter step. A run of ticks reads as tapping a bowl. A drag
  gets one soft whoosh for the whole gesture, and a counter runs silent under the music.
- An app film's music is upbeat and warm (major key, light groove, plucks or acoustic), even when the story has an
  outage in it. Slow whole-tone or minor drones read as horror.
- Mix to about -19 LUFS (or -16 for a short social cut), true peak under -1 dBFS; sound effects stay audible under
  the music.

## Live app films

- Record with Playwright from a script in the app folder (`record_film.mjs`). An init script replaces
  requestAnimationFrame, performance.now and Date.now with a virtual clock. While assets load, the clock advances by 0,
  then the script pre-rolls the simulation a whole number of seconds and captures one screenshot per 1/30 s step.
  Encode the frames with ffmpeg afterwards.
- The simulation steps only from the virtual clock, never from wall time, so the same seed gives the same film.
  Step CSS animations and transitions with the same clock (document.getAnimations(), set currentTime), and read the
  simulation time at the first captured frame instead of assuming the pre-roll landed exactly.
- Plan the film from the simulation: a small script runs the seed forward and picks the hero unit and the times, so
  the unit you click is moving and on screen at that moment.
- During a follow or a hold, keep a slow real drag-orbit or wheel going. A followed unit that stops (a train at a
  platform) otherwise gives repeated frames. Find them with ffmpeg mpdecimate plus showinfo and fix every gap over
  0.2 s.
- The subject must read at film size: the main moving unit fills at least a quarter of the frame width in the
  opening and the follow beat. Context (a city, terrain) never outweighs the system the film is about.
- When the system is hidden (underground, inside a building, behind a roof), cut it open: a clean section through
  the ground or the walls, with the camera-side scenery removed (semi-transparent buildings read as a muddy wash),
  and real materials on every cut face.
- Card fields match what the 3D view shows at that moment (a train boarding has its doors open in the card too).
- The recording script always records the full length and writes its progress to a log file; a shorter run or a
  piped output can hang and look like a crash.
- Each beat's hero event (a unit reaching a booth, a truck under a gantry) must happen inside its beat. Spawn the hero
  at a fixed simulation time so it lands 2 to 3 s into the beat, and check it on the sheet.
- A plain-words strip carries one short line at a time, on the caption timer above.
- A roof or canopy that hides the action from the camera angle goes semi-transparent (about 30% opacity).
- Fly-to moves own the camera until they finish; a drag during a fly makes the camera jump.
- A beat that shows one stage starts from that stage's camera preset (press its number key or click it in the
  stage bar), so the framing matches the app. Show one speed change on screen (2x or 5x, then back to 1x); the
  virtual clock still advances 1/30 s per frame and the app runs more simulation steps in it.

## Checks

- Make contact sheets of the final encode at a stated fps (`scripts/contact-sheet.sh <video> <folder> <fps>`: 1 for
  a slow film, 4 for action) and look at every sheet. Check the sheet files are newer than the video before
  trusting them; stale sheets hide regressions.
- Before reporting, run the full loop in `self-review.md`.
- Look for: captions cut early, figures under captions, clipped labels, empty map areas, soft shots, floating or
  sunken figures, doors that open onto walls, vehicles backing along their route, black frames at cuts. In a live app
  film also look for: the cursor hidden or off target, UI over the action, selection rings wider than the object, a
  followed unit that never reaches its event, an event too short to see, motion that steps every few frames
  (compare two consecutive frames), and surfaces that flicker or overlap (crop and zoom full-size frames).
- Re-render only the time ranges you changed when the renderer supports it, then re-encode and re-check those ranges.
