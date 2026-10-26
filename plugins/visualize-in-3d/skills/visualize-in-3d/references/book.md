# Book mode: illustrated cutaway plates

One page per subject: a big object or building cut open like an encyclopedia plate, in 3D. The viewer orbits it, reads
labels in the margins and flies to a room. Several subjects make a page-turning book with a short quiz on each
page. It uses the "Illustrated cutaway plate" look from `looks.md`. The rules below came from a real build of a
liner (a lofted hull, ten decks, about 2,000 people). They hold for any subject with many rooms.

Reading map: Plan file, Build, Post pass, Labels, Page and book, Reel, Faults seen, Checks.

## Plan file

Write one file before building. It holds:

- The view: the camera side, the home view (a high three-quarter view of the whole object) and the close-up views
  (one per hero room).
- The real numbers with a mark of "measured" or "inferred": length, width, height, decks or floors, counts of people,
  boilers, bells, whatever the subject has. Check each against a source.
- A room list in real place order, with the floor each room sits on and the jobs done in it. Name the contrast the page
  should show (luxury above, toil below, or the shrine above and the crypt below).
- 10 to 14 callouts (heading, 2 to 4 lines, the room it points to) and 6 to 8 named people for the bottom row.
- For a book: the subject order, one line on how pages connect, and 3 quiz questions for each page, with answers
  that the callouts already state.

## Build

Use three.js with no Blender. A lofted shell, boxes and a few extrusions read well under a watercolour pass.

- **Shell.** Build the outer form from cross-sections along its length (a hull, a nave, a tower), so the plan, the
  keel or roof line and the cut all come from the same numbers. Use real dimensions and keep the aspect ratio. Never
  stretch the model vertically to fit more rooms. Make the decks taller in the plan if rooms feel cramped.
- **Cut.** Remove the camera-side wall in strips of different heights, so the broken edge shows the wall thickness.
  Keep both ends of the object whole. The section plane leans back as it rises (a slope of about 0.1 to 0.15), so the
  ceiling edge of each level sits behind its floor edge. A vertical plane makes every slab edge hide the room below.
- **Rooms.** Each room is a floor slab (warm top, dark brown edge), a back wall, a ceiling edge and its furniture. Give
  it a lamp colour and its own wash. Build the hero rooms in detail and let the others share parts.
- **Figures.** Use one part list for both the instanced crowds and the large portraits. A figure is about 1.8 m
  before scale, with a pose and a job. Every room gets 10 to 40 figures doing that room's work. Rooms the story
  names get a few extras with a clear action, such as a cook, a pianist, or a stoker with a shovel.
- **Settle every figure.** A room asks for a height, not a surface. Before the crowd is built, drop each figure onto the
  highest surface under its feet: a deck, a stair, a table top, a bench. Keep the requested height too. Then check:
  `floatingFigures()` walks every standing figure, takes the height of the support under each foot, and returns the
  count, the worst offset and the worst offenders. It must report 0 above a 2 cm tolerance, and no sunken figure
  either. Run it on the raw requested heights as well, to see how many rooms relied on the drop.

## Post pass

A full-screen pass turns the render into a plate.

- Paper: cream base with low-frequency blotches, so no area is flat. Grain at the end, multiplied over everything.
- Washes: band the lit colour to 3 or 4 tones per material. Darken the colour along band edges, where pigment pools.
- Ink: outlines from depth and normal edges in dark brown, about 24, 15 and 9 percent red, green and blue
  (`#3d2615`). Black outlines read as a vector cartoon. Vary the width a little with noise.
- Hatching: two sets of short diagonal lines, only in the darkest tones.
- Scale ink and grain with the render height, so a 4K still and a phone screenshot look alike. A still export takes an
  explicit scale.
- Keep the pass cheap enough for a phone. Check frame time on a mid-range GPU before adding passes.

## Labels

- Labels are HTML over the canvas, in two columns in the paper margins. Each has a bold serif heading, 2 to 4 lines of
  body and a thin dark leader to a 3D anchor inside its room. Anchors are projected every frame.
