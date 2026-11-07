# Where models come from

Look for a ready model before building one. Check the sources in this order, and record each import in the
project's `CREDITS.md` with the source, author, licence and link. Name the source and rough size and get the
user's OK before downloading. When the user is away or has approved downloads, take CC0 and CC BY files only and
list each one in the report.

1. **Ready models of the exact thing**, with animation clips when it moves. Search Sketchfab filtered to
   downloadable CC0 or CC BY. Use fan models of known characters or real brands only when the user asks for them,
   and put a credit line in the report. A site that needs a sign-in gets one from the user. Downloads go to their
   own folder and are never executed.
2. **Scans and real materials**: Poly Haven and ambientCG (CC0), NVIDIA SimReady props (CC BY 4.0), NASA 3D
   Resources, Smithsonian Open Access (CC0 items).
3. **Stylized and low-poly packs**: Kenney and Quaternius (CC0), Poly Pizza (CC0 or CC BY per model). Kenney's
   site refuses scripted downloads (HTTP 403). If the user cannot fetch a pack by hand, use Quaternius, Poly Pizza
   or the Poly Haven API. Poly Haven has no stylized trees, and some scans run to hundreds of megabytes. Keep each
   model in a web build under about 20 MB.
4. **AI-generated models**: the Scenario 3D Collection, a public dataset of about 1,300 GLB models (CC BY 4.0,
   credit "Scenario"). It holds props, characters, creatures, mechs, vehicles and buildings made by image-to-3D and
   text-to-3D generators. Search it by hand and pick by eye from previews. Meshes are static with no skeleton. Use
   them for props and set dressing, or as a base to restyle.
5. **Build it** in Blender (or three.js, see `no-blender.md`) from a reference sheet (`real-objects.md`).

Ground cover counts as an asset too. Search for it like a prop: a ground texture (ambientCG `Grass005` is a bright
lawn, `api/v2/full_json?type=Material&q=grass` lists more) and tuft models on Poly Pizza (search "grass"; each
model page links its `.glb` on static.poly.pizza and states its licence). Tufts alone leave bare ground between
them; lay them on the texture. Brighten dark tuft textures with the material colour, and render two or three
ground options for the user to pick.

Pick the right kind of thing, not the nearest model: a narrowboat for a canal, not a sailing ship. A container
crane belongs in a port, not a construction crane. A wrong kind fails review however good it looks.

Set material, light and camera values from measured data instead of by eye: physicallybased.info (CC0) lists colour, IOR and F0 per material, colour temperature and intensity per light, and sensor sizes per camera, with JSON on GitHub.

Every main asset still gets the reference-sheet check from `real-objects.md`, whichever source it came from.
Restyle imports to the film's look and scale. Skip anything marked non-commercial (NC) or no-derivatives (ND).
Check each model's licence on its own page, not the collection's.
