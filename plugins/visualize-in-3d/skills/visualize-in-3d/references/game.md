# A playable web game

A free browser game people play, not a film or a dashboard: one creature or unit the player steers, a world that
pushes back, and growth the player earns. Reading map: Core loop, Controls, Growth, Opponents and the director, Bot
playtests, Creature motion, Tutorial and first load, Performance, Film mode and the post, Deploy, Credits. Read the
whole file for a new game; read only the matching sections when fixing one part.

## Core loop

- Goal readable in 5 seconds with no text: move, eat, grow, survive. One screen shows the player's unit, its
  size count and the nearest threat.
- Third-person chase camera in an open world unless the user asks for a diorama. The player's unit must be the
  only strong colour in a quiet world, large enough to read at phone size.
- A run has a start (one small unit), a middle (growth, fights) and an end (death card with time and size, "play
  again" without a page reload).

## Controls

- Move: the unit follows the pointer (mouse, or drag on touch). Keep steering easy; hard controls were a complaint.
- Two abilities on separate buttons with cooldowns: an attack (lunge) and a defence (dodge that becomes a parry
  when started just before a hit, `PARRY_WINDOW` about 0.35 s). Each ability is a small object with active seconds,
  cooldown seconds, `ready(time)`, `trigger(time)` and `recharge(time)` (0 to 1 for the button fill), all on the
  simulation clock, never wall time.
- Every enemy attack has a telegraph (a shadow, wind-up, ground ring or line, a sound) that ends in the attack, so
  the player can react.

## Growth

- Growth is tied to food and never jumps. Food is handed in bites to the units whose heads are in reach; a unit has
  a belly 0 to 1 and a size that follows it; a full unit splits or grows after a short visible wind-up (a pinch).
- Cost per growth step rises with the count, so a chicken is a few steps for one unit and a fraction of one for a
  crowd. Check the food supply in the world is enough to reach the cap you set.
- Hunger drains the belly over minutes; a bite resets it. Show a hunger icon only when a fifth of the crowd starves.
- Eaten prey breaks into visible chunks (meat, bones) that the crowd then eats piece by piece. Cap the count
  (desktop and phone separately).

## Opponents and the director

- Opponents unlock over time (birds at about 1 minute, a farmer at 3, a mower at 6), each with a telegraph, an
  attack, a counter the player can learn, and meat when beaten. A pixel toast and an icon show a new kind the first
  time.
- A difficulty director owns spawning. A pressure budget fills at a rate that grows with minutes and with the
  log of the crowd size, and is spent on unlocked opponents (cost and cap per kind, cap in total). After a big fight
  there is a rest. An `adapt` factor (about 0.35 to 1.8) falls with recent losses (decay about 25 s) and rises when
  the crowd grew fast, so weak players are eased and strong players pushed.
- Cheap early opponents fade in weight later so they do not farm the player all game. After a late start time the
  pressure climbs every minute so every run ends.
- All numbers live in one tuning file that a URL flag can override (`?tune=name:value`) for playtests.

## Bot playtests (the balance gate)

- Balance by bots, not by feel. A headless script runs the real game on a manual clock with fixed 1/60 s steps and no
  drawing, with three bots: idle (never moves), simple (steers at the nearest food, no abilities) and good (hunts
  by value, lunges at fleeing prey, dodges at the end of a telegraph, avoids lanes and traps).
- Run several seeds per bot (8 is enough) with a time cap, at below-normal priority, against a served production
  build. Report survival median, min, max, peak crowd and when the cap is reached.
- Targets: idle dies in about a minute, simple in a few minutes, good in 10 to 16 minutes, with no seed where the
  good bot lives to the cap. A bimodal simple bot (some seeds die at the first enemy) means the first minute is
  too hard.
- Re-run after any change to tuning, the director or the opponents. Bots never start the tutorial.
- Seed everything (`?seed=N`) so a failure reproduces.

## Creature motion

- Legless bodies (worms, snakes) push side to side in proportion to speed: a serpenoid path where the head's heading
  swings as a sine of the distance travelled. No sideways slip, and the body is still at rest. Never a time-based
  wiggle on a follow-the-leader spine; it reads as flapping.
- Bodies follow the head's path (a trail of past head positions), slow and smooth-skinned.
- Creatures climb objects and each other with the body following the surface; stacking is capped to a few layers.
  They never pass through rocks, logs or crates, and a pile is overlapping S curves, never spiral coils.
- Seeded per-creature randomness: wavelength, amplitude, speed and hesitation drift slowly, read from noise along
  the distance travelled (shape) or time (pace), never white noise, so a crowd never moves in lockstep.
- Soft-chain physics rigs (dozens of tiny rigid links) are unstable in game physics engines. In Unreal Chaos, links
  of about 2 cm exploded on the first tick and force-driven chains flew apart. Drive the motion kinematically and
  use physics only for contact.

## Tutorial and first load

- In-world labels pinned to things, not a text wall: a pulsing ring ahead with "Move the mouse", an arrow and "Eat"
  on the first food, "Left click to lunge" on the first fleeing prey, and a short slow-down at the first telegraph
  with the spot outlined. Labels are DOM text projected from world points every frame and clamped to the screen.
- First run only (remember it in local storage), a "How to play" link replays it, a visible Skip, and a flag turns
  it off. The director holds real opponents back until the lunge step is done or a minute has passed.
- Pixel loader in the page itself (first paint before any script): the bar fills from the real loading manager and
  the last tenth is "building world". Favicon set (ico, 16, 32, apple-touch), a web manifest, an Open Graph image and
  title and description meta tags.

## Performance

- Draw calls are the usual cost. Merge every multi-box model into one mesh per moving part with vertex colours and
  one shared material; instance repeated things; do not draw or pose creatures outside the camera view (plus a
  margin for their shadows); update the shadow map every other frame.
- Write a perf script that holds the worst case (crowd at the cap, all opponents out) and logs draw calls and
  milliseconds per frame. Budget about 500 to 1000 draw calls and a frame that leaves headroom at 60 fps. The
  headless browser tops out near 57 to 59 fps, so judge by work per frame, not by that number.
- Lower caps on phones. After rendering is cheap, the simulation step is the next cost: profile it.

## Film mode and the post

- A film mode (`?film`, `?manual`) runs on a virtual clock (requestAnimationFrame and the time functions
  overridden) with scripted URL flags for seed, start size and camera pulls, so any frame renders the same and a
  film can be cut from real play. Play mode keeps the real rules.
- Record a real gameplay video of the live build before drafting any post about the game. A post shows play, not a
  render of something the game does not do.

## Deploy

- Static assets only: build to a folder, serve it from a static host (a Worker with an `assets` directory and a
  custom domain works). Cache headers: hashed build files `public, max-age=31536000, immutable`; models, sounds and
  fonts about a week.
- After deploy, open the live URL and check it plays, the loader shows, the OG image resolves and the manifest loads.

## Credits

- A credits page lists every asset with source and licence (CC0 model packs, an open-licence font, CC0 sounds);
  keep a machine-readable `credits.json`. Code under MIT. Do not ship an asset whose licence is unknown.
