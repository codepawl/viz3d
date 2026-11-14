# Quick prototypes and live embeds

<!-- skill-navigation:start -->
## Reading Map

- [Quick prototypes and live embeds](#quick-prototypes-and-live-embeds)
- [Quick prototype](#quick-prototype)
- [Live embed](#live-embed)
- [Publishing as a claude.ai Artifact](#publishing-as-a-claudeai-artifact)
<!-- skill-navigation:end -->

Two needs that the full live app does not cover. Read the section that matches the request.

- **Quick prototype**: a 3D view to show leaders this week, on a machine with no Blender, in about an hour of agent
  time. One pass, models from primitives in three.js, seeded or sample data.
- **Live embed**: the 3D view goes into a dashboard or product that already exists and runs on the company's real
  data. A data adapter, a field mapping, and a component that any page can drop in.

A prototype can grow into an embed: both use the same data model and the same adapter interface, so the swap from
seeded data to a real feed is a config change.

## Quick prototype

Skip Pass 1 and do not ask about Blender. Build everything in one pass in `{{WORK_DIR}}/<topic>/app` with the Pass 2 stack
(Vite, React, React Three Fiber, drei, postprocessing with N8AO) and these cuts. A named look's own rules win over
steps 2 and 3: a Space-time cube draws lines and a map, a Point-cloud survey draws dots, a cutaway plate draws its
plate, and none of them needs props or a dressed ground. Plain three.js without React is fine for those.

1. **One site, one process.** The topic file lists one site, four KPIs and three to five stages. Leave out the site
   switcher and the film unless the user asks.
2. **Ready models first, a kit for the rest.** Take every prop that exists ready-made from the CC0 and CC BY packs
   in `asset-sources.md` (Kenney, Quaternius, Poly Pizza, Poly Haven), chosen to match the style card's shapes:
   boats, trees, rocks, people, vehicles, fences, plants, and the ground itself: a real CC0 ground texture (lawn,
   sand, gravel from ambientCG or Poly Haven) under instanced tuft models (Quaternius "Grass Wispy" and "Tall
   Grass" on Poly Pizza). Never code-built grass blades or a canvas-painted ground: flat triangles with random
   greens read as noise. Build only the subject-specific parts in one file
   `src/kit.jsx`, parametric and at real size (a lock's chamber and gates, a port's quay), with bevels and real
   materials. A scene of plain boxes and capsules is a fail, not a prototype. Build every main asset from the kit against its reference sheet
   (`real-objects.md`): proportions and part count still matter.
3. **The look carries the quality.** The look the user named, else the prototype default in `looks.md` (Choosing),
   Clean ops world: soft shadows, N8AO, a warm key light, a ground
   with real materials, flat colours from one palette. Clean primitives under good light read as a design choice.
4. **A light UI and motion that explains**, as the Pass 2 brief says: few plain buttons, no default dashboard,
   flows and stages animated, and panels added only when the user asks for them. One theme, the look's own palette;
   the three themes come with the full app.
   The 3/4 camera must see into the working part: if a near wall hides it, cut that wall away or raise the camera.
5. **Data the leaders recognise.** Ask for a sample export (CSV or JSON) and its field names. With a sample, map it
   as in "Field mapping" below. Without one, seed a simulation with the real counts and rates from the topic research.
6. **Quality gates**, checked on screenshots against the style reference (`style-reference.md`): shadows and ambient
   occlusion on, with dark contact under every object; no single-colour ground area over a quarter of the frame;
   the surroundings dressed to the card's density; every palette colour from the card; every model the right real
   kind; the side-by-side shows no gap in camera, palette, light or density. Fix and re-shoot until all pass.
   Measure the ground rule with `uv run --no-project --with pillow python {{SKILL_DIR}}/scripts/ground-share.py
   <screenshot>`; it prints PASS or FAIL and the share of the largest flat colour. A look whose design is a flat
   background (the paper of a cutaway plate or space-time cube, the void of a point cloud, white model) passes
   `--ignore "<background hex>"`, and the rest of the frame must still pass. The subject named in the request
   fills at least a third of the default view, measured as the share of the frame covered by the screen-space box of its points (a strait's centre line, a machine's parts): a strait seen as a thin line between hills fails. Measure brightness against the
   reference with `scripts/compare-look.py` (`style-reference.md`, Compare each round).
7. **Done when** the gates pass, the overview, a clicked unit with its card and each stage preset look right in screenshots, it runs
   at 60 fps, the page logs no errors, and `npm run build` gives a static folder that opens from any web server.
   From `self-review.md` run "Each round" and the generic faults that apply to a still view; the film checks apply
   only when the user asked for a film.

Budget about 60 tool calls, unless the user or a brief sets another budget. Report the URL to run it, the screenshots, and what a full build adds (Blender models,
film, more sites).

## Live embed

### Data model and adapters

All data enters through one adapter interface, so the view never knows where it comes from:

```js
// src/data/adapter.js
// connect(handlers) starts the feed and returns a function that stops it.
// handlers.snapshot(state) replaces the whole state; handlers.event(event) applies one change.
// handlers.status({ state: 'live' | 'stale' | 'offline', lastUpdate }) drives the status mark.
```

Always ship `sim:`, `replay:` and the adapter for the source the user named. Add the others when the user asks for
them. The adapter is chosen by a `source` URL or option:

| Source | Adapter | Notes |
|---|---|---|
| `sim:` | seeded simulation | Default when there is no sample data |
| `replay:sample.jsonl` | replay on the page clock | Replays a recorded or sample feed deterministically; the source for the film. A `start` option seeks to an exact record time so a film beat lands on its event |
| `https://…/snapshot.json` | polling REST | Poll every 2-10 s with `If-None-Match`; back off on errors |
| `https://…/events` (SSE) or `wss://…` | stream | Reconnect with backoff; ask for a fresh snapshot after a reconnect |
| `file:` or a dropped `.csv` | CSV | One row per unit or per event; for leaders with only a spreadsheet export |

State has one shape for every source: `sites`, `units` (id, type, site, position or a place name, status, fields),
`tasks`, `events` and `kpis`. The 3D view and the dashboard both read it.

### Field mapping

Put the link between the company's fields and the state in `public/mapping.json`, so a new feed or a renamed column
needs no code change:

```json
{
  "unit": { "id": "asset_id", "type": "asset_class", "status": "state", "position": ["lon", "lat"] },
  "status": { "RUN": "working", "IDLE": "waiting", "FAULT": "blocked" },
  "units": { "speed": "km/h -> m/s" },
  "places": { "Dock 4": [112, 0, -38] }
}
```

Places map names to world positions when the feed has no coordinates. Unknown statuses and types show as a grey
"unknown" mark and are listed in the status panel; they never crash the view.

### Motion between updates

A real feed updates every 1 to 10 s, but motion must stay smooth. Move each unit toward its last reported position
along its path at its reported or measured speed. Extrapolate for at most two update intervals, then hold. A unit with
no update for five intervals fades and shows "stale". The status mark (an icon per state: live, stale, offline) and
"updated 4 s ago" sit in the top bar. Seconds and rates on the KPI cards come from the data, never from the frame rate.

### The component

Build two outputs from the same code: Vite library mode for the component (`build.lib` in the config; the CLI has no
`--lib` flag) and a second build with `embed.html` as its entry:

- **Web component** `dist/viz3d-world.js` for any page, React, Vue or plain HTML:

  ```html
  <script type="module" src="/viz3d-world.js"></script>
  <viz3d-world source="https://ops.example.internal/events" mapping="/mapping.json" chrome="panel" theme="auto"></viz3d-world>
  ```

- **Iframe page** `dist/embed.html?source=…&chrome=…` for dashboard tools that only take a URL (BI tools, internal
  portals, wikis). It talks to the host with `postMessage`: in `viz3d:select`, `viz3d:site`, `viz3d:stage`,
  `viz3d:theme`; out `viz3d:ready`, `viz3d:selected`, `viz3d:kpis`. Check `event.origin` against an allow list.

`chrome` picks how much of the dashboard comes along: `full` (top bar, KPI cards, detail card, timeline), `panel`
(the 3D view with pins, the detail card and the stage bar, for a host that has its own KPI cards) or `none` (the 3D
view and pins only).

Rules for living inside someone else's page:

- Render inside a shadow root and leak no global styles. Inherit the host's font. Read colours from the host's CSS
  variables (`--viz3d-bg`, `--viz3d-fg`, `--viz3d-accent`, `--viz3d-ok`, `--viz3d-warn`, `--viz3d-bad`) with the look's
  palette as the fallback, and follow `prefers-color-scheme` when `theme="auto"`.
- Size from the element with a `ResizeObserver`; never assume the window. Cap the pixel ratio at 1.5.
- Stop rendering when the element is off screen (`IntersectionObserver`) or the tab is hidden. Dispose every
  geometry, texture and the renderer when the element is removed, so a host that mounts it twice does not leak.
- Keyboard shortcuts work only while the element has focus.
- Without WebGL, show the same data as a table with the status marks.

### Security

The component is read-only. It never holds a secret: tokens and API keys stay on the host's backend, which proxies
the feed or signs a short-lived URL. Never put credentials in `mapping.json`, the bundle or a query string. Personal
data (driver names, patient names) is shown only when the feed already sends it to that page's users.

### Checks

1. Run `node {{SKILL_DIR}}/scripts/mock-feed.mjs --port 8787 --file sample.jsonl` (it replays a JSONL file of records
   with a `t` field as SSE at `/events` and the latest state at `/snapshot.json`), point the component at it, and
   screenshot it live.
2. Stop the mock feed: the mark turns stale, then offline, and the view keeps the last state. Start it again: it
   recovers without a reload.
3. Put the component in a plain host page twice, at 1200x700 and 600x400, in light and dark host themes. Look at each
   screenshot for clipped UI, wrong colours and text that wraps.
4. Unmount and mount it ten times and check that the WebGL context count and memory stay flat.
5. Record a film of the host page with the component inside, driven by `replay:` (or `sim:`) on the virtual clock
   (`film.md`). Keep the camera drifting slowly (about 0.05 rad/s) during holds: a still camera over a still frame
   gives repeated frames.

Trap from the first build: React StrictMode mounts effects twice, so movers and pins registered in an effect were
registered twice and the pins hid. Make every registry idempotent (keyed by unit id) or leave StrictMode off in the
component entry.

## Publishing as a claude.ai Artifact

Measured on a real walk-through page:

- Artifacts refuse `.glb`, `.gltf` and `.bin` files under any content type. Ship each model as glTF JSON, named
  `<name>.gltf.json`, with the buffer embedded as base64.
- The page's CSP blocks `fetch()` of `data:` URIs. GLTFLoader cannot read that embedded buffer by itself, and the page
  shows "could not load" with no console error you can see. In the page, fetch the JSON, decode the buffer, rebuild a
  GLB in memory and call `gltfLoader.parseAsync`.
- Each text file may be 16 MB at most after base64, which adds about a third. Split big scenes and load the rest on
  first use. Textures go as `.webp` files and audio as `.mp3`. Skip Draco and KTX2, because their decoders fetch wasm
  from other hosts.
- Check the published page in a signed-in Chrome, because a built-in browser may not be signed in. When the Chrome
  window is hidden behind another app, `requestAnimationFrame` drops to about 1 fps. Judge motion from local
  Playwright runs, not from that tab.
