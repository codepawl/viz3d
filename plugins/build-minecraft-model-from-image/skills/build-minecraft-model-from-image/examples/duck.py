"""Rubber duck in a bronze shirt, two dice in one wing, playing cards in the other, three-quarter photo. 30 units tall.
Visible: big glossy head, wide orange-red beak, white eyes with blue iris, bronze shirt with V collar, yellow belly bowl,
yellow wing tips, dice, cards, tail tip at the right.
Inferred: a rubber duck is longer than wide, so the body runs back behind the head; the raised tail sits on the centre line;
the shirt wraps round the back. The printed brand on the belly is left out on purpose."""

SOURCE = {"image": "source.jpg", "mask": "read/mask.png", "yaw": 20, "pitch": 14}

COLLAR = "#f6dfa4"
EYE = {"W": "#ffffff", "B": "#2f83b8", "P": "#14100e"}
INK = "#1a1412"
RED = "#d8362a"


def build(kit):
    materials = {
        "yellow": kit.Material(["#fce85e", "#f6dc40", "#efcd30"], noise=0.15, roughness=0.3),
        "shirt": kit.Material(["#f0cf84", "#e0b25c", "#c9913e", "#a97030"], style="metal", noise=0.25, roughness=0.35, metallic=0.25),
        "beak_top": kit.Material(["#f78a4a", "#ec6c32", "#d85024"], noise=0.15, roughness=0.3),
        "beak_low": kit.Material(["#d84c20", "#b83616", "#8c2410"], noise=0.15, rim=False, roughness=0.3),
        "die": kit.Material(["#fbfbf6", "#f2f2ea"], noise=0.05, rim=False, roughness=0.25),
    }
    model = kit.BlockModel(materials, seed=3)
    center_x = 11.0

    # Body: a bowl narrowing to the floor, then the shirt, stepped in at the shoulders. The belly is longer than wide.
    model.round(center_x, 14, 0, 1, 14, "yellow", corner=3, name="base")
    model.round(center_x, 14, 1, 2, 18, "yellow", corner=4, name="lower belly")
    model.round(center_x, 14, 3, 5, 22, "yellow", corner=4, name="belly")
    shirt_parts = model.round(center_x, 14, 8, 5, 22, "shirt", corner=4, name="shirt")
    shoulder_parts = model.round(center_x, 15, 13, 2, 18, "shirt", corner=3, name="shoulders")
    collar_rows = ["cc..........cc", ".cc........cc.", "..cc......cc..", "...cc....cc...", "....cccccc....", ".....cccc....."]
    shirt_parts[2].paint("front", collar_rows, {"c": COLLAR})
    shoulder_parts[2].paint("front", ["cc........cc", ".cc......cc."], {"c": COLLAR})

    # Head: chamfered tiers, not one cube, with a small tuft.
    model.round(center_x, 17, 15, 1, 12, "yellow", corner=2, name="neck")
    model.round(center_x, 17, 16, 2, 14, "yellow", corner=3, name="head low")
    head_parts = model.round(center_x, 17, 18, 8, 16, "yellow", corner=3, name="head")
    model.round(center_x, 17, 26, 2, 14, "yellow", corner=3, name="head high")
    model.round(center_x, 17, 28, 1, 8, "yellow", corner=2, name="crown")
    model.box((center_x - 1, 29, 16), (2, 1, 3), "yellow", name="tuft")

    # Eyes are painted on the flat front of the head, as on any Minecraft mob.
    eye_rows = [".WW.", "WBBW", "WPBW", ".WW."]
    head_parts[2].paint("front", eye_rows, EYE, at=(0, 1))
    head_parts[2].paint("front", eye_rows, EYE, at=(6, 1))

    # Beak: the upper sticks out further than the lower and has a rounded front.
    model.box((center_x - 6, 20, 25), (12, 2, 5), "beak_top", name="upper beak")
    model.box((center_x - 5, 20, 30), (10, 2, 1), "beak_top", name="upper beak tip")
    model.box((center_x - 5, 18, 25), (10, 2, 4), "beak_low", name="lower beak")

    # Tail: a rising wedge on the centre line at the back.
    model.box((center_x - 4, 6, 1), (8, 5, 3), "yellow", rotation=(-28, 0, 0), name="tail")
    model.box((center_x - 2, 10, -1), (4, 3, 2), "yellow", rotation=(-28, 0, 0), pivot=(center_x, 8, 2), name="tail tip")

    # Sleeves in shirt colour, wing tips in yellow, each wing reaching forward.
    model.box((-2, 9, 15), (3, 5, 9), "shirt", name="left sleeve")
    model.box((-2, 10, 24), (3, 3, 3), "yellow", name="left wing tip")
    model.box((21, 9, 15), (3, 5, 9), "shirt", name="right sleeve")
    model.box((21, 10, 24), (3, 3, 3), "yellow", name="right wing tip")

    # Two dice on the left wing tip: big enough for clean pips.
    pips = {"o": INK}
    first_die = model.box((-5, 13, 23), (4, 4, 4), "die", rotation=(0, -12, 0), name="die")
    first_die.paint("front", ["o...", "....", "....", "...o"], pips)
    first_die.paint("top", ["....", ".oo.", ".oo.", "...."], pips)
    second_die = model.box((-1, 13, 24), (4, 4, 4), "die", rotation=(0, 16, 0), name="die")
    second_die.paint("front", ["o..o", "....", "....", "o..o"], pips)
    second_die.paint("top", ["....", ".o..", "..o.", "...."], pips)

    # Two playing cards in the right wing tip, fanned: a corner letter and one suit mark each, nothing finer.
    king = model.box((20, 13, 25), (5, 7, 1), "die", rotation=(0, 0, 12), pivot=(22, 13, 25), name="card")
    king.paint("front", ["o.o..", "oo...", "o.o..", ".....", "..o..", ".ooo.", "..o.."], {"o": INK})
    ace = model.box((22, 13, 26), (5, 7, 1), "die", rotation=(0, 0, -12), pivot=(23, 13, 26), name="card")
    ace.paint("front", [".#...", "#.#..", "###..", ".....", ".#.#.", ".###.", "..#.."], {"#": RED})
    return model
