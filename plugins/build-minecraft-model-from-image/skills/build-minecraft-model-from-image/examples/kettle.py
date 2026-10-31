"""Japanese cast-iron kettle (tetsubin), side-on photo. 28 units tall.
Visible: pillow-shaped body with a flat shoulder, raised lid, bud knob, short beak spout on the left, bail handle, casting seam, rust.
Inferred: the body is turned, so the far side repeats the near side; the bail is one piece in the picture plane;
nothing else sits on the back."""

SOURCE = {"image": "source.jpg", "mask": "read/mask.png", "yaw": 0, "pitch": 0}
SEAM = "#2a2228"
RUST = ["#6e5245", "#5e4640", "#74563f"]


def build(kit):
    materials = {
        "iron": kit.Material(["#5e504c", "#4f4345", "#41373b", "#352c31", "#2a2329"], noise=0.55, roughness=0.8, metallic=0.1),
        "lid": kit.Material(["#6a5a55", "#584b4c", "#483d40", "#3a3035"], noise=0.5, roughness=0.8, metallic=0.1),
        "wire": kit.Material(["#57483f", "#40343a", "#2f2830"], noise=0.3, rim=False, roughness=0.6, metallic=0.3),
        "bronze": kit.Material(["#a08e68", "#84724f", "#665640", "#4e4034"], style="metal", noise=0.3, rim=False, roughness=0.4, metallic=0.5),
        "lip": kit.Material(["#a4482c", "#7c3220"], noise=0.3, rim=False),
    }
    model = kit.BlockModel(materials, seed=11)
    center_x = 13.5
    center_z = 13.5

    # Body tiers follow the photo's rounded profile: small foot, wide belly, shoulder stepping in to the lid.
    model.round(center_x, center_z, 0, 1, 15, "iron", corner=3, name="foot")
    model.round(center_x, center_z, 1, 1, 19, "iron", corner=4, name="lower belly")
    belly = model.round(center_x, center_z, 2, 8, 21, "iron", corner=4, name="belly")
    for part in belly:
        part.band(5, SEAM)
        part.speckle(RUST, 0.08, faces=("front", "back", "left", "right"))
    model.round(center_x, center_z, 10, 1, 19, "lid", corner=4, name="upper belly")
    shoulder = model.round(center_x, center_z, 11, 1, 17, "lid", corner=3, name="shoulder")
    for part in shoulder:
        part.speckle(RUST, 0.1, faces=("top",))

    model.round(center_x, center_z, 12, 1, 11, "lid", corner=2, name="lid")
    model.box((13, 13, 13), (1, 1, 1), "bronze", name="knob neck")
    model.box((12, 14, 12), (3, 3, 3), "bronze", name="knob bud")
    model.box((13, 17, 13), (1, 1, 1), "bronze", name="knob tip")

    # Spout: a stubby beak leaving the upper belly, tipped up, with the red inside showing at the mouth.
    model.beam((5.0, 6.8, 13.5), (0.8, 10.2, 13.5), (4, 3), "iron", name="spout")
    mouth = model.box((-2, 10, 12), (4, 2, 3), "iron", name="spout mouth")
    mouth.paint("top", ["....", "##..", "...."], {"#": "#6a2a1c"})

    # Lugs on the shoulder and the bail: straight posts, then two angled pieces each side, then the top bar.
    model.box((4, 12, 12), (2, 3, 3), "iron", name="lug left")
    model.box((21, 12, 12), (2, 3, 3), "iron", name="lug right")
    z = 13.5
    bail_points = [(5, 14), (5, 22), (6.5, 25.5), (10, 27.5), (17, 27.5), (20.5, 25.5), (22, 22), (22, 14)]
    for start, end in zip(bail_points[:-1], bail_points[1:]):
        model.beam((start[0], start[1], z), (end[0], end[1], z), (1, 2), "wire", name="bail")
    return model
