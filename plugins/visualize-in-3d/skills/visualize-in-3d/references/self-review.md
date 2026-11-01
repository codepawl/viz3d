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

Reading map: read "Every film" always, then only the groups that match what you built. Groups: Every film; Camera and framing; Apps and UI; Books and illustrated plates; Motion and physics; Vehicles, roads and terrain; Weather, light and water; Sound; Documentary screens and evidence; Game.

### Every film

Read always.

- A model that breaks into scattered shards after a mesh decimation pass, while its code is unchanged. Shoot every decimated model and compare it with the original; if a code revert does not fix a broken model, restore the original file first (Ironbay's scissor lift at ratio 0.05 came out as loose plates and floating debris, and a worker hunted it in the code).
- A decimation target or a re-export that makes the file bigger than the original compressed one (the same lift grew from 11 MB to 32 MB, without meshopt).
- Whole frames go dark in a repeatable run while the camera pose and the sim are valid: a few NaN pixels spread by a bloom or AO blur. Render that frame with the composer off and read the scene buffer for non-finite values. In Ironbay the source was zero-length vertex normals in the glbs, which become NaN only when lit. Repair them on load instead of clamping the blur.
- A framing number measured by a separate still script while the film's own path moves the camera differently (Ironbay's V8 measured 271 px on stills and never appeared in the film, because a car click turned on follow). Measure on frames from the film's own path.
- Physical realism, checked on consecutive frames as well as stills (An, 2026-11-01, on four SimReady films): an object with no support, a load lifted with no contact or carrier (a forklift raising a beam), a warning light floating in the air, an effect no physics would make, a tool tip off the tube it works on (measure tip to surface in mm), or a vehicle too big against a real door and desk.
- A light shown as a visible cone or beam mesh. Light reads through what it falls on: a pool on the floor and objects that changes as the light arrives, and looks better than the cone did (An, same day).
- A beacon or lamp placed by a typed-in height beside a model, not read from the model. A robot beacon at a fixed y floated next to its mast, and it hid in stills where the mast overlapped it. Read the mount point from the model's vertices and turn it with the unit's heading.
- A strip laid behind a vehicle whose end drifts away from it. Position by a curve's parameter and draw by arc length disagree on an ellipse: the boom's end ran ahead of its robot. Resample the path evenly by length, and give the strip a source on the vehicle (a reel that shrinks).
- A light with no source on screen: a soft lamp added to lift a dim subject, or a point light offset 1.5 m off a wall fitting. Move a real fitting so it lights the subject and aim it, with a shadow.
- A camera flown in a straight line between shots (2026-11-01, office night shift: "lượn mượt mà chứ k phải đi xuyên đồ vật"). Fly a curve that rises above the tallest object between two low views, log the distance from the camera to every mesh box each frame with a no-draw dry run, and read the count of frames under 0.25 m.
- A cone removed with nothing in its place (same film: "máy scan máy tính nó còn k hiện cái beam"). A working beam stays visible as one thin soft ray fading with distance, landing on a line that moves on the thing it scans.
- A prop whose body is open where you mounted something. A lamp and a tow bar at typed-in positions hung in air because the robot was a flat base with two side racks (2026-11-01, office night shift), and a stock model mop stood upright touching nothing. Check part bounds at the mount height, then crop a frame.
- A bright streak on a floor or a spark on steel near a fire, in no reflection any viewer expects. A flame's point light glints on anything polished, and a model's roughness map can keep a surface polished after its `roughness` value is raised. Drop the map on walls and slabs, and keep mirror reflection to the wet patch.

- Moving parts that clip into static ones: a vehicle or rail passing through a tool, a support post through a machine. Measure the clearance in code from the model bounds and require it above zero before looking at frames (Session Fab, 2026-10-31: OHT legs sunk through tool roofs and An called it glitching).

- A refine or remake of a film is shown before it stands next to the old film, frame against frame at the same moments. Better parts do not count if the whole film reads worse (An, 2026-10-30: "sao nó tệ hơn trước vậy").
- "More realistic" came out as dirt: blotchy tiled ground filling the frame, stains on the skin, grey gloom, over-reflective glass. Realism comes from shape, clean light and soft shadows; keep the stage calm and bright unless the subject asks otherwise.
- The camera hides what the step is about: a lowered flap seen from above and ahead sits behind the wing and only its track fairings show, as spikes. Film a moving part from the side where it moves into view.
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
- Corners and far walls turning white in a dark scene while no mesh is there: a contrast post effect pushes near-black values below zero, and the next effect turns them bright (2026-11-01, factory fire). Remove `BrightnessContrastEffect` and grade with lights and tone mapping. Test by screenshot; `readPixels` reads the wrong framebuffer behind a composer.
- A colour cast added by the encode grade: compare one raw render frame with the same frame of the encoded film. Run
  `eq` and `vignette` on YUV and the blend on gbrp. An `eq` on gbrp frames before a screen blend turned a whole film
  purple.
