"""French fire hydrant painted pink, nearly front-on, in a garden. 30 units tall.
Visible: grey base with a raised front rib, pink column, big front port, two side ports aimed out and forward, dark red recess with
a square nut in every port, flat grey cap, operating nut on top.
Inferred: the column is turned, so the back repeats it with the rib; the side ports sit opposite each other; the back has no port.
A dark band under the front port is that port's shadow in the photo, not a part.
A blind reader took the first version for a pig: side ports read as ears and the front port as a snout. What made it a hydrant:
level ports with a flanged collar, a bolted steel flange between base and column, and a real operating nut on top."""

SOURCE = {"image": "source.jpg", "mask": "read/mask.png", "yaw": 0, "pitch": 4}
BOLT = "#6f7477"


def build(kit):
    materials = {
        "pink": kit.Material(["#fbbcc2", "#f6a6ad", "#ee9199"], noise=0.15, roughness=0.5),
        "recess": kit.Material(["#c02c32", "#a32226", "#861c1e"], noise=0.15, rim=False, roughness=0.55),
        "steel": kit.Material(["#ccd2d5", "#bcc4c8", "#adb4b7"], noise=0.15, roughness=0.45, metallic=0.25),
        "cap": kit.Material(["#d8dcde", "#b8bec1", "#94999b"], style="metal", noise=0.2, roughness=0.35, metallic=0.5),
        "rust": kit.Material(["#7a4a3a", "#5e3a30"], noise=0.3, rim=False),
    }
    model = kit.BlockModel(materials, seed=9)
    center_x = 8.5
    center_z = 8.5

    # Base: rust foot, grey standpipe with a rib down the front and the back.
    model.round(center_x, center_z, 0, 1, 13, "rust", corner=3, name="foot")
    model.round(center_x, center_z, 1, 8, 11, "steel", corner=2, name="base")
    model.box((7, 2, 14), (3, 7, 1), "steel", name="front rib")
    model.box((7, 2, 2), (3, 7, 1), "steel", name="back rib")

    # Bolted steel flange between base and column: a wide flat ring with bolt heads painted on its sides.
    flange = model.round(center_x, center_z, 9, 2, 15, "cap", corner=3, name="flange")
    for part in flange[1:5]:
        part.paint("front", ["o.o.o.o.o"[:part.face_size("front")[0]]], {"o": BOLT}, at=(0, 0))
        part.paint("back", ["o.o.o.o.o"[:part.face_size("back")[0]]], {"o": BOLT}, at=(0, 0))
        part.paint("left", ["o.o.o.o.o"[:part.face_size("left")[0]]], {"o": BOLT}, at=(0, 0))
        part.paint("right", ["o.o.o.o.o"[:part.face_size("right")[0]]], {"o": BOLT}, at=(0, 0))

    # Pink column, straight, a little narrower at the top.
    model.round(center_x, center_z, 11, 9, 11, "pink", corner=2, name="column")
    model.round(center_x, center_z, 20, 5, 9, "pink", corner=2, name="column top")

    # Cap, and the operating nut every hydrant has on top.
    model.round(center_x, center_z, 25, 1, 13, "cap", corner=3, name="cap")
    model.round(center_x, center_z, 26, 1, 9, "cap", corner=2, name="cap top")
    model.box((7, 27, 7), (3, 2, 3), "cap", name="operating nut")

    # Front port: a stem, then a wider flanged collar with a real dent and a square nut.
    model.disc(center_x, 16, 11, 7, 9, "pink", corner=2, name="front port stem")
    model.disc(center_x, 16, 18, 3, 11, "pink", corner=3, recess=1, core="recess", name="front port collar")
    model.box((7.5, 15, 20), (2, 2, 1), "cap", name="front nut")

    # Side ports: real barrels, aimed out and forward so their faces show. Long stem, wide collar, deep dent, nut.
    for side in (-1, 1):
        rotation = (-6, side * 42, 0)
        pivot = (center_x, 21.5, center_z)
        model.disc(center_x, 21.5, center_z + 3, 7, 7, "pink", corner=2, rotation=rotation, pivot=pivot, name="side port stem")
        model.disc(center_x, 21.5, center_z + 10, 3, 9, "pink", corner=2, recess=2, core="recess", rotation=rotation, pivot=pivot,
                   name="side port collar")
        model.box((center_x - 1, 20.5, center_z + 11), (2, 2, 1), "cap", rotation=rotation, pivot=pivot, name="side nut")
    return model
