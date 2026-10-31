"""Arts and Crafts armchair, three-quarter photo. 40 units tall so 2 x 2 legs stay as slender as the photo's.
The four foot positions on the blueprint solve to yaw 57, pitch 25 and width about equal to depth.
Visible: near side, front, thin arm boards, gold printed cushion, four slats, top rail, stretchers.
Inferred: the far side mirrors the near side; the rear stretcher and the back of the slats match what shows through the frame."""

SOURCE = {"image": "source.jpg", "mask": "read/mask.png", "yaw": 57, "pitch": 25}
PRINT_TILE = ["..o...", ".o.o..", "..o..o", "o....o", ".oo...", "...oo."]


def tiled(rows, columns, shift=0):
    return ["".join(PRINT_TILE[(row + shift) % 6][(column + shift) % 6] for column in range(columns)) for row in range(rows)]


def build(kit):
    materials = {
        "wood": kit.Material(["#7d4c3a", "#673c2f", "#532f28", "#432523"], style="wood", noise=0.4, roughness=0.5),
        "arm": kit.Material(["#8e5a3c", "#774630", "#623828"], style="wood", noise=0.4, roughness=0.45),
        "cushion": kit.Material(["#e2cc92", "#cfb274", "#b4955a"], style="fabric", noise=0.25, roughness=0.95),
    }
    model = kit.BlockModel(materials, seed=5)
    width = 15
    depth = 15
    left = 0
    right = width - 2
    back = 0
    front = depth - 2
    inner_width = right - left - 2
    inner_depth = front - back - 2

    # Legs. The back legs run up as the posts; the front legs run up to carry the arms.
    for x in (left, right):
        model.box((x, 0, back), (2, 40, 2), "wood", name="back post")
        model.box((x, 0, front), (2, 28, 2), "wood", name="front leg")

    # Seat rails sit between the legs, set in by half a leg, so they read as separate boards.
    model.box((left + 2, 16, front), (inner_width, 3, 1), "wood", name="front rail")
    model.box((left + 2, 16, back + 1), (inner_width, 3, 1), "wood", name="rear rail")
    model.box((left, 16, back + 2), (1, 3, inner_depth), "wood", name="left rail")
    model.box((right + 1, 16, back + 2), (1, 3, inner_depth), "wood", name="right rail")
    model.box((left + 1, 18, back + 2), (inner_width + 2, 1, inner_depth), "wood", name="seat board")

    # Cushion: sits between the posts and the front legs, its front spilling over the rail, domed on top.
    cushion = model.box((2, 19, 2), (inner_width, 2, inner_depth + 2), "cushion", name="cushion")
    pillow = model.box((3, 21, 3), (inner_width - 2, 1, inner_depth), "cushion", name="cushion dome")
    print_legend = {"o": "#7a5a30"}
    cushion.paint("front", tiled(2, inner_width), print_legend)
    cushion.paint("top", tiled(inner_depth + 2, inner_width), print_legend)
    pillow.paint("top", tiled(inner_depth, inner_width - 2, 3), print_legend)
    pillow.paint("front", tiled(1, inner_width - 2, 2), print_legend)
    pillow.paint("right", tiled(1, inner_depth, 1), print_legend)
    pillow.paint("left", tiled(1, inner_depth, 4), print_legend)

    # Stretchers cross the legs at different heights, as in the photo.
    model.box((left, 9, back + 2), (1, 1, inner_depth), "wood", name="left stretcher")
    model.box((right + 1, 9, back + 2), (1, 1, inner_depth), "wood", name="right stretcher")
    model.box((left + 2, 6, front + 1), (inner_width, 1, 1), "wood", name="front stretcher")
    model.box((left + 2, 12, back), (inner_width, 1, 1), "wood", name="rear stretcher")

    # Back: lower rail, top rail with a raised middle, four thin slats sitting close.
    model.box((left + 2, 24, back), (inner_width, 1, 1), "wood", name="lower back rail")
    model.box((left + 2, 35, back), (inner_width, 2, 1), "wood", name="top rail")
    model.box((left + 5, 37, back), (inner_width - 6, 1, 1), "wood", name="top rail crown")
    for slat_x in (4, 6, 8, 10):
        model.box((left + slat_x, 25, back), (1, 10, 1), "wood", name="slat")

    # Arms: thin boards butting into the post and running past the front leg, a touch wider than the leg.
    model.box((left - 1, 28, back + 2), (4, 1, depth), "arm", name="left arm")
    model.box((right - 1, 28, back + 2), (4, 1, depth), "arm", name="right arm")
    return model
