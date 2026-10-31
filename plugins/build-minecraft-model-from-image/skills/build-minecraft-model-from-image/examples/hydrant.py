"""French fire hydrant painted pink, nearly front-on, in a garden. 30 units tall, about 15 wide (the photo is about half as wide as tall).
Visible: grey base with a raised front rib, pink column, front port, two side ports aimed out and forward, dark red recess with
a square nut in every port, flat grey cap, operating nut on top.
Inferred: the column is turned, so the back repeats it with the rib; the side ports sit opposite each other; the back has no port.
A dark band under the front port is that port's shadow in the photo, not a part.
A blind reader took the first version for a pig: side ports read as ears and the front port as a snout. What made it a hydrant:
level ports with a flanged collar, a bolted steel flange between base and column, and a real operating nut on top.
Second pass (reel fix): ports pulled in close to a tall 9 wide column (stems 3 long, collar 7 wide), base and cap mid grey like the photo."""

SOURCE = {"image": "source.jpg", "mask": "read/mask.png", "yaw": 0, "pitch": 4}
BOLT = "#5d6265"


def build(kit):
    materials = {
        "pink": kit.Material(["#f9a9b1", "#f29aa3", "#e98791"], noise=0.15, roughness=0.5),
        "recess": kit.Material(["#c02c32", "#a32226", "#861c1e"], noise=0.15, rim=False, roughness=0.55),
        "grey": kit.Material(["#aeb2b4", "#9ea3a5", "#8d9295"], noise=0.15, roughness=0.5, metallic=0.1),
        "cap": kit.Material(["#b9bdbf", "#a0a5a7", "#868b8e"], style="metal", noise=0.2, roughness=0.4, metallic=0.3),
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

    # Pink column, tall and straight.
    model.round(center_x, center_z, 12, 14, 9, "pink", corner=2, name="column")

    # Cap, and the operating nut every hydrant has on top.
    model.round(center_x, center_z, 26, 1, 9, "cap", corner=2, name="cap")
    model.round(center_x, center_z, 27, 1, 7, "cap", corner=2, name="cap top")
    model.box((7, 28, 7), (3, 2, 3), "cap", name="operating nut")

    # Front port: a short stem, then a flanged collar with a real dent and a square nut.
    model.disc(center_x, 16.5, 10, 4, 5, "pink", corner=1, name="front port stem")
    model.disc(center_x, 16.5, 14, 3, 7, "pink", corner=2, recess=2, core="recess", name="front port collar")
    model.box((7.5, 15.5, 15), (2, 2, 1), "cap", name="front nut")

    # Side ports: short barrels close to the column, level with each other, aimed out and forward.
    for side in (-1, 1):
        rotation = (-4, side * 35, 0)
        pivot = (center_x, 21.5, center_z)
        model.disc(center_x, 21.5, center_z + 2, 3, 5, "pink", corner=1, rotation=rotation, pivot=pivot, name="side port stem")
        model.disc(center_x, 21.5, center_z + 5, 3, 7, "pink", corner=2, recess=2, core="recess", rotation=rotation, pivot=pivot,
                   name="side port collar")
        model.box((center_x - 1, 20.5, center_z + 6), (2, 2, 1), "cap", rotation=rotation, pivot=pivot, name="side nut")
    return model
