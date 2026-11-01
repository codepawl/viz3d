# Faults that make a built house look fake

Each entry was seen on a real render from this pipeline. Read the group you are judging, then look for it at full size.

## Reading map

- Light: "Light". Walls and roof: "Surfaces". Lawn and sky: "Site". Inside: "Rooms". Numbers wrong: "Build".

## Light

- **Rooms dark, needing 8 stops.** Refractive glass with caustics off drops every bounce that crosses it. Only camera rays
  see real glass now, the rest pass a clear tint. Measured on the cottage living room: median 0.0002 to 0.0016.
- **A room lit flat and grey.** The sun missed every window you can see. Set `site.sun.azimuth` so sun lands on the walls in
  the hero shot and through a window in the main room.
- **Walls smeared like foil, half the room black.** Too few light paths find a window, and the denoiser paints over the gaps.
  Sky portals did not help, flipped or not (Holten hall median stayed 0). A soft lamp filling each window, hidden from the
  camera, took the median to 0.0064 and the mean from 0.002 to 0.012. Tune it with `site.window_sky`.
- **Interior exposure guessed per shot.** Rooms differ by stops. Interiors meter themselves. Leave `exposure` for taste.
- **Exterior with a black side.** Sun behind the visible faces. Turn the sun, not the exposure.

- **White rectangles over the view in a window.** The window lamp shows in the glass. Hide it from glossy and transmission
  rays as well as the camera.

## Surfaces

- **Inside walls read as grey concrete or foil.** Scanned plaster keeps its blotches at any tile size, and from inside a room
  they fill the frame. A painted wall is a plain colour drifting by a few percent. Use `wall_paint` or `wall_paint_old`, or
  real boards where the house had them.
- **A model comes out pure white.** Its textures are missing. Give the item `paint` with a material name.

- **Siding a dark chocolate block.** Scanned plank textures are dark before any tint. Lift the tint and desaturate, then
  compare with a photo of the same material in daylight.
- **Wood floor with narrow modern strips in an old house.** Pick wide boards and check tile size against the room.
- **Rug or curtain reads as plastic.** Textile set with no fibre detail. Use a real fabric scan at a small tile (0.2 m for
  linen) and pale tint.
- **Roof reads as a flat colour.** Too small a shingle texture, seen as noise from far away. Keep real shingle courses in
  the mesh and let the texture add wear.
- **Fireplace as a painted box.** Give it a real `firebox` depth, brick inside, hearth, mantel and tools.

## Site

- **Lawn as a green sheet.** Flat texture from any low angle. Use tufted grass by instancing, a ground texture beneath, and
  density falling with distance.
- **Path as a smooth plank.** A strip with straight edges and big tile. Use uneven edges, conform it to the ground, use a
  smaller tile or a worn dirt-and-grass scan.
- **White patches on grass, a pale strip at the horizon.** The scanned ground's roughness map mirrors the sky at low angles.
  The ground is now matte, with no roughness map.
- **Grass growing through a road or floor.** Excluding it per blade took 1287 s on the street. A 4 m grid of polygons took
  127 s and looks the same.
- **Empty strip at the horizon.** The ground ends in clean sky. Add a treeline of 110 or more trees, set `ground_size`
  well past it. Use a list of rings when one ring leaves gaps.
- **Black seam along a kerb.** Road and pavement were flat faces at different heights. Build them as slabs.
- **Doorway or window a black hole from outside.** The room behind it had no light. Keep the window lamps on for exteriors.
- **White siding renders grey.** The scan is dark before any tint. A tint above 1.0 is fine, check it beside a photo.
- **Disc edge in a high aerial.** The ground has an end. Keep the camera low enough that the treeline hides it.
- **Pines and firs.** The scanned pine takes many minutes to import. Use broadleaf trees unless the place demands them.
- **House floating or sunk.** Set `site.ground_level` from the drawing's steps, and let the plinth show.

## Rooms

- **Sofa or chairs facing the wall.** Model orientation assumed. At `rot: 0` a model's front faces -y. Check on the grid
  with `preview_assets.py` before placing.
- **A model at the wrong size.** Objaverse units vary. Always use `fit_w`, `fit_h` or `fit_size` with a measured size.
- **A row of plants in one pot.** Poly Haven plant files hold several variants. Use `part` to keep one.
- **Modern fridge in a 1950s kitchen.** Pick period models and look at them beside a photo of the period. Search by several
  words ("vintage", "retro", the maker).
- **A washing machine with its door open, a toilet with a broken lid.** Scanned or sculpted models carry odd states. Look at
  the model before placing it.
- **Empty rooms.** A room with one object reads as a game level. Add curtains, a rug, a lamp and what the room is used for.
- **Beds floating, models the wrong size.** A linked model's matrix is stale until `view_layer.update()`, so its bounding box
  lies. Update before measuring.
- **Black or blank slab filling part of the frame.** The camera stands inside a wall or behind a door leaf. Check every shot
  in a preview before a final render.
- **Upper floor hiding the room in a cutaway, or one cut ignored.** Cuts must slice `floors` as well as walls. Shots run
  uncut first, then highest cut down, and recut when the height changes.

## Build

- **As-built score below the plan score.** Wall ends or a stub misread. Open `check_asbuilt_overlay.png` and read which
  wall is off.
- **Door check failing on an upper floor.** A door's head is measured from its own sill.
- **Build over 5 minutes.** glTF import. Models cache as linked `.blend` files after their first import.
- **Film over 20 s a frame at 20 samples.** Writing `hide_render` or a scale that did not change still tags the scene, and
  Cycles rebuilds it. The build-up film writes only values that changed.
