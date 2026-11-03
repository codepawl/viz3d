"""French fire hydrant painted pink, nearly front-on, in a garden. 34 units tall, about 16 wide at the ports (the photo is about
half as wide as tall).
Visible: grey base with a raised front rib, pink column, a front port, two side ports aimed out and forward, a flat grey cap
with an operating nut on top, a steel square nut in the middle of every port cap.
Inferred: the column is turned, so the back repeats it with the rib; the side ports sit opposite each other; the back has no port.
A dark band under the front port is that port's shadow in the photo, not a part.
A blind reader took the first version for a pig: side ports read as ears and the front port as a snout. What made it a hydrant:
level ports with a flanged collar, a bolted steel flange between base and column, and a real operating nut on top.
Reel fix (third pass): the column is taller so pink shows between the flange and the ports; every port is a round nozzle:
a short stem, a grey flange ring, then a pink cap with a shallow, pink-red recess (not dark red) that a bright steel nut fills;
the side ports are level (no pitch), set well out from the column on a visible stem, so they read as nozzles, not ears."""

SOURCE = {"image": "source.jpg", "mask": "read/mask.png", "yaw": 0, "pitch": 4}
BOLT = "#5d6265"
PORT_YAW = 40


def build(kit):
    materials = {
        "pink": kit.Material(["#f08a92", "#e97d86", "#dc6d77"], noise=0.15, roughness=0.5),
        "recess": kit.Material(["#d4606c", "#c85763", "#b94c58"], noise=0.15, rim=False, roughness=0.55),
        "grey": kit.Material(["#aeb2b4", "#9ea3a5", "#8d9295"], noise=0.15, roughness=0.5, metallic=0.1),
        "cap": kit.Material(["#b9bdbf", "#a0a5a7", "#868b8e"], style="metal", noise=0.2, roughness=0.4, metallic=0.3),
        "steel": kit.Material(["#e6e9ea", "#cfd3d5", "#b4b9bb"], style="metal", noise=0.12, roughness=0.3, metallic=0.5),
        "rust": kit.Material(["#7a4a3a", "#5e3a30"], noise=0.3, rim=False),
    }
    model = kit.BlockModel(materials, seed=9)
    center_x = 8.5
    center_z = 8.5

    # Base: rust foot, tall grey standpipe with a rib down the front and the back.
    model.round(center_x, center_z, 0, 1, 11, "rust", corner=3, name="foot")
    model.round(center_x, center_z, 1, 10, 9, "grey", corner=2, name="base")
    model.box((7, 2, 13), (3, 7, 1), "grey", name="front rib")
    model.box((7, 2, 3), (3, 7, 1), "grey", name="back rib")

    # Bolted flange between base and column: a flat ring with bolt heads painted on its sides.
    flange = model.round(center_x, center_z, 11, 1, 11, "cap", corner=3, name="flange")
    for part in flange[1:5]:
        for face in ("front", "back", "left", "right"):
            part.paint(face, ["o.o.o.o.o"[:part.face_size(face)[0]]], {"o": BOLT}, at=(0, 0))

    # Pink column, tall and straight: 17 units, so it shows between the flange and the ports.
    model.round(center_x, center_z, 12, 17, 9, "pink", corner=2, name="column")

    # Cap, and the operating nut every hydrant has on top.
    model.round(center_x, center_z, 29, 1, 9, "cap", corner=2, name="cap")
    model.round(center_x, center_z, 30, 1, 7, "cap", corner=2, name="cap top")
    model.box((7, 31, 7), (3, 3, 3), "steel", name="operating nut")

    # Front port: stem, grey flange ring, pink round cap with a shallow recess and a steel nut that fills it.
    port_y = 19.5
    model.disc(center_x, port_y, 10, 4, 7, "pink", corner=2, name="front port stem")
    model.disc(center_x, port_y, 14, 1, 9, "grey", corner=2, name="front port ring")
    model.disc(center_x, port_y, 15, 2, 7, "pink", corner=2, recess=1, core="recess", name="front port cap")
    model.box((7, port_y - 1.5, 16), (3, 3, 1), "steel", name="front nut")

    # Side ports: level (no pitch), aimed out and forward, on a visible stem well out from the column.
    side_y = 25.5
    for side in (-1, 1):
        rotation = (0, side * PORT_YAW, 0)
        pivot = (center_x, side_y, center_z)
        model.disc(center_x, side_y, center_z + 2, 4, 5, "pink", corner=1, rotation=rotation, pivot=pivot, name="side port stem")
        model.disc(center_x, side_y, center_z + 6, 1, 9, "grey", corner=2, rotation=rotation, pivot=pivot, name="side port ring")
        model.disc(center_x, side_y, center_z + 7, 2, 7, "pink", corner=2, recess=1, core="recess", rotation=rotation, pivot=pivot,
                   name="side port cap")
        model.box((center_x - 1.5, side_y - 1.5, center_z + 8), (3, 3, 1), "steel", rotation=rotation, pivot=pivot, name="side nut")
    return model