- A beat that renders empty or wrong only when the render runs into it from the beat before. The cause is state
  (opacity, visibility, near plane) set inside one beat's branch and never reset: a vanished cabinet stayed invisible
  through the next shot. Reset such state on every frame. After any partial re-render, sheet the whole film at 1 fps
  before sending, not just the spans you changed.
- A result card or toasts over the last beat of a film that should end on the world itself. End on the simulation
  unless the plan asks for a card.

### Camera and framing

Any shot with a moving camera.

- A camera that passes through objects or turns abruptly (An, 2026-11-01: "camera biết lượn mượt mà chứ k phải đi xuyên đồ vật"). Fly a smooth curve, and measure the camera's distance to every mesh's bounding box on each frame, including the moves between shots. Any frame inside a box is a fault.
- A symbol in the frame centre: an emblem at the vanishing point, or wall parts that line up into a cross. A statue's
  raised arm can also read as a salute. Check every documentary shot about a regime for these.
- A close shot from inside the subject's own clutter: tall dark parts (pylons, racks, masts) fill the frame.
  Nothing reads as one object. Pull back until each part has space around it. In an app film, shrink
  the dashboard so the world fills most of the frame.

### Apps and UI

- A click mark that lands beside its target (An, 2026-11-01: "điểm chọt bị lệch vào các ống phẫu thuật"). Project the target's world position to the screen on the click frame, and put the mark on that point. Check small targets at full size.
Interactive apps, dashboards and their films.

- The film spends its time dragging the time scrubber. Allow one short drag at most; the cursor works inside the world: hover, click a machine, follow a unit (An, 2026-10-31).
- A moving unit gives no sign of where it is going, or a machine's state cannot be read at a glance. Draw each unit's path along its real route, and give running, idle and fault marks of different shapes, all from sim state (An, 2026-10-31).
- A stretch of more than about 2 s where the cursor and camera hold still while the script waits for the sim. Speed it up in the edit or wait before recording starts (Session Fab round 3 waited 5 s for a walker).
- A sound cue for an event that is off screen. A sim's event log covers the whole site, so check each cue against the frame at its time.
- A close-up that lands after the action it came for. Trigger the click on the sim's work (first stroke laid, tool on the surface), not on the phase starting, and start it from a pick test so a click on a target behind a moving unit does not select the unit (Paint Studio t1: three wrong selections, knife close-up on nothing).
- Two materials from one patch function look identical: three.js shares a program when `onBeforeCompile` source matches, so a variant silently renders the first one's shader. Give variants a `customProgramCacheKey` (Paint Studio: the wooden palette read flat brown for hours).
- A step that generates paid assets from a copied script: check the prompts it will send before running, since a text patch can miss on CRLF and generate the old subject (Paint Studio: 20 forklift sounds and 2 music tracks wasted).

- Too many controls on an interactive page: panels in several corners, labels on every object at once, controls over
  the subject. Use one dock at the bottom, one menu open at a time, and labels only for the current step. A phone card
  must leave the subject in view.
- A cut that leaves part of the scene standing: a custom ShaderMaterial ignores `clippingPlanes` unless its shaders
  include the clipping_planes chunks. Shoot every cut view and look for water, sky domes or effects left in front of
  the section.
- A surface that looks right headless and wrong in a real browser (a moat gone white from sky reflection). Check the
  published page in Chrome at the default hour before reporting.
- The main event is missing from the picture while the numbers say it happens: a flood stage that shows dry rooms
  with "46 cm" in the HUD. Shoot every stage and check that the event (water, fire, smoke) is drawn in every
  view, the section view included.
- A state that contradicts itself on screen: corridor lamps and bulbs still lit in a "Blackout" stage. Check every
  light source against the state that should switch it.
- A result or end card drawn translucent over a busy scene, so its text mixes with the rooms behind. A card with
  more than one line of text sits on an opaque surface.
- A cut-away neighbour faded with a coarse dither reads as a ghost polka-dot block. Fade it to a clean low alpha or
  cut it to stub height like the main building.
- A map layer toggle that draws nothing readable: thin world-width lines vanish at overview zoom. Shoot each layer at
  overview and close, and draw network overlays with screen-space width lines and moving particles.
