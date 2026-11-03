# viz3d

Some things are hard to understand from text, a spreadsheet or a two-hour documentary. How does an airport turn a plane
around in 45 minutes? What does an ER do with ten arrivals at once? How does a metro keep trains two minutes apart, or
a toll gantry charge a truck at full speed? Why did a reactor explode at 01:23?

This skill has your agent turn questions
like these into a 3D world you can watch or click through. The world is built from researched facts and from models
made to real dimensions.

<table>
  <tr>
    <td width="200">
      <a href="https://67js.codepawl.com">
        <picture>
          <source media="(prefers-color-scheme: dark)" srcset="https://67js.codepawl.com/brand/wordmark-dark.svg?v=0.10.0" />
          <img src="https://67js.codepawl.com/brand/wordmark-light.svg?v=0.10.0" alt="67js" width="160" />
        </picture>
      </a>
    </td>
    <td>
      Films and stills render in <a href="https://github.com/codepawl/67.js"><b>67js</b></a>, our WebGL2 engine that
      agents drive through an MCP server: JSON scene recipes, PNG review grids, and GPU or CPU export to images and
      video with bounded memory. viz3d works without it, and looks better with it. See
      <a href="#films-and-stills-with-67js">Films and stills with 67js</a>.
    </td>
  </tr>
</table>

It has eight modes:

- **Live app**: a three.js app with a dashboard around a 3D world of the place. A seeded simulation moves the units and
  the numbers. The agent records a 30 s film by driving the app with real clicks on a virtual clock.
- **Documentary film**: a 2 to 4 minute film of an event, told in order. It is built from a sourced fact file, a map,
  block-built scenes and flat glowing figures. Captions are timed for reading, and the score changes with the story.
- **Quick prototype**: a live app in one pass from three.js primitives, with no Blender. Use it when you need something
  to show your leads this week.
- **Live embed**: the 3D view as a web component (`<viz3d-world>`) or an iframe page that goes into the dashboard or
  product you already have. It reads your real data from REST, Server-Sent Events, WebSocket or a CSV export through a
  field mapping file, so a new feed needs no code change. Tokens stay on your backend.
- **Lesson app**: a step-by-step lesson on a real object at real size, such as an Arduino and a breadboard. Parts and
  wires plug in as they do on a desk. The highlighted code line is what the board does right now. A free bench lets
  the learner build their own circuit.
- **Action short**: creatures, machines or characters doing something, such as a fight, a chase or a launch. Every
  move is planned beat by beat, and every hit lands on a visible contact. The agent checks the frames for hidden or
  mistimed actions before it shows you the film.
- **Book**: an illustrated cutaway plate of one big object or building, such as a liner or a castle, in 3D. You orbit
  it, read the margin labels and fly into any room, each full of small people at work. Several subjects make a
  page-turning book with a short quiz on each page.
- **Game**: a free browser game people play. The player steers one creature or unit through an open world that pushes
  back, grows by playing, and starts again from a death card. Bots play it before you do, to balance it and to find
  stuck states.

| Live app | Documentary film |
|---|---|
| ![A canal lock app: a container ship selected, its card open on the right, and the stage timeline at the bottom](docs/images/live-app.jpg) | ![A documentary map: a red route from a farm to a hardware store across a county](docs/images/documentary.jpg) |
| **Quick prototype** | **Live embed** |
| ![An electric bus depot built from three.js primitives, with pantograph chargers over the buses](docs/images/quick-prototype.jpg) | ![A transit company dashboard with the 3D depot view inside it, a bus card open and a live status mark](docs/images/live-embed.jpg) |
| **Lesson app** | **Stage cameras** |
| ![An Arduino lesson: an LED fading on a breadboard, the current code line highlighted and the PWM signal drawn on the right](docs/images/lesson-app.jpg) | ![A metro app with the stage bar at the top and the speed controls at the bottom](docs/images/stages.jpg) |

A real place starts from its real layout. The agent draws the plan from OpenStreetMap data and
builds the 3D world on the same coordinates, so the two line up. Things then work as they do in reality. Aircraft
follow the taxiway centre lines and give way to each other. Jet bridges and service vehicles attach to the real doors
and ports, and the agent measures every gap before it records.

![Singapore Changi: the aerodrome plan drawn from OpenStreetMap on the left, the same layout in 3D on the right](docs/images/real-place.jpg)

Every live app has stage cameras on number keys, a guided tour, follow camera and playback from 0.25x to 10x, as in
the metro app above.

There are twelve looks:

