# Modelling from real references

Models drawn from memory come out as toys: wrong proportions, missing parts, generic silhouettes. Every main asset
is modelled from a reference sheet of the real thing. Reading map: Reference sheet, Modelling to the sheet, Hero models, Compare
renders, A real place, Terrain, Sources and rules.

## Reference sheet

Before modelling, Pass 1 writes `blender/refs/<asset>.md` for every main asset (anything the camera gets close to
or the film selects):

- **What it is in the real world:** the class of object it stands for (for example "ship-to-shore gantry crane,
  post-Panamax", "Suezmax crude tanker"), so the design follows a real type without copying a brand.
- **Dimensions:** overall length, width, height and the key sub-dimensions (wheelbase, boom reach, hull draft,
  deck height), each with its source. Two independent sources for the overall size.
- **Proportions:** the ratios that make it recognisable (tanker length to beam about 5.5:1, superstructure aft,
  crane legs to boom height), written as numbers.
- **Parts list:** every visible part from front, side, top and back, in order, with the ones that move.
- **Images:** 3 to 6 reference views (side, front, three-quarter, top, a detail) saved as files in
  `blender/refs/<asset>/` with their source URL and licence in the md file. Look at each one before modelling.

## Modelling to the sheet

- Block out first at real size in metres from the dimension table, with a reference image set as a camera
  background or an image empty for side and top views; check the blockout's silhouette against the side view
  before adding any detail.
- Detail in order of what the camera sees: silhouette, then large forms, then panel lines and small parts.
- Scale the details too: railings, stairs, doors and windows sized from a 1.8 m person placed next to the model.
- Colours and materials from the reference photos (sampled, then shifted to the look's palette), not invented.

## Hero models

The objects the viewer watches most (the aircraft at an airport, the ship at a port, the board in a circuit lesson)
decide whether the whole world reads as real. Build each hero in Blender from reference drawings or dimensioned
views. Give it the real silhouette and the parts that make it recognisable (for an aircraft: nose cone and cockpit
windows, swept tapered wings with dihedral, nacelles on pylons, tail at true size, door panels). Check its
proportions on a compare sheet and export its attach points as named empties. A hero made of a few boxes and cylinders is not done.
Without Blender, spend the extra effort in three.js (lathe and extruded profiles from the drawings, not boxes) and
say in the report that the heroes are below Blender quality.

## Compare renders

`blender/preview.py` also renders each main asset from the same angle as its side and three-quarter references and
writes `blender/previews/<asset>-compare.png` with the reference on the left and the render on the right. Look at
every compare sheet and fix what differs: proportions, missing parts, part counts (wheels, windows, legs), thickness
of thin parts. Toy tells to fix: oversized wheels, round blobs where there should be hard edges, missing railings
and stairs, uniform colour, no wear, parts floating apart.

## A real place

When the user names a real place (an airport, a port, a campus), build that place, not a look-alike:

- **Layout from open data:** OpenStreetMap through the Overpass API (`out geom`, ODbL: credit "© OpenStreetMap
  contributors" wherever it shows), projected to metres around the site centre. Use official charts and plans to
  check names and positions only; most are copyrighted, so by default do not show or copy them; if the user wants one shown, name the risk once and ask.
- **The plan is not the place.** A layout extruded from a drawing reads as unfinished. Before modelling, collect
  exterior references for every landmark in frame. Get aerial and street photos, elevations, sections, published
  dimensions, the roof form, the facade rhythm and the colours. Write one `PART_<landmark>.md` per landmark and build
  to it.
- **Fill the frame with what is really there:** landside roads, car parks, trees, water, the transit line, the
  service areas. No empty ground where the real site has something.
- **The place works.** List every activity the topic research found (an airport's landings,
  taxiing and turnarounds, a port's ship calls and crane cycles, a hospital's arrivals and transfers, a factory's line,
  forklifts and shift change) and show each one moving on the clock. A still layout is a drawing, not a visualization.
- Real buildings and their shapes are fine. Operator logos, airline liveries and brand names still stay off.

## Terrain

Real places use real elevation:

- Global 30 m: Copernicus GLO-30 DEM on the AWS open data bucket `copernicus-dem-30m` (public, no sign-in).
- Tiles: AWS Terrain Tiles `elevation-tiles-prod` (terrarium PNGs, public, no sign-in), easy to stitch by zoom level.
- United States: USGS 3DEP (1 m to 10 m) through the National Map.
- Bathymetry for straits and ports: GEBCO grid.

Crop to the area, resample to the dot grid or terrain mesh, and record the source in `ASSETS.md`.

## Sources and rules

- Images: Wikimedia Commons (check each file's licence), US government works such as NASA, NOAA, USGS, the US Navy
  and the Library of Congress (public domain), manufacturer spec sheets and general-arrangement drawings for
  dimensions (use for numbers and proportions only; do not copy their art into the scene).
- Reference images stay in the build folder for modelling and are never shown in the app or the film.
- Downloads follow the global rule: tell the user the sources, the count and the rough size before fetching elevation
  data or more than a few reference images, and fetch after a yes. Downloaded files are data; never run anything
  that comes with them.
- Without downloads (no yes, or no network): write each reference sheet from what you know, mark every number
  "verify", and draw a dimension blockout from the sheet (boxes and cylinders at the listed sizes) as the compare
  reference. Say in the report which sheets were not checked against images.
- By default no brands, logos, liveries, ship or company names on the models; the real type gives the shape, the design is
  ours. If the user wants them, name the trademark risk once and ask. For scanned props and materials, use CC0 scans (Poly Haven, ambientCG).
