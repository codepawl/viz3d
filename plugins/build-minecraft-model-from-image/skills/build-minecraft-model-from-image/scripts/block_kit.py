"""Minecraft-style box models: a few cuboids, each face a pixel texture at one texel per unit.

Axes: x = width (+x is the viewer's right when facing the front), y = up, z = depth (+z is the front).
Sizes are whole units, so every pixel on the model is the same size. A box may be rotated for angled parts.
Faces are named front (+z), back (-z), right (+x), left (-x), top, bottom. A face's rows read as seen from outside it;
the top face is seen from above with the front edge at the bottom of the rows.
"""

from dataclasses import dataclass, field
from math import atan2, ceil, cos, degrees, hypot, radians, sin

import numpy


@dataclass
class Material:
    ramp: list  # hex colours, lightest first; 3 to 6 steps taken from the picture
    style: str = "plain"  # plain, wood, metal or fabric
    noise: float = 0.5  # how far a texel wanders from the base step, in ramp steps
    rim: bool = True  # lighter top row and darker bottom row on side faces, so each part reads as a part
    roughness: float = 0.85
    metallic: float = 0.0


def hex_to_rgb(colour):
    colour = colour.lstrip("#")
    return tuple(int(colour[index:index + 2], 16) for index in (0, 2, 4))


def _paint_steps(material, width, height, face, generator):
    """A height x width array of ramp positions for one face, before rims."""
    steps = len(material.ramp)
    base = (steps - 1) / 2
    positions = numpy.full((height, width), base, dtype=float)
    if material.style == "wood":
        across = width >= height
        lines = generator.normal(0.0, material.noise, height if across else width)
        grain = generator.normal(0.0, material.noise * 0.45, (height, width))
        positions += (lines[:, None] if across else lines[None, :]) + grain
    elif material.style == "metal":
        ramp_down = numpy.linspace(-0.8, 0.8, height)[:, None]
        positions += ramp_down + generator.normal(0.0, material.noise * 0.5, (height, width))
    elif material.style == "fabric":
        positions += generator.choice([-1.0, 0.0, 0.0, 1.0], (height, width)) * material.noise * 2
    else:
        positions += generator.normal(0.0, material.noise, (height, width))
    if face == "top":
        positions -= 0.8
    elif face == "bottom":
        positions += 1.2
    return positions


def _apply_rim(positions, face):
    height, width = positions.shape
    if min(height, width) < 2:
        return
    if face in ("front", "back", "left", "right"):
        positions[0, :] -= 0.9
        if height >= 3:
            positions[-1, :] += 0.9
    elif face == "top" and min(height, width) >= 3:
        positions[0, :] -= 0.5
        positions[-1, :] -= 0.5
        positions[:, 0] -= 0.5
        positions[:, -1] -= 0.5


class Box:
    def __init__(self, model, low, size, materials_by_face, rotation, pivot, name):
        self.low = tuple(float(value) for value in low)
        self.size = tuple(int(value) for value in size)
        self.rotation = rotation
        self.pivot = pivot
        self.name = name
        self.materials_by_face = materials_by_face
        self.generator = model.generator
        self.textures = {}
        for face in FACES:
            material = materials_by_face[face]
            width, height = self.face_size(face)
            positions = _paint_steps(material, width, height, face, model.generator)
            if material.rim:
                _apply_rim(positions, face)
            indices = numpy.clip(numpy.rint(positions), 0, len(material.ramp) - 1).astype(int)
            palette = numpy.array([hex_to_rgb(colour) for colour in material.ramp], dtype=numpy.uint8)
            self.textures[face] = palette[indices]

    def face_size(self, face):
        size_x, size_y, size_z = self.size
        if face in ("front", "back"):
            return size_x, size_y
        if face in ("left", "right"):
            return size_z, size_y
        return size_x, size_z

    def paint(self, face, rows, legend, at=(0, 0)):
        """Pixel art on a face. at = (column, row) of the top-left character, as seen from outside.
        legend maps a character to a hex colour; any other character leaves the texel alone."""
        texture = self.textures[face]
        for row_offset, row in enumerate(rows):
            for column_offset, character in enumerate(row):
                colour = legend.get(character)
                if colour is None:
                    continue
                target_row = at[1] + row_offset
                target_column = at[0] + column_offset
                if 0 <= target_row < texture.shape[0] and 0 <= target_column < texture.shape[1]:
                    texture[target_row, target_column] = hex_to_rgb(colour)
        return self

    def band(self, row, colour):
        """One texel line round the four sides, counted from the top: seams, stripes, belts."""
        for face in ("front", "back", "left", "right"):
            texture = self.textures[face]
            if 0 <= row < texture.shape[0]:
                texture[row, :] = hex_to_rgb(colour)
        return self

    def speckle(self, colours, share, faces=None):
        """Scatter texels of these hex colours over faces: rust, wear, printed fabric."""
        palette = [hex_to_rgb(colour) for colour in colours]
        for face in faces or FACES:
            texture = self.textures[face]
            chosen = self.generator.uniform(0.0, 1.0, texture.shape[:2]) < share
            for row, column in zip(*numpy.nonzero(chosen)):
                texture[row, column] = palette[self.generator.integers(len(palette))]
        return self

    def corners(self):
        """The eight world corners, x-low first."""
        x0, y0, z0 = self.low
        x1, y1, z1 = x0 + self.size[0], y0 + self.size[1], z0 + self.size[2]
        points = numpy.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)], dtype=float)
        return self.transform(points)

    def rotation_matrix(self):
        if self.rotation is None:
            return numpy.eye(3)
        angle_x, angle_y, angle_z = (radians(value) for value in self.rotation)
        rotate_x = numpy.array([[1, 0, 0], [0, cos(angle_x), -sin(angle_x)], [0, sin(angle_x), cos(angle_x)]])
        rotate_y = numpy.array([[cos(angle_y), 0, sin(angle_y)], [0, 1, 0], [-sin(angle_y), 0, cos(angle_y)]])
        rotate_z = numpy.array([[cos(angle_z), -sin(angle_z), 0], [sin(angle_z), cos(angle_z), 0], [0, 0, 1]])
        return rotate_y @ rotate_x @ rotate_z

    def transform(self, points):
        if self.rotation is None:
            return points
        pivot = numpy.asarray(self.pivot, dtype=float)
        return (points - pivot) @ self.rotation_matrix().T + pivot