| Look | Fits |
|---|---|
| Clean ops world | The default for a system that runs: a white-grey world with one accent colour, framed like a real operations product |
| Toy isometric | A friendly diorama of a place or system |
| Lived-in isometric | Ordinary buildings where people live or work and a crisis plays out inside |
| Point-cloud survey | A scanned, technical view of land, sea or a site |
| Photoreal terrain | Something spreading over real land, such as a wildfire or a flood |
| Dark documentary | A case or an event told as a film |
| White model documentary | A case told as an architect's white model |
| Pixel diorama | Pixel-art sprites on a 3D stage, for battles and small worlds |
| Illustrated cutaway plate | One big object or building cut open, for the book mode |
| Dither + ASCII showcase | A film that shows off a model, a tool or a product: the model stays clean, the world around it turns to ASCII |
| Gradient glow ASCII | A creature or object that is itself the art, drawn in glowing ASCII |
| Layer build film | One locked aerial camera while a place is built up layer by layer |

Name a look in your request, or let the agent pick one from the subject.

## What is new

- Films and stills render in [67js](https://github.com/codepawl/67.js) when it is installed.
- The `game` mode: a playable browser game, balanced by bot playtests.
- Six more looks: clean ops world, lived-in isometric, white model documentary, Dither + ASCII showcase, gradient glow
  ASCII and layer build film.
- A longer self-review fault list: contact and support checks, camera flights measured against every mesh, vehicles
  that steer and roll like the real ones, and sound faults.
- A fast low-quality preview of the whole film goes to you first. The full render waits for your sign-off.

## Install

In Claude Code, add this repository as a plugin marketplace and install the plugin:

```text
/plugin marketplace add codepawl/viz3d
/plugin install visualize-in-3d@codepawl
```

From a shell, the same two steps are:

```bash
claude plugin marketplace add codepawl/viz3d
claude plugin install visualize-in-3d@codepawl
```

For Claude Code, Codex, Cursor and other agents that read skill folders, use the [skills CLI](https://github.com/vercel-labs/skills):

```bash
npx skills add codepawl/viz3d
```

To install by hand, copy both folders in `plugins/visualize-in-3d/skills/` (`visualize-in-3d` and the `viz3d`
command) into your agent's skills folder:

| Agent | Skills folder |
|---|---|
| Claude Code | `~/.claude/skills/` |
| Codex | `~/.agents/skills/` |
| Cursor | `~/.cursor/skills/` (it also reads `~/.claude/skills/` and `~/.agents/skills/`) |
| Gemini CLI | `~/.gemini/skills/` |
| OpenCode | `~/.config/opencode/skills/` |

Gemini CLI and OpenCode take slash commands from their own folders. To get `/viz3d` there, also copy the command file:

| Agent | Copy | To |
|---|---|---|
| Gemini CLI | `harness/gemini/viz3d.toml` | `~/.gemini/commands/` |
| OpenCode | `harness/opencode/viz3d.md` | `~/.config/opencode/commands/` |

## Use

Start it with the command, a mode and the subject:

```text
/viz3d film the 1906 San Francisco earthquake
/viz3d app a container port
/viz3d action two mechs fighting in a flooded city
/viz3d book the Titanic
/viz3d game a worm that eats its way through a city
```

| Mode | What you get |
|---|---|
| `app` | Live app with a dashboard and a 30 s film |
| `lesson` | Lesson app that builds a real object step by step |
| `prototype` | Quick prototype from three.js primitives, no Blender |
| `embed` | Live embed for your dashboard, on your real data |
| `film` | Documentary film |
| `action` | Action short: creatures, machines or characters doing something |
| `book` | Illustrated cutaway plate of one subject, or a page-turning book of several, with quizzes |
| `game` | Playable browser game, balanced by bot playtests |

Leave the mode out and the agent picks one from the subject. How you type the command depends on the agent:

| Agent | Command |
|---|---|
| Claude Code, plugin install | `/viz3d` (or `/visualize-in-3d:viz3d` when another plugin also has a `viz3d`) |
| Claude Code, skills folder | `/viz3d` |
| Codex | `$viz3d`, or pick it from `/skills` |
| Cursor | `/viz3d` |
| Gemini CLI, OpenCode | `/viz3d`, after you copy the command file |

You can also just ask for what you want to see, for example:

- "Visualize how a container port works."
- "Show how a city metro keeps its trains apart."
- "Build Singapore Changi Airport from its real layout and show a turnaround."
- "Make an Arduino lesson app that goes one circuit at a time."
- "Make a documentary-style 3D film of the 1906 San Francisco earthquake."
- "Make a quick 3D prototype of our warehouse for Monday's leadership review. Here is last week's CSV export."
- "Put a live 3D view of our fleet in our ops dashboard. The feed is at /api/fleet/events."

The agent writes a topic file first, then builds the models, then the app or the film. It checks its own film on
contact sheets before it shows you anything.

For a live embed, the agent builds a web component and an iframe page. Put the component in any page and point it at
your feed:

```html
<script type="module" src="/viz3d-world.js"></script>
<viz3d-world source="https://ops.example.internal/events" mapping="/mapping.json" chrome="panel"></viz3d-world>
```

`mapping.json` links your field names and status codes to the 3D view, so a new feed needs no code change. For a tool
that only takes a URL, use `embed.html?source=...` in an iframe. To test without your real system, the skill's
`scripts/mock-feed.mjs` replays a JSONL file as a live feed.

## Films and stills with 67js

Apps, lessons, embeds and games stay in three.js, because people click and steer them. Documentaries, action shorts,
cutaway films, showcase films and stills render in [67js](https://github.com/codepawl/67.js) when it is installed:

- Terrain, scanned trees and grass, baked liquid, vehicles on paths, skinned characters, HDRI light and baked room
  light come as addons.
- The agent builds the scene as a JSON recipe through MCP and checks it on labelled review grids. It tries two or
  three looks as branches and shows you the grid to pick from.
- A timeline of shots with fades and depth of field drives the clock, so any frame renders the same in any order.
- Render jobs export PNG and MP4 with the soundtrack and an audio sync check. Memory is planned before it is used.

Set it up in your project:

```bash
npm install 67js@npm:@codepawlhq/67js
```

```bash
claude mcp add 67js-scene -- npx --package @codepawlhq/67js 67js-mcp --backend gpu --memory 256
```

```bash
npx skills add codepawl/67.js
```

The last command adds the 67js skills (`build-67js-scene` and `render-67js-media`). The skill's
`references/67js.md` has the full workflow, Windows notes and the faults we have seen. Showcase and docs are at
[67js.codepawl.com](https://67js.codepawl.com). If viz3d is useful to you, a star on
[codepawl/67.js](https://github.com/codepawl/67.js) helps the engine behind it.

## What you need

- Node 20 or later, with Playwright and Chromium for recording.
- ffmpeg on your PATH.
- A GPU that runs WebGL2 at 1080p.
- [Blender](https://www.blender.org/download/) 5.x is optional. It gives much better models for the full live app and
  the documentary. Without it the skill builds the models in three.js and tells you the quality is lower. Quick
  prototypes and embeds never need it.
- [67js](https://github.com/codepawl/67.js) is optional. It renders the films and stills, as described above.

The skill asks before it downloads anything, such as elevation data, map data or reference images.

## Also in this repository

**build-minecraft-model-from-image** turns a picture of an object into a Minecraft-style 3D model. The agent looks at
the picture and writes the model as code: a few cuboids with pixel textures, not a fine voxel grid and not an
image-to-3D network. You get a GLB, a viewer page, renders from every side and a sheet that compares them with the
picture. It needs Python through [uv](https://docs.astral.sh/uv/) and Blender 5.x for the renders.

![Four photos with the block model built from each: an iron kettle, an armchair, a rubber duck and a pink fire hydrant](docs/images/minecraft-model.jpg)

```text
/plugin install build-minecraft-model-from-image@codepawl
```

Photo credits for the picture above and the skill's `examples/`: kettle and armchair by Auckland War Memorial Museum
(armchair photo by Gerald E Jones), CC BY 4.0. Rubber duck by Julian Lupyan, CC0. Fire hydrant by Tournasol7, CC BY 4.0.
All from Wikimedia Commons.

**build-house-from-plan** turns a 2D house plan into a photoreal 3D house. The agent reads the walls, doors, windows and
scale off the drawing into a plan file. A check overlays the built walls on the drawing's ink and fails when they do not
line up. The house gets measured wall thickness, real frames and glass, CC0 scanned materials and real furniture models,
and renders in Blender Cycles. You get stills, a film of the walls rising off the drawing, and whole streets. It needs
Python through [uv](https://docs.astral.sh/uv/), Blender 5.x and a GPU.

![From a public domain drawing to a house and a street](docs/images/house-from-plan.jpg)

```text
/plugin install build-house-from-plan@codepawl
```

The plans behind the picture are public domain: Historic American Buildings Survey and Historic American Engineering
Record sheets from the Library of Congress, and a USDA plan. Furniture includes CC BY models listed in the skill's example.

## Contributing

Faults you saw, new looks, example topics and harness adapters are welcome. Read
[CONTRIBUTING.md](CONTRIBUTING.md). Coding agents read [AGENTS.md](AGENTS.md).

## License

MIT
