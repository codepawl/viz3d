# Looks

Each topic file names one look. The look sets the world's rendering, the UI skin and what the film shows; the data
model, the dashboard parts and the film's click-driven shape stay the same. Reading map: Toy isometric (default),
Point-cloud survey, Photoreal terrain analysis, Dark documentary, Pixel diorama, Illustrated cutaway plate, Lived-in isometric, Choosing.

Reference stills or clips for a look are optional. If you have some, save them under `{{WORK_DIR}}/references/<slug>/`
and point the briefs at them; they are for study only and never ship in the app or the film. Without them, the
description of each look below is enough.

## Toy isometric (default)

Built for an AI data center, an agents office, an airport ramp, a chip fab, air traffic control, a metro and a toll
plaza. Think of a clean isometric diorama inside a light operations dashboard.

- World: a diorama on a ground slab with soft edges, seen from about 35 to 45 degrees above with a long lens (field
  of view 25 to 35). Light cool palette, one strong brand colour for the main units, a second colour for alerts.
- Scale: real dimensions, but vehicles and people slightly chunky (about 1.1x thickness) so they read when small.
- Light: one soft sun with long, soft shadows, a sky fill, ambient occlusion, gentle bloom only on lamps and screens.
- Materials: matte paint, rubber and concrete with low roughness variation; glass slightly tinted; no busy textures.
- Assets: Blender models with bevels and panel detail (Pass 1 as written).
- UI: light dashboard, white rounded cards with soft shadows, one font family, coloured status icons, numbers in
  tabular figures.

## Point-cloud survey

Reference: a strait-monitoring app drawn as white dots over terrain. Fits places defined by their land and water: straits, ports, borders, mountains, coasts, a city seen from above.

- World: terrain as a dense grid of small white spheres raised by a real heightmap, so slopes shade and valleys sit
  in shadow. Water is a flat, matte, light-grey plane. Vehicles and buildings are matte white clay models (no
  textures, no colour) with real detail; wakes, trails and exhaust are particles of the same dots.
- Rendering: under about 150k dots, `InstancedMesh` of low-poly spheres (8x6 segments). Above that, `THREE.Points`
  with a sphere-impostor shader (round point sprite, normal from the sprite UV for lambert shading, depth written so
  dots occlude). Jitter each dot slightly so the grid does not moire. SSAO is what makes it read as 3D; add a light
  bokeh depth of field (tilt-shift) and a soft overcast key light with long, faint shadows. No bloom.
- Heights: a real DEM of the place (see `real-objects.md`, Terrain), resampled to the dot grid; exaggerate height
  1.5-3x when the land is low.
