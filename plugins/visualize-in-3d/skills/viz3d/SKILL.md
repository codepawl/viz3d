---
name: viz3d
description: Start the visualize-in-3d skill from a command, with an optional mode and look first and then the subject, for example "/viz3d film white model the 1906 San Francisco earthquake". With no request it shows the menu of modes and looks.
argument-hint: "[app|lesson|prototype|embed|film|action|showcase|book|game] [look] <subject>"
disable-model-invocation: true
---

# viz3d

The user started viz3d with this request:

$ARGUMENTS

In tools that do not fill in the line above, the request is the rest of the user's message.

1. If the request is empty or is `help`, show the menu below as it is, then ask one question: what do you want to
   make 3D? Stop there.
2. Otherwise load the `visualize-in-3d` skill and follow it from the start. It is installed next to this one
   (`../visualize-in-3d/SKILL.md`).
3. If the first word is a mode, use that shape and drop the word from the subject. Otherwise pick the shape from the
   subject with the skill's table.
4. If the request names a look, use the matching section of `references/looks.md`. Otherwise use the default look for
   the shape (looks.md, Choosing).

## Menu

**Modes**, by what you want people to do with it:

| Watch it | Explore it | Put it in your product |
|---|---|---|
| `film` or `doc`: documentary film of a story or event | `app`: live 3D app with a dashboard and a 30 s film | `prototype`: quick prototype from primitives, no Blender |
| `action`: action short, things fighting, chasing, launching | `lesson`: a real object built and explained step by step | `embed`: live 3D view inside your dashboard, on your data |
| `showcase`: a film or stills that show off one object or model | `book`: illustrated cutaway plate, or a book with quizzes | |
| | `game`: playable browser game | |

**Looks**, in four families:

| Clean product | Real and cinematic | Technical | Stylized art |
|---|---|---|---|
| ops, toy, lived-in | terrain, documentary, white model, layer build | point cloud, plate | pixel, ASCII, glow |

Examples: `/viz3d app a container port`, `/viz3d film white model the Chernobyl accident`,
`/viz3d showcase glow a cockroach`, `/viz3d game pixel a worm that eats a city`.
