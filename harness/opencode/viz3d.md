---
description: Visualize anything in 3D with the visualize-in-3d skill
---

Load the visualize-in-3d skill and follow it from the start for this request:

$ARGUMENTS

If the request is empty or is "help", list the modes and looks below and ask what the user wants to make 3D. Otherwise, if the first word is a mode, use that shape and drop the word from the subject; if the request names a look, use that look, else the default look for the shape.

Modes: film or doc (documentary film), action (action short), showcase (film or stills that show off one object or model), app (live 3D app with a dashboard and a short film), lesson (a real object built and explained step by step), book (illustrated cutaway plate, or a book with quizzes), game (playable browser game), prototype (quick prototype from primitives), embed (live 3D view inside a dashboard, on real data). With no mode, pick the shape from the subject with the skill's table.

Looks: clean product (ops, toy, lived-in), real and cinematic (terrain, documentary, white model, layer build), technical (point cloud, plate), stylized art (pixel, ASCII, glow). A look word may be two words, such as "white model", and may come first when there is no mode. A look the user names always wins over the default. Look words match whole words in any case, longest first. Text in quotes is always the subject. With no mode, a look that fits only one shape settles it; otherwise ask one question naming the shapes that fit.