- UI: almost monochrome (white, greys, near-black text), one alarm colour (orange about #FF5A1F) used only for
  alerts, the selected unit and a crossed threshold. Monospace type, bracketed section titles (`[STRAIT]`), thin
  HUD furniture over the scene (heading tape, pitch ladder, range rings), mac-style window chrome, small line
  charts with dashed baselines, a hatched band between panel groups. House UI rules still apply (no divider lines
  between rows, icon-led statuses, no eyebrows).
- Film: slow low-angle drift along the terrain with the depth of field, the selected unit in sharp focus.
- Traps: dots too big (reads as Lego) or too sparse (reads as noise); aim for 2-4 px per dot at 1080p in the
  wide shot. Without AO it looks like a flat stipple texture.

## Photoreal terrain analysis

Reference: wildfire analysis tools that scrub a fire's spread across real terrain. Fits events that happen across
real land over time: wildfire, flood, an expedition, a manhunt, a battle, a historical route.

- World: real DEM terrain with a satellite-style or procedurally painted ground texture (dry grass, rock, scattered
  instanced trees), long mountain shadows, atmospheric haze toward the horizon. Overlays drape on the terrain:
  burned or affected area as a translucent red/orange fill, the event's front as a glowing line, dated waypoints
  ("Aug 14, 14:26") as pins with leader lines, arrows for the direction of spread.
- Time is the main control: a timeline slider scrubs the event from start to end, and every overlay, chart and the
  key-events list follow it. A 2D map toggle shows the same overlays on a flat topographic map.
- Units: drones or aircraft fly real paths; clicking one opens its camera feed in a floating window (a thermal
  palette, purple to yellow, with a crosshair and HUD numbers).
- UI: warm off-white panels (paper, beige), dark text, red/orange for the event; layers panel with opacity sliders,
  an incident overview card, weather and behaviour cards, small area and rate-of-spread charts along the bottom.
- Film: open on the wide 3D view, scrub time so the overlay grows, switch to the 2D map, open a unit's feed, fly the
  camera low along the front.

## Dark documentary

Reference: the dark map-and-silhouette style of documentary YouTube channels such as LEMMiNO (study only; copy no
frames, music or text). Fits a case file or a piece of history: a crime, a disappearance, an investigation.

- Palette: near-black (#0b0b0c to #1a1a1c), greys, white text, one red (about #e0262b) for the crime, the clue and
  the key word; a muted blue only for police or investigators. No other colour.
- Map: a dark historical street map, thin light-grey lines on black, street names in letter-spaced caps, slight
  grain and vignette; crime sites are glowing red X marks or dots; the camera pushes in slowly from the district to
  the street. A public domain period map (USGS historical topo, an old city plan) traced or shaded dark works.
- 3D reconstructions: dark low-poly rooms and buildings lit by a few warm windows and one red light pool where the
  crime happened (the red light stands in for violence: never blood, bodies or wounds). People are flat solid
  silhouettes: white for the victim or witness in focus, blue for police, translucent grey for others.
- Labels: small boxed captions in spaced caps with thin leader lines (`PC THOMAS BARRETT`, `SUSPECT`), red dots at
  the anchor; a thin red timeline across the top with times and events (`04:45 BODY IS FOUND`), a note that times
  are approximate.
- Documents: quotes as small centred grey text with the key phrase in red and an italic source line with the date;
  footnote brackets `[6:207]` in a corner; fact cards (name in spaced caps, age, address, dates) beside a framed
  portrait. Portraits are engraved-style sketches with a label tab; a victim's frame is red. Draw no likeness of a
  real person from imagination; use a public domain image or leave the frame as a name card.
- Opening: a black card saying the events may disturb and no graphic imagery is shown; an engraved-style panorama
  of the place under a starry sky with the place and year in spaced caps (year in red); the title in spaced caps
  with the name in a glowing red script. A building of interest is its footprint extruded dark on the map with a
  red glowing outline and a boxed label.
- Motion and sound: slow pushes and dissolves, nothing snappy; a low ambient drone with soft hits on reveals.
- Respect: victims are named with dates and treated as people; the film follows the investigation, not the gore.

## Pixel diorama

Reference: the "small floating world" pixel style seen in short battle and port clips. Reuse
`{{SKILL_DIR}}/scripts/pixel-pass.js` (copy to `src/pixel-pass.js`; it only imports `three`). Fits any place seen as
a small floating world with many tiny units: ports, yards, farms, camps, fairs, battles. Needs no Blender: boxes,
extrusions and a few icospheres read well at this resolution.

- Rendering: a real 3D scene drawn at about 360 px across (use `pixelScale` 5 at 1920x1080, so 384x216) and
  upscaled with nearest-neighbour; one directional sun with real cast shadows; flat toon shading, 3 to 4 tones per
  material (`createToonMaterial`); dark 1 px outlines around objects from depth edges, light creases from normal
  edges; a limited natural palette (greens, soil browns, concrete, teal water, muted colours); a plain
  paper-coloured background; the world is a floating block of 0.5 u cells (a cap cell over a soil column) with
  ragged edges (cells near the border drop out by noise) and a soil cliff below.
- Camera: orthographic, azimuth -135 and elevation 30 for the iso views. `snapOrthographicCamera` snaps the camera to
  whole low-res pixels along its right and up axes and returns the sub-pixel residual that `PixelPass.render` applies
  while upscaling, so the camera drifts smoothly and nothing shimmers. Ease the focus, zoom, azimuth and elevation
  yourself every frame; keep zoom changes slow (they re-sample every texel).
- Smoke, dust and fade-ins: clusters of 4 or 5 icospheres sharing one material with `addDitherDissolve`, an ordered
  Bayer discard in low-res pixels. Mark the group `userData.skipNormalPass = true`. Units fade in at the edge of the
  world with the same helper, so nothing appears out of thin air.
- Water: a flat toon slab, deeper-blue lane stripes, pale arcs (`RingGeometry` arcs that blink on for the middle of
  their life) and sparkles (tiny cubes blinking in steps), plus arcs spawned behind moving boats.
- Traps: pixel scale too high (units under 3 px vanish; keep boxes at least 4 px), too many shadow-casting instanced
  meshes (cast shadows only from objects, not ground cells), a half-float render target needs
  `EXT_color_buffer_half_float` (all WebGL2 desktop), clipping planes need `renderer.localClippingEnabled = true`.
- Views, each chosen for what it shows best: a wide iso overview, a close-up of the busiest spot, a map-style
  top-down (azimuth 0, elevation 76) for flows, a low side view for arrivals, and a side cutaway of one unit. A
  cutaway clips the camera-side half of that unit with a clipping plane (`material.clippingPlanes`,
  `side = DoubleSide`) and hides anything in front, so its inside shows while work goes on. Build the interior
  inside the unit from the start.
- UI: flat paper panels with a 3 px ink outline and a hard offset shadow, a pixel font (Pixelify Sans, OFL,
  bundled), segmented progress bars, 8x8 bitmap status icons with a different shape per state, quiet text tabs.
- The floating block itself needs detail, or its corners and underside look sharp and plain:
  - corners rounded in pixel steps, with an eroded edge
  - an underside of rock strata that tapers to hanging spires of varied length, with roots
  - hanging vines that sway over the edges
  - a waterfall where water meets the edge, and a lava stream where lava meets it
  - loose rocks, grass tufts and moss along the top edge, instanced
- Characters, creatures or vehicles acting in this look (a fight, a chase): `action.md`.
- Film: real clicks on a virtual clock (`film.md`, Live app films): overview, close-up, click a unit (card and
  follow), cutaway, top-down, low view, overview. Check frames at the real size; pixels must be square and crisp.

## Illustrated cutaway plate

Reference: an encyclopedia plate of a medieval castle in the style of the DK and Stephen Biesty cross-section books.
It shows one big building cut open, with a room on every level full of small people at work, and labels in the margins.
Fits one big object or building with many rooms full of people: ships, castles, cathedrals, stations, factories. The
`book` mode (`book.md`) builds it. Keep a copy of the reference under `{{WORK_DIR}}/references/<slug>/` for study.

- Page: warm cream paper (about `#f3ead6`) with fine grain. The object floats on the paper, with no ground box or sky.
  Its base dissolves into the paper in loose washes (rocks, water, sea).
- Rendering, read off the plate: watercolour washes in 3 or 4 soft tones per material, warm overall. Thin dark brown
  ink outlines from depth and normal edges, slightly uneven. Short ink hatching in the shadow tones only. Pigment
  pools darker along wash edges. Paper grain multiplied over everything. The ink is brown (about `#3d2615`), never
  black.
- Light tells the story: the exterior is pale stone or paint in daylight, and the cut interiors glow amber (lamps,
  fires), so the eye goes straight into the rooms. Give each room its own wash (cool for a bridge, green for a
  garden, red for a boiler). One amber wash over everything reads flat. Accents are few and saturated.
- The cut: the camera-side wall is removed in a stepped, broken edge (masonry or hull plates show their thickness),
  never a clean plane. Tilt the section plane back as it rises, so each level's ceiling edge sits behind its floor
  edge and slab edges do not hide the rooms below. Every exposed room is a stacked stage seen from a high
  three-quarter view, packed with small figures each doing the room's job (eating, cooking, praying, stoking).
  Empty rooms kill the look.
- Labels: no boxes. A bold serif heading and 2 to 4 lines of serif body sit in the empty paper beside the object, in
  columns at the left and right edges, each with a thin dark leader line to its part. They are HTML over the canvas,
  re-projected every frame, and their slots are chosen so leaders never cross (`book.md`, Labels).
- Page furniture: a big small-caps serif title at the top left with a short intro paragraph, a small inset of the
  whole exterior, and a "People in the ..." row along the bottom with full-figure characters, a bold name and a
  two-line role each. House UI rules hold: no boxed frame or rule lines, so group by spacing alone.
- Fonts: an engraved serif with real small caps for the title (Cormorant SC or IM Fell English SC, OFL), and a book
  serif for labels (EB Garamond or Crimson Pro).
- Proportions are real. Never stretch the model vertically to show more rooms. Make the decks taller in the plan
  instead.

## Lived-in isometric

The survival-game look of Project Zomboid, studied from public sources only. Fits ordinary buildings where people
live or work and a crisis plays out inside them: a house in a storm, a flat in a fire, a clinic in a blackout.

- Camera: orthographic, high three-quarter view (about 30 degrees down, 45 degrees around), 4 to 6 zoom steps. The
  floors stack; a floor switcher shows one floor and hides every floor above it.
- The cut: walls and doors on the camera side drop to a 0.3 m stub around the floor in view, with a soft dithered fade
  near the focused person instead of a hard pop; wall thickness, skirting and the inside finish show on the stub.
- Lived in: real scale, every room furnished and cluttered with the things its people really own; muted, slightly
  desaturated realistic materials with grime and wear, never toy chunky shapes or clean showroom surfaces.
- Light tells the state: warm interior bulbs that spill through doors and windows onto floors and the street; when the
  power fails the rooms drop to near black and only flashlights, candles and phone screens light them. Time of day
  moves the sun. An optional vision cone darkens what the focused person cannot see.
- Weather is part of the world: rain streaks and splashes, wind that sways trees, wires and loose things, puddles, and
  murky brown flood water with floating debris that rises as a real plane through the rooms.
- UI: small dark translucent panels in the lower corners (survival HUD), a right-click context menu on objects with
  the real actions, a short task queue per person, and a clock with the hours to the event. House UI rules hold.

## Choosing

Toy isometric is the default for every topic. The point-cloud look can read as dull on a busy site, so use it when
it is asked for. Otherwise pick the look the place itself suggests: built places full of moving vehicles go toy
isometric; land and water seen from above go point-cloud; an event spreading across real land over time goes
photoreal terrain; a case or a piece of history told in order goes dark documentary; a small floating world with
many tiny units, or a battle between creatures, goes pixel diorama; one big object or building with many
rooms full of people goes illustrated cutaway plate; an ordinary building with a crisis playing out inside it goes lived-in isometric. A look the user shows from a reference video is
studied frame by frame (`scripts/contact-sheet.sh`) and written up as a new section here. Write the look's name in
the topic file. Add a new look only after saving its reference and writing a section here.