- A time scrubber that moves the numbers but not the world (An, 2026-10-29, Session Fab: "chỉnh mốc thời gian mà
  trên không gian k thay đổi j, hầu như đều tuyến tính"). Show the data's real rhythm in the scene: quiet days empty,
  peaks packed, areas rising and falling at different times. Shoot a quiet, a normal and a peak position side by side;
  they must differ at a glance.
- A tool that misses what it works on (An, 2026-11-01, operating room: "điểm chọt bị lệch", up to 39 mm off a cannula 18 mm wide). Blending poses joint by joint swings the end off its contact even when both poses are right. Log the end's distance from its target in millimetres on every frame of the film's own path, and hold the end on the target with the rig's own joints each frame.
- A spot light placed at a lamp's centre, shadowed by its own housing, so the room is lit but no pool lands (2026-11-01, operating room). Start the light in front of the glass and check that the pool falls on the subject.
- A cross on the floor from a reflection blurred along two directions with a very bright point in it (2026-11-01, operating room). Cap samples before the blur.
- A real place that reads as sci-fi or cluttered (An, same day: the fab "k giống cái factory thật lắm, hơi scifi và
  khó nhìn"). Check against photos of the real place before shooting: real proportions, its own colour cues, fewer and
  larger elements, nothing decorative, readable at 1280x720.
- A film a stranger cannot read in two seconds (An, 2026-10-29, Claude Code Factory: "nhìn sơ qua video thì chưa thấy
  và hiểu được gì"). Small realistic people, identical stations repeated down the hall and a close camera hide the idea.
  Use big friendly units in the subject's own brand colours (a mascot-like bot for software), a different station
  design per role with a label sign, the links between stations drawn by their real volume, and open on the full
  overview.
- A click in a film that lands on the wrong thing or on nothing (2026-10-31, warehouse: the camera stayed on a forklift
  after clicks meant for a line and a dock, and another forklift's hit box caught a third). Read the selected unit after
  every scripted click and fail the take on a mismatch. Give the app a real way back to the overview for the cursor to use.
- A half-size draft that fails or misleads because the HUD is in fixed pixels (2026-11-01, operating room: at half viewport a read-only strip sat on the click point and took the click, and the HUD looked twice its final size). Read-only panels get `pointer-events: none`; judge HUD size and overlap on a full-size frame.
- A camera flight whose straight line runs through the unit in the middle of the room (2026-11-01, operating room: a frame filled by a white column on the way to the console). Bend the flight around the unit and test the whole curve against every mesh's box when the flight starts.
- A flight that stops at the overview and leaves the other way (2026-11-01, operating room: clean clearance of 373 mm, yet a 146 degree turn over 1 s, 9.3 m/s and a 29 m/s2 jolt at each end). Clearance alone misses this: also measure speed, per-frame acceleration, look rate and the turn over a 1 s window, which sees a stop-and-reverse that a frame-to-frame angle skips. Use a fifth-order move that starts from the present velocity and acceleration, and let the next click land in flight. Then check the clicks again, because the next target may still be out of frame.
- A click planned from a world point that is off screen or behind a unit with higher pick priority (2026-11-01, factory fire: five of eight clicks in the first dry run). Run the recorder once without saving frames, choose each click point from a grid over the unit's box by asking the app what it would pick there, and stop the take at the first mismatch instead of finding it after a long render.
- A close-up that lands on an idle unit or behind a prop (same film: an empty belt, an empty dock, a forklift hidden by
  its rack). Give each kind of unit a view that shows its work, and search the seed for the pre-roll where each unit is
  busy on the second it is on screen, instead of hoping a live sim obliges.
- Work overlays left on after the work ends (2026-11-01, office night shift: route lines and markers on the floor at 08:00). Tie them to the same state the clock announces.
- A mechanism too thin to read (same film: a carton on a rod, a scan arm crossing a chair back). Widen it to a real tray or rail and route it above the furniture. Check a crop before accepting a reader's "floating": both arms were attached.

### Books and illustrated plates

Pop-up books, cutaway plates, painted textures.

- A pop-up page that reads as a greeting card: one flat cut-out on one plane in front of a wall of text. A pop-up
  needs depth layers at different distances, box folds with volume and a scenic backdrop. Its layers rise in a
  staggered order and shadow each other.
- Stiff programmer drawing on painted textures: straight strokes, hard polygon edges, flat fills. Illustrated art
  needs curved, tapered ink lines, soft washes and organic shapes.
- Close-ups that go soft or show only part of the detail. Paint each texture at 1.5 times the texels of the closest
  shot, and draw text at that size. Use maximum anisotropy and frame the whole detail.

### Motion and physics

- A vehicle route that crosses props (An, 2026-11-01: "xe khoanh tròn xe mà đi xuyên mấy cái thùng"). Check the vehicle and its load against every prop on each frame. Any overlap is a fault, so move the route or the props.
- An item that moves by itself to the gripper before the pick (An, 2026-11-01, on the dark store: "cái chai ... tự di chuyển tới vị trí của cái móc"). The gripper travels to the item and touches it first, and the item then moves only while attached to a carrier.
- A lift or mast that overshoots and comes back: the item is level with the bar, but the bar jumps higher and slides back down (An, same day: "đơ đơ phi logic"). Plan one monotonic move to the pick height with acceleration and deceleration, and log height against time: a pick has 0 reversals before it reaches the item.
- A device sunk into the surface that holds it (An, 2026-11-01: "máy báo cháy dính vào tường"). Mount it the real way: its base touches the surface and its body stays outside.
- Spilled liquid that vanishes when the flow stops (An, 2026-11-01: "k giữ mấy cái trail còn lại mà lại xoá hết nước"). Stop only the flow. Pools and trails stay, then dry or drain over time.
- A load or part that moves with nothing carrying it, and a thing that hangs with no support (An, 2026-11-01: "forklift kéo thanh đỡ lên cao k cần điểm tựa", "đèn báo lơ lửng giữa không trung"). For every moving load and every prop above the floor, name what holds it and show that contact in frame: forks under the beam, a pole or wall bracket under the lamp. No named support is a fault, and effects that break physics are faults too.
- A vehicle too large for its room (An, 2026-11-01: "mấy cái xe nhìn bự dữ"). Measure each vehicle against the door and a person in the same frame, using the real dimensions.
- A seeded sim that plays a different night in Node and in the browser, so a shot plan misses (Nightshift, 2026-11-01). A sort with a random comparator gives a different order in each engine. Shuffle with a seeded Fisher-Yates, and run the same night in Node and Chromium once to compare.

Anything that walks, crawls, drives or is simulated.

- A thin object resting on a surface that sinks into it or z-fights: a curled sheet of paper whose middle passes
  through the desk read as see-through (An, 2026-10-29). Run the contact check (`measureContacts` in
  `scripts/frame-guard.js`) on every frame for each object that rests on another; a vertex below the surface or
  within the z-fight gap is a fault.
- A character merged with what it lies on or under: a body sunk into a mattress and a sheet passing through it (An,
  2026-10-29, "mền và model người nó bị dính vào nhau"). Lay the body on the surface with the contact check (sample the
  skinned vertices), and drape a blanket over it by shrink-wrapping a cloth grid onto the body and mattress with a
  small offset, never a fixed shape that intersects.
- A change the viewer cannot read: an empty corner meant to say "the machine vanished" looked like "the machine was
  smashed" (An, same day). Show the before and the after in the same framing, so the change itself is on screen.
- A light effect that reads as a prop: a visible red beam cone under a small EXIT sign looked odd. Small practical
  lights get a glow on the wall and floor, not a volumetric beam.

- A transition clip played on loop: a "sit" clip that is really the sit-down motion stands people up and sits them
  down every cycle. Check each clip's first and last root pose; a clip that ends in a different pose plays once and
  holds its last frame, or the model gets a separate held pose.
- A legless body that wiggles on a clock: a time-based wiggle on a follow-the-leader spine reads as flapping. Push side to side in proportion to speed (a serpenoid path driven by distance travelled), with no sideways slip and no motion at rest.
- A creature that goes through objects or moves in lockstep with its neighbours: bodies must follow the head's path, climb objects and each other with capped layering, and carry seeded per-creature randomness (wavelength, amplitude, speed, hesitation).
- A propeller or wheel that looks still in the film (An, 2026-10-29, Factory Clawds: "chong chóng tre nó k xoay").
  A two-blade rotor that steps near 90 degrees per frame aliases to frozen. Spin it at 25-35 degrees per frame, add a
  faint blur disc, and make the blades thick and light enough to read at phone size.
- Flying units that pass low over signs and stations and cover them (same day). Rise vertically, cruise above the
  tallest object, and descend vertically into an open spot. Paint station names on the floor like the belt labels
  instead of on floating sign cards, and keep landing spots off that text.
- A figure that glitches while it reaches (An, 2026-10-30: "con người nó cứ bị glitch"). A solver that answers each frame on its
  own can land on another pose in the next frame. Bake its answers, hold and smooth them, play them back by time, and fail the
  render on travel per frame (above about 12 cm for the pelvis or 22 cm for a hand at 30 fps). Also smooth facing across a path's corners.
- A hand that floats near what it holds (An, 2026-10-30: "k cầm vào cái cạnh tủ mà lại lơ lửng"). Every hold, pull or
  turn gets a socket on the prop, a contact on the hand, two-bone IK and a registered grip: `registerGrip` / `measureGrips`
  in `scripts/frame-guard.js` fail the render above 1 cm. Then look at the shot: an arm that cannot reach makes the body lunge.
  Measure the torso against the prop per frame too: every grip passed while the reach solver walked a chest 17 cm into a cabinet. Use the
  hand on the prop's side, and read a solver's largest reach: a value at its cap means it failed. A held prop rides the hand (`carryProp` in
  `scripts/human-arm.js`); only rails or a slot may lead it until it clears them. Hold things upright in the fist, palm on the long side.
- A hand that touches but is bent like no hand can bend (An, 2026-10-30: "hướng tay cầm bị dị dạng ... giới hạn tay chân, cách cầm
  thoải mái theo khớp gân"): the grip took its whole rotation from the prop, wrist at 149 degrees, and the palm axis had been
  written backwards. `scripts/human-arm.js`: read the palm axis off the finger bones (where they curl, where the thumb sits) and never
  assume it. A socket says only what the contact fixes (palm normal on a face, thumb side along an edge); the hand takes the rest
  from the forearm and is clamped to the comfortable range. `keepArmInRange` is the last stop on every posed arm, stock clips too.
  Fail the render on the anatomical range: elbow 0-145, pronation 80, supination 85, wrist flexion 80, extension 70, radial 20,
  ulnar 30. `scripts/arm-audit.mjs` lists every fault in a film without capturing. Look at each grip with a lit close camera,
  because a black figure hides this. Ask what holds the prop up: a palm on one side of a box holds nothing, so wrap an edge, or
  put fingers behind and the thumb in front. And which side of a door or panel the body is on before choosing push or pull.
- Props that collide by keyframe (a book shutting through its cover). Bake a rigid-body sim in Blender and play the
  transforms back by time, with a per-frame gap probe; the film stays in three.js.
- Units that stand still while idle or working (An, 2026-10-29, Factory: "lúc nó idle hay làm việc thì nó k có tương
  tác gì, nhìn nó bị nhạt"). Give each role its own readable work loop with the station's prop (typing, page turns,
  scanning with a magnifier), idle fidgets out of sync (bounce, look around, turn to a neighbour), and a small payoff
  when a task ends. Moving units also leave a path trail, flights included.
- A seated character offset from the seat: Blocky passengers sat 0.26 m back, their torsos inside the seatback (An,
  2026-10-30, "người ngồi trong cabin đang bị lệch so với vị trí ghế"). Measure the seated body against the cushion and
  the backrest's front face, not the seat's bounding box, which includes the seatback and tray.
- A recline that turns the whole part: rotating the whole seat about the floor tipped it forward (An, same day, "sao tự
  nhiên ghế đẩy ra trước"). Split the moving piece (the backrest out of a one-mesh seat, by triangle position) and
  hinge it where it meets the fixed part; check the hinge angle's sign on a still.
- A soft chain built from dozens of tiny rigid physics links: it is unstable (in Unreal Chaos, links of about 2 cm exploded on the first tick and force-driven chains flew apart). Drive the motion kinematically and use physics only for contact.

### Vehicles, roads and terrain

Built places, traffic, ground.

- A vehicle that corners with its front wheels straight, stutters through a turn, or drives backwards when the real one would not (An, 2026-11-01, airport ramp film: "nó cua là nó k chuyển bánh với lại cua bị lag z, với lại có xe đi ngược nữa"). Research how the real vehicle and operation run first. Measure heading against velocity, steering angle against path curvature, wheel rotation against distance and frame-to-frame jumps.

- A town or site with no streets: houses and cars standing on grass because the layout had lots but no road graph.
  Every built place gets its circulation first (roads with curbs, sidewalks and lane paint, driveways, yard paths),
  and every vehicle drives on it.
- A vehicle that could not do what the story asks: a quadcopter docking with an airliner at cruise (An, 2026-10-30:
  "nó bay k kịp so với tốc độ máy bay này"). Check speed, range and size against the real class before modelling;
  a 900 km/h rendezvous needs a fixed-wing drone that matches speed and a capture rig.
- A vehicle that pops between cuts: the drone rose straight out of the bay across a cut (An, same day, "0:14 drone
  nó bị glitch"). Drive arrivals and departures on one continuous clock across the cut, and let a departing vehicle
  leave the frame fully before the next shot.
- Vehicles that ignore the ground and the road: a car keeps its flat height and yaw on a hill, so it sinks into the
  slope going up and floats going down, or points off the lane. Sample the ground under the front and rear axles every
  frame, set height and pitch from them (and roll from both sides), yaw from the lane tangent, wheels spinning with
  distance; check the gap at each wheel on the steepest road (under 5 cm). A site also needs believable traffic
  density for its size, not a handful of cars.
- Bare ground in the frame: neighbours cut low so the subject stays visible leave a flat empty field behind them.
  Put a next row of full-height buildings behind the subject (behind it as seen from the camera, so it hides
  nothing) with facades turned toward the camera, never plain rear walls, then low plots out to the distance fade.
- Dark puddle ellipses scattered on grass read as holes, and street-lamp light pools drawn as huge orange discs.
  Puddles only on paving, few and sky-reflective; a lamp pool about the lamp's height in radius.

### Weather, light and water

Rain, water, beams.

- A light beam that reads as a cone object (An, 2026-11-01: "k làm lộ là cái object cone nữa"). Show light by what it lands on: a pool on the floor and objects that brighten as it reaches them. Any visible cone edge, flat fill or hard tip is a fault. Removing the beam is also a fault when the action needs it (An, same day, on a scanner: "còn k hiện cái beam"). Keep a thin beam that fades with distance, plus the light on its target.
- A beat about weather with no weather in the sky: a reroute card said "storm cell ahead" over clear clouds (An,
  2026-10-30, "storm mà sao trong environment lại k có hiện bất kỳ storm nào"). Put the hazard on screen where the
  camera looks (a cumulonimbus tower with lightning lit from inside), and move it in frame as the vehicle avoids it.
- An avoidance where the obstacle moves instead of the vehicle: the storm slid aside while the plane held still in
  frame and the clouds stood still (An, 2026-10-30, "sao né bão mà bão lại tự né nhỉ"). Fix the obstacle in world
  space, turn and bank the vehicle against a camera that does not turn with it, and keep the ground or clouds
  scrolling so speed reads. Place the obstacle so it passes beside the vehicle inside the shot: r6 left the cell 13 km
  ahead on the turn side, so it barely moved in 4 s and the plane still looked headed into it ("chưa thấy né").
- An object that appears with no visible mechanism: a dinner rose out of a console with no hatch or lift (An, same
  day, "đồ ăn từ đâu hiện ra từ dưới lên"). Show the opening, the platform and the moving part before the object.
- A hand-off nobody sees: the meal vanished from the lift and reappeared on the robot, hidden under its head (An,
  2026-10-30, "con robot phải lấy rồi mới đưa đồ ăn cầm theo"). Show the reach, the object moving across, and the
  carrier holding it in view on the way; frame the hand-off side-on or from above, not behind the carrier.
- A part that overhangs its housing: a lift hatch ran 9 cm past the console's end, so the sinking tray clipped the
  console face, and a lamp floated off the end (An, same day, "đồ ăn nó bị dính vào tường"). Check every opening
  and fixture against its housing's box.
- A cover under the body: a duvet thinner than the sleeper and set at mattress height sat inside her (An, same day,
  "cái mền đắp sao lại ở dưới thân"). Measure the body's top and put covers over it.
- A device that moves into a face: a tablet arm swung to the reader's head (An, same day). Reach to the hands or
  lap, and put controls where the person can reach them (the reading light in the seatback ahead, tapped on).
- An ending that cuts on the climax: the film stopped 3 s after touchdown (An, 2026-10-30, "khúc cuối hơi cục, để cho nó
  đáp một đoạn nữa rồi hết vid"). Let the action finish and settle (rollout to a stop, a held beat), then the end title,
  placed where it does not cover the subject.
- A beat moved in the cut keeps its old lighting: check a re-cut shot against the clock and time of day around it, and
  sample between lightning flashes as well as on them, since a flash hides a storm that is invisible the rest of the time.
- A feature shown as one on/off moment: the seat device only toggled a lamp (An, 2026-10-30, "nên hiện scene tương tác được,
  hiển thị sự tiện lợi và tân tiến"). Show the control itself in use, with its values changing and the real thing answering.
- A camera inside a character: seats this close put an over-the-shoulder camera inside the head. Go first person and hide the head.
- An AI action people would not expect for the moment: for a sleeper the "air off her face" vent read as odd, and
  a body tilted against its reclining seat looked pushed up (An, same day, "t tưởng đắp gì lên mắt"). Pick the
  action a real passenger knows (an eye mask, the seat, the shade, the light) and keep the body moving with the seat.
- Falling water drawn as opaque white sprites or a row of identical streaks. At phone size it reads as foam clumps or
  a barcode. Draw clear falling water as a thin, mostly transparent sheet that catches light on its edges.
  It turns white only where it breaks, and its width varies.
- A flashlight beam drawn as a straight translucent cone: hard edges, even brightness, frozen in the hand. Draw it
  from the lens, fade it along its length and toward its edge, add faint haze noise and motes, and let the hand drift
  a little. Guard the shader against NaN (pow of a negative, normalize of zero): one NaN pixel through bloom turns the
  whole frame black.
- A jump scare nobody planned: a level jump of more than about 12 dB within a second, usually near silence before a hit.
  Print half-second levels of the final mix; do not trust a cue's own check, which passes because the hit is loud.
- Rain that falls as one uniform slant: every streak tilted by the same wind vector, same length and brightness. Keep
  rain near vertical, give each drop its own lean, speed, length and brightness, and let gusts move across the scene.

- A dark scene that breaks into hard pure white and black shapes, with speckle at their edges, while the raw HDR image has no bad pixels (Nightmart, 2026-11-01). A contrast effect after tone mapping pushes near-black below zero, and the sRGB encode turns a negative into NaN. Clamp to zero after every grade step, and read the raw target for NaN and negatives before blaming lights or materials. A dark clear colour shows it as a whole white background.
- Ground outside a building reading as a lit tan floor through a door (Nightmart, 2026-11-01). Point lights without shadows shine through walls, so the door lamp inside lit the alley. Give what lies outside a material that takes no lights, with its lamp pools painted into a light map, and check it with the door open.
- An item that moves before its carrier touches it, such as a bottle that slides over to a hook and then gets lifted (An, 2026-11-01: "tự di chuyển tới vị trí của cái móc ... phi logic"). The carrier travels to the item, touches it, and the item is fixed to the carrier for its whole path. Set it down on its place instead of blending it there. Log the gap between the carrier and the item at each grip and each release; it must be about 0.
- A machine axis that jumps above its goal and comes back, or stops dead (An, 2026-11-01: "thanh forklift nó tự nhảy lên cao hơn, rồi lại tuột xuống"). Drive each axis with one planned move with acceleration and braking, pace it with the travel, and log height against time for each pick. Direction reversals between the start and the pick must be 0. A visual trick that changes a part's length to clear a view counts as this fault.
- A view placed relative to a unit that moves sideways, which sends the camera into the facing shelf, or a view where the unit's own frame hides the working part. Place it from the aisle's middle, choose its side from where the part will be, and look at the frames of each new take, since another unit in another aisle can fail where the last one passed.
- A moving part with nothing under it, such as a crossbar above the top of its masts (An, 2026-11-01: "thanh này nó lơ lửng"). Compare the part's highest position with the real bounds of what holds it, and add a mount that goes down to the base.
- A glowing rod or cone standing in for a light or a laser, or a state icon hanging in the air over a machine (Nightmart, 2026-11-01). Remove the mesh and light what it falls on: a small real point light on the goods with a soft spot on the surface. State goes on a lamp mounted on the machine, or on a post that stands on something.
- A camera that flies in a straight line or kinks mid-flight (Nightmart, 2026-11-01). Measure each frame's clearance to every mesh and instance, and the turn and speed along the path, including the flights between shots. Arc the path, ease it with a quintic, and do not run a flight through OrbitControls: its polar limit kicked the camera sideways at 47 m/s. Trail a moving unit through one filter in flight and after it, so landing makes no corner.
- A black disc in a mirror or sky at night, or white blotches on glossy parts (Nightshift, 2026-11-01). The sun in an HDRI can overflow half float into Infinity. Load the HDRI as float and clamp its peak before the environment map is built.
- A wipe or paint trail that does not sit under the thing making it, or vanishes outside the room (Nightshift, 2026-11-01). A canvas texture has flipY on: check the canvas axis against the shader uv by shooting the trail under the robot, not by reading the number that says wiped.
- A floor plane or mirror that runs past the walls: seen from above it shows the sky around the building. Discard it outside the rooms, along with roof plant and posts that stand outside.
- A whole frame washed pale or milky. Split it into albedo, sky and sun before touching materials: pale roofs in a city
  film came from a solid coping box sitting on every roof like a lid, and a milky veil came from light shafts marched
  from the camera instead of from a distance.
- Smoke or steam that starts in mid air, or a plume with nothing under it. Crop each mouth at double size: every plume
  must start at a visible pipe, stack or vent, and all plumes lean the same way.

### Sound

Any film or app with audio.
- Music that measures fine but nobody can hear: many cues keep the duck on and bury the bed. A median cue margin above
  about 12 dB means the music is too low (An, 2026-11-01: "sao của minecraft k có nhạc z" at a 25 dB median, "nhạc còn
  nhỏ" after a first lift, "ok hơn r" at a 12 dB median with cues still at least 6.8 dB clear).
- A generated recording asked for 3 s that is really 0.6 s of sound and then silence, while the picture keeps going.
  Measure each cue's level over time; a long action gets several recordings, not one stretched hope.
- A bright line on the mix sheet is not yet a fault: the spectrogram is log scale. Measure that band per stem first. A
  14 kHz line that looked like a whine was -68 dBFS, inside the music track.

- Loud, hissy foley on a gentle action, such as leaf-rustle recordings used for page turns. Keep paper foley soft and
  low-passed under the music, with few snaps, never louder than the beat it marks.
- Stacked sounds on one action, and "magic" stingers: a page turn with a creak, snaps, chimes and marimba at once.
  Use one sound per action, and no wind chimes or sparkle on a reveal.
- A rain bed that hisses, sounds dull or rings. A distant rain wash is a band of hiss, low-passing it sounds cheap,
  and offset copies of a mono bed comb-filter into a ringing room. Pick a close recording whose energy sits mostly
  at 250 Hz to 4 kHz at a steady level, measure its band shares before mixing, and keep it quiet under the cues.
- Sound tails that read as reverb in fast stretches (a howling wind bed, a clank left ringing, a thunder with a long
  fade) and a low tone under the whole film (a bed whose loudest band sits at 80-250 Hz). Keep wind thin, cut one-shots
  to their dry attack, drop ambience with no picture event, high-pass rain near 500 Hz and water near 150 Hz.
- A silent input: a click, wheel step, key press or drag in an app film with no sound on its frame. Check the
  recorder's input log against the cue list.
- An empty opening: a cold open with only a faint hum or room tone before the music starts. Viewers leave in the
  first seconds. Music plays from the first second; keep true silence for one punch line later in the film.
- A long gap between two music pieces: 7 s of room tone under a documentary punch line read as "empty, boring" (An,
  2026-10-29). Bridge with a drone or a pulse; true silence stays at 1 to 2 s.

### Documentary screens and evidence

Screen recordings, archive pages, documents, titles.

- A screen shown flat and still, filling the frame. Film it as an object: the plane at an angle, shallow depth of
  field on the action, a camera that pans with the cursor or typing and makes eased push-ins to close-ups (An,
  2026-10-29, on a cold open with no zoom and no close-up). Typing, windows and cursor moves each get a sound.
- Evidence as flat frames on black: empty boxes with labels and a red strike read as slop (An, same day). Put the
  papers, photos and objects on a lit desk in 3D, with close-ups and a moving camera.
- A close-up everywhere, or a push-in before the viewer has seen the whole (An, 2026-10-29: "zoom quá nhanh, chưa kịp
  nhìn ở tổng thể"). Show a plain screen straight on; when a close-up earns its place, hold the full view 1.5 to 2 s,
  then push in slowly with eased, continuous camera curves (no speed jumps between segments).
- The narration names a state the picture does not show: "headaches, nausea" over a child standing still. Act it out
  (posture, sway, hands to head, a slow double-vision blur) without gore.
- A title cut away before it is read (An: "chuyển cảnh quá nhanh chưa kịp nhìn"). Let it land, hold still about 2 s,
  then move on with a camera move (a tilt down into the next scene) rather than a hard break.
- A paper or white flash frame between dark shots: one bright frame in a dark film reads as a glitch. Keep exits dark.
- A body that acts a symptom in silence: a headache, nausea or a nightmare acted with no breath, groan or cough
  under it. Give the figure its own voice sounds (no words).
- A title that only fades. Give it a short motion: assembling from slices, a light sweep, slow tracking, a break-up
  on exit.

### Game

A playable web game (`game.md`).

- A game balanced by feel: no bot playtest (idle, simple and good players, several seeds) with survival times against targets.
- A post about a game made from a render or a mock-up instead of a recording of the real build being played.

## Growing the lists

When the user or the main session finds a fault this loop missed, add it to the matching mode's fault list in the
same turn, with the case. Add it to the generic list above when it can happen in any mode.

## Previews and the final render

Show the user fast previews while the cut is still changing: half size, 30 fps, no motion-blur subframes. Run the
full final render (full size, subframes, master and web copy) only after the user approves the cut.
