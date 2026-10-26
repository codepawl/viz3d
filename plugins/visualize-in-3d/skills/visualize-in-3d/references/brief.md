# Briefs for the live app passes

Two passes, one after the other, each pointed at the same topic file: hand each to a fresh subagent where the
harness has them, or run them in sequence in one session. Copy each brief, replace `{{SKILL_DIR}}` (where this skill lives), `{{FOLDER}}`,
`{{PORT}}` and `{{TOPIC}}` (the topic file's path), and change nothing else. The topic file's first line names the
folder and the port; use those. Without them use `{{WORK_DIR}}/viz-<slug>` and a free port from 5420 up. If the topic
names no look, use toy isometric and write that into the topic file first. Paths use forward slashes on every platform. Without Blender, replace Pass 1 with {{SKILL_DIR}}/references/no-blender.md.
Reading map: Pass 1 (assets), Pass 2 (app and film).

## Pass 1: Blender asset pack

```
Build the 3D asset pack for a live 3D app that shows how a complex place or system works. The subject, its world and
its data are in {{TOPIC}}; read it first. The topic names a look; read that look's section in
{{SKILL_DIR}}/references/looks.md, and its reference files if the topic folder has any, before
modelling. Make your own designs; no real brands, logos, liveries or existing characters.

Model from real references, never from memory: follow
{{SKILL_DIR}}/references/real-objects.md. For every main asset write its
reference sheet in blender/refs/ (real type, dimensions with sources, proportions, parts list, 3 to 6 reference
images with source and licence) before modelling it, block out at real size against the reference views, and check
the compare renders. If the user has not approved downloading reference images, write each sheet from what you
know, mark the numbers "verify", and use a dimension blockout drawn from the sheet as the left side of the compare.
Say so in the report. If the topic is a real place, fetch its elevation as that file says (the topic file states
whether the user approved the download).

Work only in {{FOLDER}}: Blender scripts in blender/, GLBs in app/public/assets/. Run Blender 5.x
headless (--background --factory-startup --python <script>) at low priority, one Blender at a time (wait while another
blender process runs). Use the full path to the Blender executable if `blender` is not on PATH, and send its output
to a log file you read afterwards. Keep scratch files inside {{FOLDER}}, never in a folder another job shares.
Blender gotchas: --factory-startup still loads the default cube, camera and light, so start each script with
bpy.ops.wm.read_factory_settings(use_empty=True). Model each vehicle facing Blender -Y; the glTF exporter turns that
into +Z, so lookAt works in three.js. Write the facing into ASSETS.md. glTF export of clips needs
export_animation_mode="NLA_TRACKS" with each clip pushed to an NLA strip. The exporter takes the rest pose from the last NLA
track at its first frame, so push a clip that starts at rest last. bmesh.ops.bevel gives new faces material
index 0, so set the materials of the bevel faces again on multi-material meshes. An exact boolean can silently drop a concave prism; build
such walls from convex parts. The exporter writes only materials that a mesh uses, so park unused state materials
(lamp on/off) on a small hidden swatch node. Blender renames duplicate names to
.001, so prefix each child with its variant name (Car_Cab_Door_L, not Door_L).

Model every asset procedurally with proper bevels and rounded edges, panel lines and small real details (vents,
bolts, windows, wheels with hubs, lights, signage plates), clean topology with smooth shading and hardened edges,
UVs, PBR materials (small procedurally baked textures are fine), emissive where things glow. Anything the app switches (signals, lamps, screens) gets its own named emissive
material per state, so the app can toggle it. Two to four variants of anything that repeats more than about five
times (vehicles, people, trees, buildings); one model is fine for unique structures. Moving parts are separate named objects or bones with their pivot at the
origin (wheels, doors, fans, lifts, booms, bridges, character limbs); characters and animals get an armature with
named clips (the app plays clips per figure, or for crowds uses a few baked pose meshes per clip, since three.js
instancing does not skin) (vertex groups per bone, an Armature modifier, clips on NLA strips); render one posed frame of each clip
to check the bone axes. Build repeating structures (track, platforms, sheds) on one module length that fits the real
thing, and write it into ASSETS.md. Keep the total under about 40 MB (10 MB is typical), one GLB per asset family so repeats can be instanced.
Set single-sided materials (backface culling on), so the exported glTF is not doubleSided.

Verify: blender/preview.py renders a contact sheet per GLB (a few angles, back-face culling on, a 1.8 m figure block
beside each asset for scale) to blender/previews/. For 3 to 6 main assets, also a compare sheet: reference (or
dimension blockout) and render in the same orthographic view and scale with a ruler (1 m, or 10 m for assets over 40 m), side and top views,
side by side or stacked for long objects; look at every sheet and fix wrong
scale, wrong proportions, missing parts, bad normals, holes, floating parts. Write
blender/ASSETS.md with one table row per node: file, node name, pivot, facing, clips, real-world size and where it
goes. Also write blender/catalog.json with the numbers the app needs (lengths, axle or wheel offsets, sensor heights).
Check the facing in ASSETS.md against the exported file before handing over. Rules:
check GPU memory before GPU renders and use Workbench or CPU when it is full, no personal data. Write pass1_started_at.txt and
pass1_finished_at.txt (UTC). Budget about 80 tool calls; for a wide topic (more than about 6 asset families) budget 120. If the budget runs
out, stop after a family is exported and checked, and list the families not built. Report the asset list with sizes,
what you looked at, gaps.
```

## Pass 2: the app and the film

```
Build a live 3D app in the browser that makes a complex place or system easy to see, on the subject in {{TOPIC}}
(read it first), using the GLB asset pack in {{FOLDER}}/app/public/assets (read blender/ASSETS.md). Render the
world, skin the UI and shape the film as the look named in the topic says (its section in
{{SKILL_DIR}}/references/looks.md, and its reference files). In every look: a
world with things moving on their own; pins and selection rings over objects; and a light UI that keeps the world
the main thing on screen. Start from the smallest UI the topic needs: a name, the few numbers that matter (two to four
KPIs), a detail card that opens for a clicked object, the stage bar and the playback controls. Buttons are few, large
enough to hit, plainly labelled and do one thing each. Do not add a default dashboard (search, site switcher, user
menu, list tabs, extra panels) unless the topic needs it or the user asks; when the user asks for a specific panel or
control, build that one to their need. Make your own name, logo and data; do not copy the reference's name, logo,
text or exact layout. Never call it a game in the UI.

Motion that explains. Animate what the viewer must understand: the parts move as the process does, flows (goods,
power, fluid, people, data) travel along their real paths as moving particles or arrows, the part a stage is about
glows while the rest dims, numbers count to their new value, cards and the stage bar slide in rather than pop, and the
camera eases between stages. Every motion shows a fact of the process; nothing moves only for decoration.

Nothing appears out of thin air. A part or a cable that joins the scene comes from somewhere real (a bench, a tray, a
truck, a rack), travels there and is fitted as a person would fit it: a jumper wire is picked up, carried and pushed
into its hole, its cable a continuous curve re-solved from both ends every frame. A flow overlay (current, heat,
pressure, data) is off by default behind one toggle; when on it is easy to read: large particles with short trails,
direction and speed from the real quantity, colour by its level, and a value label on each branch. Where people learn
by doing, add a "Build your own" mode: a parts tray, parts that snap to real positions, connections drawn by dragging,
Run and Stop, and a simple check that says why something does not work.

Things work as they do in reality, whatever the topic. Every mover follows its real guidance (a lane, a rail, a
taxiway or runway centre line, a conveyor, a pipe run, a cable tray) with turns, speeds and acceleration the real
machine can make: no sharp kinks, no sideways sliding, no passing through solids. Every connection meets its real
connection point and stays on it while things move: a gangway or jet bridge on the door sill, a hose on its port, a
plug in its socket, a coupler on its hitch, a wire in its hole, a belt end on the hatch. Put each attach point in the
model's metadata (named empties exported with the GLB) and drive the connector to it, never to a guessed offset. A
debug check measures every connector gap while attached (under 0.1 m at site scale, under 1 mm at bench scale) and
draws each mover's trace over its real path from above; run both before recording. Movers that share space follow the real right-of-way rules, never pass through each other: an aircraft is cleared to push back only when the taxilane is free, trains keep block separation, ships wait at a lock, vehicles queue behind each other. Reserve the shared segments in the simulation, and have the check report the smallest distance between any two movers over a long run (zero overlaps) and how long they waited, so traffic still flows. Look at every scene where two movers meet.

Themes. Ship three themes switched by one quiet button and remembered per viewer: the look's own palette, a dark
one and one more that suits the topic (blueprint, paper, night shift). A theme changes the scene's lights, ground and
materials as well as the UI colours, and every theme keeps text contrast readable.

Work only in {{FOLDER}}/app. Stack: Vite + React + React Three Fiber (+ drei, @react-three/postprocessing with N8AO for ambient occlusion), and
Playwright as a dev dependency for checks and the film, all pinned to exact versions, serve on port
{{PORT}}. A plain data model (sites, units, tasks, events) drives everything; the 3D view and the dashboard both read
it, and a small seeded simulation advances it in real time so things move, statuses change and numbers tick. Load the
GLBs with instancing for repeats, drive every moving part and clip from the simulation. A fixed-step simulation
keeps the previous and current pose of everything that moves and renders the pose interpolated by the leftover
time, so motion and the follow camera change every frame (no stutter). No two surfaces share a plane and no two
modules overlap: lay repeats end to end, build curves (track, viaduct deck) as continuous swept geometry, lift
stacked floors a few centimetres apart, and set the camera near plane to about 0.5 m. Ground layers each get
their own height: grass -0.2 m, pads -0.06, road and floor modules 0, paint and decals +0.04. Walls and vehicles follow the same rule: a sign, lamp or poster stands 4 cm proud of the glass or panel behind it, never at the same depth. Where a pad or plaza
replaces a road, leave the road modules out there instead of laying both. Run {{SKILL_DIR}}/scripts/coplanar-check.js
on the built scene and fix every pair it lists before any screenshot. Anything that must meet a vehicle (platform screen doors, jet bridges, loading docks, lock
gates) is placed from the vehicle's own door or hatch positions where it stops, not from a repeating module, and the
vehicle stops exactly on its mark; print the offset of every pair and keep each under 5 cm, and keep the side gap
to the real one (about 0.1-0.2 m at a platform). Layered transparent surfaces
(glass over glass) read as a smear; keep one glass layer and make the rest opaque. Clicking an object selects it
and opens its card; clicking a list row flies the camera to it (and follows it if it moves); switching sites changes
the world. Soft shadows, ambient occlusion, gentle bloom on lights, smooth camera moves. 60 fps at 1920x1080 on a
mid-range GPU such as an RTX 3060.

Stages and playback. The topic lists the key stages of the process (for a toll: queue, booth or reader, class set,
paid, posted). Each stage gets a named camera preset framed on where that stage happens, close enough that the unit
doing it fills about a quarter of the frame, from the side that shows the moving part (the boom, the tray, the hold
door), never through a wall or roof. A stage bar lists them in process order with a number key each (1 to 9); picking
one flies the camera there in about a second, and "Next stage" and "Previous stage" step through them. A "Tour"
button plays the stages in order, holding each until its event has happened once, then moves on; any click or drag
stops it. Per selected unit, "Follow" keeps the camera on it with three distances (close, mid, wide), and the card
shows which stage it is in, and how long it has been in it. Playback controls sit in the timeline strip: pause and
play (Space), speed 0.25x, 1x, 2x, 5x and 10x (keys - and +), and "Step" that advances one fixed step while
paused. Speed changes how many fixed steps run per frame (fractional speeds accumulate), never the step length, so the
simulation stays deterministic and the same seed gives the same result at every speed; the clock and every rate on
the KPI cards follow simulation time. "Slow down at events" (on by default in the tour) eases to 0.25x for the
second around a stage's key event and back. A preset may sit lower than the free camera's minimum height (platform eye level for train doors); flag it and
skip the clearance rule only while that preset holds. Ease the slow-down in before the event from the known schedule,
not after it fires. Store the camera presets in one data file, and expose them and the speed on
window.__app for the checks and the film.

UI rules: no small uppercase eyebrow labels above headings, no coloured left-border callouts, no divider lines
between rows (spacing and subtle fills instead), every status starts with an icon whose shape differs per state, tabs
are quiet text buttons, a card closes by clicking empty ground or Esc (no X on side panels).

Verify with Playwright (Chromium with --enable-gpu --ignore-gpu-blocklist, plus --use-angle=d3d11 on Windows) at 1920x1080: the overview, a selected object with its card, a second site, a
close-up, close-ups of each main asset type, and one per stage camera preset. Check that pause freezes every
moving part, that 5x and 0.25x keep the same order of events as 1x for the same seed, and that the tour runs
through every stage once. Look at every one and fix clipping, overlapping UI, unreadable
text, z-fighting, floating or sunken objects, broken picking, anything that looks like programmer art. Measure fps.

Film: 30 s 1920x1080 30 fps at shots/film.mp4 with a deterministic virtual clock (override requestAnimationFrame,
performance.now and Date.now in an init script, advance 1/30 s per captured frame; drive the app only through real
clicks, drags and wheel events with a visible cursor), encoded at below-normal priority, H.264 yuv420p crf 18
faststart, plus a copy under 25 MB. Shape: 0-5 s slow orbit over the whole site with things moving; 5-12 s click a
moving unit, its card opens and updates live while the camera follows; 12-18 s click a list row and the camera flies
there; 18-24 s switch to another site; 24-30 s pull back to a wide shot where the site still fills most of the frame.
mpdecimate must show no repeated frames; look at stills.
Film traps that earlier builds had to fix: the opening so far out that units are specks (open close
enough that dozens of moving units read); a beat that waits on the simulation and shows nothing (pre-roll the
virtual clock so the followed event lands 2-3 s into its beat); a follow camera that ends inside a structure (keep a
minimum distance and a height above the tallest model); selection rings far wider than the object (fit the
footprint, an ellipse for long things, at most about 1.3x); bare white or grey ground (give every surface a real
material: asphalt, lane paint, verges, floors); a last shot where the site is small in a sea of empty ground. Use the stage presets for the film's beats instead of
free camera moves when a beat shows one stage, and show a speed change (2x or 5x) once with the control on screen.

Before reporting, run the loop in {{SKILL_DIR}}/references/self-review.md (up to three rounds) on the app and the film. Record the film as {{SKILL_DIR}}/references/film.md "Live app films" says. Run the dev server as a background
job and stop it when done. Write README.md, pass2_started_at.txt and pass2_finished_at.txt (UTC). Budget about 100 tool calls. Report: what was
built, how to run it, screenshot and film paths, checks with numbers, honest gaps, and a one-line caption suggestion
("Claude built a live <place>, every <main assets> modeled in Blender and running in three.js").
```