- Slots are the order of labels in a column. Sort them by the anchor's screen height, then swap any two slots whose
  leaders would cross. For a recording, freeze the slot order. Pick the order with the fewest crossings, and among
  equals the shortest leaders, over the whole planned orbit: sample the anchors at several azimuths and try each order.
  Text stays in its slot. Only the leader ends follow the camera. A label that changes slot mid-shot reads as
  jumping.
- Expose `labelCrossings()` and call it on every recorded frame. It must be 0 while labels are visible.
- Labels never overprint the object, the title block or each other. Check at the page's smallest supported width.
  On a phone, labels collapse into numbered pins pushed apart so none overlap, each tied to its anchor by a short
  line, and a tapped pin opens one card.
- Labels hide during a fly-in to a room, and the opened room's own labels (people, objects) show instead.

## Page and book

- A page is the plate plus its furniture: the title in small caps, an intro of two or three sentences, an inset of the
  whole exterior, the margin labels and a "People in the ..." row at the bottom.
- Controls: orbit within limits (the cut side keeps facing the viewer), zoom, tap a label to fly to its room, and a
  way back to the home view. One dock at the bottom, one menu open at a time.
- A book holds several pages, each its own plate, in a fixed order. Turn pages with the arrow keys and a swipe, and
  show the page number. Load one plate at a time and free the previous one's geometry and textures.
- A quiz is 3 questions per page on a card that opens from the dock, never over the object. Questions have 3 to 4
  choices. Wrong answers say why in one line, and the right answer flies to the room that explains it. Keep a score for
  the whole book and show it on the last page.
- Optional: an "Ask Claude" box per page, when the host provides one. Give it the page's plan file as context, so
  its answers stay on the subject and use the page's numbers.

## Reel

For a short film of the page, record it frame by frame from the live page.

- Use Playwright with its fake clock, so each captured frame advances exactly 1/30 s and animation depends only on
  time. Install the clock before the page loads and keep it moving while fonts and shaders load.
- Pre-roll before the first frame. Park the camera at a mid-orbit view, let labels settle, lock the slot order for the
  whole orbit (see Labels), then move to the first view. Without it, frame 0 shows labels overprinted at their starting
  slots.
- Camera keys are a list of seconds and views. Ease between keys with a smoothstep, and hold when two keys are equal.
  A typical reel: wide with a slow orbit, one close-up per hero room, wide again. End on the start view, so the film
  loops.
- Labels fade out over the first 0.6 s of a fly-in and come back once the camera is home again.
- Turn off CSS transitions with a style tag, so the clock alone drives the page.
- Write the frames as JPEGs, count leader crossings on every visible frame and log the worst. Encode with ffmpeg.

## Faults seen

- Floating figures: feet above a deck or a table, or sunk below it. Cause: a figure placed at a fixed height. Fix: settle
  every figure onto the highest surface under it and run `floatingFigures()`.
- Empty rooms: a cut room with furniture and no people. Every room needs its crowd and its job.
- One amber wash: every room lit the same, so the plate reads as flat orange. Give each room its own wash and keep amber
  for lamps and fires.
- Black ink instead of brown: outlines turn the plate into a vector cartoon. Use dark brown.
- Labels jumping or overprinting: slots re-sorted every frame, or two labels at the same height. Freeze the order in
  recordings and keep a minimum gap.
- Leaders crossing: check `labelCrossings()` at the home view and along the whole orbit, not just at one view.
- Frame 0 overprint: the first frame of a reel shows labels before they settle. Pre-roll first.
- Stretched proportions: a model scaled vertically to fit more rooms. Keep real proportions.
- Hidden deep rooms: a vertical section plane lets slab edges cover the rooms below. Tilt the plane back as it rises.
- A clean cut: a straight sliced wall looks like a CAD section. Break the edge in steps.
- Leaders into nothing: an anchor placed outside its room, or behind a wall edge. Put anchors on the room's floor.
- A ground box or sky behind the object: the plate floats on paper.

## Checks

- Run `scripts/frame-guard.js` and `self-review.md` on any recorded reel.
- Run `floatingFigures()` and `labelCrossings()` before reporting. Both must be 0.
- Screenshot the home view and each close-up at 1920x1080 and at 390x844. Look at the title block, the labels and the
  bottom row for overlap.
- Compare one rendered still with the reference plate for paper, ink colour and wash count.
