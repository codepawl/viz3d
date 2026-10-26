---
name: viz3d
description: Start the visualize-in-3d skill from a command, with an optional mode first (app, lesson, prototype, embed, film, action, book) and then the subject, for example "/viz3d film the 1906 San Francisco earthquake".
argument-hint: "[app|lesson|prototype|embed|film|action|book] <subject>"
disable-model-invocation: true
---

# viz3d

The user started viz3d with this request:

$ARGUMENTS

In tools that do not fill in the line above, the request is the rest of the user's message.

1. Load the `visualize-in-3d` skill and follow it from the start. It is installed next to this one
   (`../visualize-in-3d/SKILL.md`).
2. If the first word of the request is a mode, use that shape and drop the word from the subject:

   | Word | Shape |
   |---|---|
   | `app` | Live app with a dashboard and a short film |
   | `lesson` | Lesson app that builds a real object step by step |
   | `prototype` | Quick prototype from primitives, no Blender |
   | `embed` | Live embed for an existing dashboard, on real data |
   | `film` or `doc` | Documentary film |
   | `action` | Action short |
   | `book` | Illustrated cutaway plate of one subject, or a book of several with quizzes |

   Otherwise pick the shape from the subject with the skill's table.
3. If the request names a look (toy, point cloud, terrain, documentary, pixel, plate), use it. Otherwise the skill picks one.
4. If the request is empty, ask one question: what do you want people to see?
