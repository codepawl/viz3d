# Learn the style from a reference

A look written only in words comes out generic: flat grey ground, one object in the middle, default light. Every
build starts from a real picture of the style it aims for, and every self-review round compares the render with
that picture. Reading map: Find the reference, Capture it, Write the style card, Build to the card, Compare each
round, Copy the style, not the work.

## Find the reference

1. **The user's reference wins.** Use the image, video, live page or post link that the user gives.
2. **Otherwise find two or three.** Search where people share finished 3D work: X (posts with many bookmarks),
   Dribbble, Behance, ArtStation, Awwwards, Sketchfab, YouTube. Search by the look and the shape, not only the
   subject: "isometric stylized water three.js", "cutaway diorama", "ops dashboard 3D". Prefer pieces with a live
   page or a video, so you can study the motion and interaction too.
3. **Let the user pick.** Show the candidates side by side with one line each on what each one brings. If the user
   is away, pick the piece with the most engagement. Its camera and density must fit the subject. Say why.
4. A look from `looks.md` is still chosen for its rules (camera kind, UI, traps). Where the reference and the
   look's default disagree on palette, light, materials or density, the reference wins.

## Capture it

- A page: screenshots at the size the build will run, from the default view and one or two others. Note what moves,
  what the pointer does and what the UI holds.
- A video: frame sheets with `scripts/contact-sheet.sh <video> <folder> <fps>`.
- Keep the captures in `{{WORK_DIR}}/<topic>/reference/`. They are study material and never ship.

## Write the style card

Write it into the plan file before anything is built. Each line is a value that a review checks the build against:

| Line | What to write |
|---|---|
| Camera | Angle from the ground in degrees, field of view, how much of the frame the subject fills |
| Palette | Five to eight colours sampled from the capture as hex, each with where it is used |
| Light | Direction and colour of the key light, softness and length of shadows, how dark the contact shadows are |
| Materials | How each surface reads: painted, glossy, textured, flat; the roughness range |
| Density | What fills the frame around the subject and roughly what share of it; no empty ground left over |
| Shapes | Soft or hard edges, rounded or bevelled, stylized or real proportions |
| Motion | What moves without input (water, leaves, people) and how fast |
| UI | Where it sits, its type, its corner radius, how much of the screen it takes |

## Build to the card

Turn every line into settings before the first render. That means camera values, the palette as constants, light
and shadow settings, the material list, and the set dressing list that gives the density. Pick models that already have the card's
shapes (`asset-sources.md`) instead of reshaping primitives toward them.

## Compare each round

Each self-review round renders the build from the reference's camera (its angle and field of view, at a distance
where the subject fills the same share of the frame) at the same size and puts the two side by
side in one image. Write the three biggest gaps, each tied to a card line ("ground is one flat colour, card says
grass with flowers and stones"), fix them, and render again. A round passes when no gap is about the card's camera,
palette, light or density. Show the user the side-by-side, not the render alone.

## Copy the style, not the work

Learn the camera, palette, light, density and feel. Never copy its models, textures, logos, names, layout of a
signature scene or its text. Credit the reference in the report ("style studied from <link>"). When the user asks
for a close remake of someone's piece, say whose it is and ask whether they have the right to use it.