FACES = ("front", "back", "right", "left", "top", "bottom")


def _filler_size(corner):
    return (corner + 1) // 2


def _notch_fillers(first_low, second_low, diameter, corner):
    """Low corners of the boxes that fill the four notches of a core-and-slabs round, so it reads as an octagon."""
    if corner < 3:
        return []
    size = _filler_size(corner)
    near = corner - size
    far = diameter - corner
    return [(first_low + first, second_low + second) for first in (near, far) for second in (near, far)]


@dataclass
class BlockModel:
    materials: dict
    seed: int = 7
    boxes: list = field(default_factory=list)

    def __post_init__(self):
        self.generator = numpy.random.default_rng(self.seed)

    def box(self, low, size, material, top=None, bottom=None, sides=None, rotation=None, pivot=None, name=""):
        """low is the box's low corner, size is (width, height, depth) in whole units. top, bottom and sides override the
        material on those faces. rotation is degrees (x, y, z) around pivot, which defaults to the box's centre."""
        if pivot is None:
            pivot = tuple(low[index] + size[index] / 2 for index in range(3))
        side_material = self.materials[sides or material]
        materials_by_face = {face: side_material for face in ("front", "back", "left", "right")}
        materials_by_face["top"] = self.materials[top or material]
        materials_by_face["bottom"] = self.materials[bottom or material]
        created = Box(self, low, size, materials_by_face, rotation, pivot, name)
        self.boxes.append(created)
        return created

    def round(self, center_x, center_z, low_y, height, diameter, material, corner=None, top=None, bottom=None, name=""):
        """A round part the Minecraft way: a square core, four side slabs and, for corners of 3 or more, a filler in each
        notch. Returns the boxes: core, back slab, front slab, left slab, right slab, then any fillers.
        Odd and even diameters both stay centred when center_x fits them."""
        corner = corner if corner is not None else max(diameter // 5, 1)
        core = diameter - 2 * corner
        left = center_x - diameter / 2
        back = center_z - diameter / 2
        parts = [
            self.box((left + corner, low_y, back + corner), (core, height, core), material, top=top, bottom=bottom, name=name),
            self.box((left + corner, low_y, back), (core, height, corner), material, top=top, bottom=bottom, name=name),
            self.box((left + corner, low_y, back + diameter - corner), (core, height, corner), material, top=top, bottom=bottom, name=name),
            self.box((left, low_y, back + corner), (corner, height, core), material, top=top, bottom=bottom, name=name),
            self.box((left + diameter - corner, low_y, back + corner), (corner, height, core), material, top=top, bottom=bottom, name=name),
        ]
        for first, second in _notch_fillers(left, back, diameter, corner):
            parts.append(self.box((first, low_y, second), (_filler_size(corner), height, _filler_size(corner)), material, top=top,
                                  bottom=bottom, name=name))
        return parts

    def disc(self, center_x, center_y, low_z, depth, diameter, material, corner=None, recess=0, core=None, rotation=None,
             pivot=None, name=""):
        """A round part facing +z: ports, lenses, wheels, spout mouths. Rotate it to aim it anywhere. recess sets the
        square core back from the rim by that many units, with its own material, for a real dent. Returns (core, rim parts)."""
        corner = corner if corner is not None else max(diameter // 5, 1)
        core_size = diameter - 2 * corner
        left = center_x - diameter / 2
        bottom = center_y - diameter / 2
        if pivot is None:
            pivot = (center_x, center_y, low_z)
        shared = {"rotation": rotation, "pivot": pivot, "name": name}
        core_box = self.box((left + corner, bottom + corner, low_z), (core_size, core_size, depth - recess), core or material, **shared)
        rim = [
            self.box((left + corner, bottom, low_z), (core_size, corner, depth), material, **shared),
            self.box((left + corner, bottom + diameter - corner, low_z), (core_size, corner, depth), material, **shared),
            self.box((left, bottom + corner, low_z), (corner, core_size, depth), material, **shared),
            self.box((left + diameter - corner, bottom + corner, low_z), (corner, core_size, depth), material, **shared),
        ]
        for first, second in _notch_fillers(left, bottom, diameter, corner):
            rim.append(self.box((first, second, low_z), (_filler_size(corner), _filler_size(corner), depth), material, **shared))
        return core_box, rim

    def beam(self, start, end, thickness, material, name=""):
        """A straight bar between two points at any angle, for handles and braces. thickness = (across, deep);
        the bar runs in the plane of its rotation around z, then around y."""
        start = numpy.asarray(start, dtype=float)
        end = numpy.asarray(end, dtype=float)
        delta = end - start
        horizontal = hypot(delta[0], delta[2])
        length = max(int(ceil(numpy.linalg.norm(delta))), 1)
        center = (start + end) / 2
        angle_z = degrees(atan2(delta[1], horizontal))
        angle_y = degrees(atan2(-delta[2], delta[0]))
        low = (center[0] - length / 2, center[1] - thickness[0] / 2, center[2] - thickness[1] / 2)
        return self.box(low, (length, thickness[0], thickness[1]), material, rotation=(0, angle_y, angle_z),
                        pivot=tuple(center), name=name)
