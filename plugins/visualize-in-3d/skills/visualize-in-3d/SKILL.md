---
name: visualize-in-3d
description: Turn anything hard to picture into a 3D world people can watch or play with - an operation or system (airport, data center, port, factory, hospital), an event spreading over real land (wildfire, flood), a story in time (a historical event, a case), characters or machines in action (a fight, a chase, a launch), or how a thing works. Builds a live three.js app with a dashboard and a 30 s film, a lesson app, a quick no-Blender prototype, a live embed that runs on real data inside an existing dashboard, a documentary film, an action short, or an interactive cutaway plate or book. Looks include toy isometric, point cloud, photoreal terrain, dark documentary, pixel diorama and illustrated cutaway plate. Models come from ready sources or Blender builds made from real references, and the skill checks its own frames before showing anyone. Use for "visualize how X works", "show this event on a 3D map", "a live 3D dashboard of X", "a 3D lesson on how X works", "a documentary-style 3D explainer", "a quick 3D prototype", "two creatures fight in 3D", "app nhìn như game", "làm phim 3D về", "cho 2 con đánh nhau", "pixel battle", "theme point cloud", "kiểu wildfire tool".
license: MIT
---

# Visualize in 3D (Dựng thế giới 3D để thấy mọi thứ vận hành)

If `references/local.md` exists, read it first: it sets the folders and house rules for this machine.

Take any subject and make it visible in 3D: models from real references, a seeded simulation or a scripted timeline
driving them, a look chosen for the subject, and a film checked frame by frame. The user can also start it with
`/viz3d <mode> <subject>` (modes: app, lesson, prototype, embed, film, action, book, game).
Paths use `{{WORK_DIR}}` for the folder where projects live (the current directory unless the user names one) and
`{{SKILL_DIR}}` for this skill's folder. Write paths with forward slashes on every platform.

## Before you start

1. **Blender** (not needed for a quick prototype, an embed, or the pixel look): run `blender --version` or look in
   the usual install folder. If it is missing, say it gives much better models, is free at blender.org, and ask
   whether to wait or go on without it. Without it, follow `references/no-blender.md` and say in the report that
   model quality is lower.
2. **Node 20+ and Playwright with Chromium** for recording; **ffmpeg** for encoding and checks.
3. **Subagents:** where the harness has them, give each pass to a fresh subagent with its brief and keep it inside
   about 80 tool calls. Where it does not, run the passes one after another in this session, finish and check one
   before starting the next, and re-read the plan file at the start of each.
4. **Downloads** (elevation, map data, models, reference images, sounds): name the source, count and rough size,
   and get the user's OK first.

## 1. Pick the shape

Read what the user wants people to see, then pick one shape (or combine two) and read its reference:

| The subject is | Shape | Read |
|---|---|---|
| A place or system that runs (units, tasks, flows) | Live app with dashboard and a 30 s film | `references/brief.md`, `examples/` |
| How a thing works (aircraft, circuit board, engine) | Lesson app: 3 to 5 lessons, one control each, a "Build your own" sandbox | `references/brief.md` (parts, flow overlays, sandboxes) |
| Something spreading over real land | Terrain app with a time scrubber | `references/looks.md` (photoreal terrain), `examples/wildfire-valley.md` |
| A story, case or piece of history | Documentary film | `references/documentary.md`, `references/film.md` |
| Characters, creatures or machines doing something | Action short | `references/action.md` |
| One object cut open or exploded | Cutaway film, or an app with a section view | `references/film.md`, `references/looks.md` |
| One big object or building with many rooms, as a page or a book | Book: interactive illustrated cutaway plate, with quizzes | `references/book.md`, `references/looks.md` |
| A game people play in the browser (steer a creature, survive, grow) | Playable web game, bot-balanced | `references/game.md` |
| A demo for leaders in about an hour | Quick prototype from three.js primitives | `references/live-embed.md` |
| A live view inside an existing dashboard or product | Embed (web component or iframe) on real data | `references/live-embed.md`, `scripts/mock-feed.mjs` |

Pick the look in `references/looks.md` (Choosing): clean ops world (default for a system that runs), toy isometric, point cloud, photoreal terrain, dark documentary
pixel diorama or illustrated cutaway plate. Study a look the user shows from a reference video with timestamped frame sheets
(`scripts/contact-sheet.sh <video> <folder> <fps>`), then write it up as a new section in `looks.md`.

## 2. Write the plan file

Write one file in `{{WORK_DIR}}` before anything is built: the topic file for an app (the `examples/` shape), the
fact file for a documentary, the action sheet for an action short. It names the real parts of the subject, what
moves or changes, the beats or features to show, the look, and the camera view that shows the subject best (a
cutaway for depth, top-down for flows, low side for arrivals).

Research the real subject first: real dimensions, steps, rules and moves. Use made-up names for companies and
people unless the user asks for real ones. For a real named place, follow "A real place" in
`references/real-objects.md`.

## 3. Pass 1: assets and stage

Models follow `references/asset-sources.md`: ready models first, then scans, packs, AI-generated models, and
Blender builds from a reference sheet (`references/real-objects.md`). The pass reports stills at film scale.

## 4. Pass 2: build and film, with the self-review loop

Build the app or the film from the plan file with the brief in `references/brief.md`. Before reporting, run
`references/self-review.md` for up to three rounds: `scripts/frame-guard.js` measurements, frame sheets and the
mode's fault list. Run the two passes separately; one pass doing both runs too long.

## 5. Check, then show

Open the final sheets and peak stills yourself (`scripts/contact-sheet.sh`, sheets newer than the video). Look for
what the loop can miss: a subject wrong for the real thing, a dull beat, broken UI rules, toys or programmer art.
Every fault the user or you find that the loop missed goes into the fault lists the same turn
(`self-review.md`, Growing the lists).

## 6. Polish

Give fixes to one more pass with "everything else is approved, change nothing else", then re-record. Publish only
on the user's word.

## Rules

- Original names and designs by default. Real brands, liveries and known characters only when the user asks, with
  licensed models and a credit line.
- Every main asset matches a reference of the real thing. Models from memory read as toys.
- Every frame is a function of time (a virtual clock, clips set from it), so any frame renders the same in any
  order. Real clicks on that clock drive an app's film, not a camera moved in code.
- Render and encode at low priority, one heavy job at a time, and stop every server you start.
- Real people and real harm: facts from sources, victims named with respect, no gore (`references/documentary.md`).
- Reference images and videos are for study only: never ship them in the app or the film.
- The public copy of this skill is mirrored from this folder. Edit only this folder; never put personal paths, names
  or tools outside `references/local.md`. A nightly sync script mirrors the rest.
