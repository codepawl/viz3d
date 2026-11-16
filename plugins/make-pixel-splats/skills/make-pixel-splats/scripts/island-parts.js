// Shapes of the "Pocket Seasons" island: terraces, an organic pond, stepping stones, a picket fence with a gate, the
// log cabin and the small things on the ground. Every shape is a plain distance function; seasons.js snaps them to
// voxel blocks so the cabin, the tree and the ground all read as the same kind of block art.
// Blocks are VOXEL wide and their centres sit on odd hundredths (0.01, 0.03 ...). A part one block thin must be
// centred on such a value, or it falls between two blocks and vanishes.
import { hashNoise, valueNoise, boxDistance, sphereDistance, ellipsoidDistance, capsuleDistance, smoothUnion } from './voxel-splats.js';

export const VOXEL = 0.02;
export const TOP = { halfX: 0.78, halfZ: 0.62 };
export const cellOf = value => Math.floor(value / VOXEL);

// ---- Pond: three blended circles, so the outline is a soft bean, not a rectangle ----

export function pondOutline(x, z) {
  const first = Math.hypot(x - 0.42, z - 0.3) - 0.15;
  const second = Math.hypot(x - 0.55, z - 0.2) - 0.1;
  const third = Math.hypot(x - 0.3, z - 0.37) - 0.09;
  return smoothUnion(smoothUnion(first, second, 0.07), third, 0.07) + (valueNoise(x * 9, 3.1, z * 9) - 0.5) * 0.03;
}

// One block layer of water a block below the grass.
export function waterDistance(x, y, z) {
  return Math.max(pondOutline(x, z), Math.abs(y + 0.03) - 0.01);
}

// ---- Island: three terraces; the pond is carved out of the top ----

export function islandDistance(x, y, z, season) {
  const top = boxDistance(x, y, z, 0, -0.06, 0, TOP.halfX, 0.06, TOP.halfZ);
  const middle = boxDistance(x, y, z, -0.04, -0.2, 0.03, 0.66, 0.1, 0.54);
  const bottom = boxDistance(x, y, z, 0.02, -0.4, -0.02, 0.48, 0.12, 0.4);
  const root = boxDistance(x, y, z, 0.0, -0.58, 0.0, 0.24, 0.1, 0.22);
  const lumps = y < -0.13 ? (valueNoise(x * 7, y * 7, z * 7) - 0.5) * 0.07 : 0;
  let island = Math.min(top, middle, bottom, root) + lumps;
  const carve = Math.max(pondOutline(x, z), -(y + 0.05));
  island = Math.max(island, -carve);
  if (season.icicles) island = Math.min(island, iciclesDistance(x, y, z));
  return island;
}

// Icicles hang from the top terrace's overhanging front and right edges in winter.
function iciclesDistance(x, y, z) {
  if (y > -0.11 || y < -0.24) return Infinity;
  let distance = Infinity;
  for (let index = 0; index < 22; index++) {
    const alongFront = index < 13;
    const position = alongFront ? -0.69 + index * 0.12 : -0.49 + (index - 13) * 0.12;
    const length = 0.03 + hashNoise(index, 7.7, 1.3) * 0.07;
    const icicleX = alongFront ? position : TOP.halfX - 0.01;
    const icicleZ = alongFront ? TOP.halfZ - 0.01 : position;
    distance = Math.min(distance, boxDistance(x, y, z, icicleX, -0.12 - length / 2, icicleZ, 0.009, length / 2, 0.009));
  }
  return distance;
}

// ---- Cabin: 16 blocks wide, 14 deep, 13 tall to the eaves ----

export const CABIN = { x: -0.34, z: -0.2 };
export const CHIMNEY = { x: -0.44, top: 0.5, z: -0.28 };

export function cabinDistance(x, y, z, seasonName = "summer") {
  const walls = boxDistance(x, y, z, CABIN.x, 0.13, CABIN.z, 0.16, 0.13, 0.14);
  const roofSlab = boxDistance(x, y, z, CABIN.x, 0.34, CABIN.z, 0.2, 0.1, 0.18);
  const gable = Math.abs(z - CABIN.z) * 1.05 + (y - 0.26) - 0.17;
  const roof = Math.max(roofSlab, gable, -(y - 0.25));
  const chimney = boxDistance(x, y, z, CHIMNEY.x, 0.42, CHIMNEY.z, 0.02, 0.08, 0.02);
  const doorStep = boxDistance(x, y, z, -0.27, 0.01, -0.05, 0.04, 0.01, 0.01);
  // A window box under the front window; in spring and summer a row of flowers grows out of it.
  const windowBox = boxDistance(x, y, z, -0.43, 0.09, -0.05, 0.05, 0.01, 0.01);
  const blooming = seasonName === "spring" || seasonName === "summer";
  const flowers = blooming ? boxDistance(x, y, z, -0.43, 0.11, -0.05, 0.05, 0.01, 0.01) : Infinity;
  return Math.min(walls, roof, chimney, doorStep, windowBox, flowers);
}

// ---- Path, fence, rocks ----

// Stones from the door toward the pond, two blocks of bare ground between each, the last one stopping short of the water.
export const STONES = [[-0.26, 0.04], [-0.14, 0.1], [-0.02, 0.15], [0.1, 0.2]];
const FENCE_INSET = 0.03;
const GATE = { from: -0.03, to: 0.15 };

export function pathDistance(x, y, z) {
  let distance = Infinity;
  for (const [stoneX, stoneZ] of STONES) distance = Math.min(distance, boxDistance(x, y, z, stoneX, 0.006, stoneZ, 0.04, 0.008, 0.03));
  return distance;
}

export function onStone(x, z) {
  return STONES.some(([stoneX, stoneZ]) => Math.abs(x - stoneX) <= 0.04 && Math.abs(z - stoneZ) <= 0.03);
}

// A picket fence round the whole yard: pickets on every other block with every fourth one taller, two rails behind
// them, taller posts at the corners and either side of a gate gap on the front.
export function fenceDistance(x, y, z) {
  if (y < 0 || y > 0.13) return Infinity;
  const frontZ = TOP.halfZ - FENCE_INSET;
  const backZ = -TOP.halfZ + FENCE_INSET;
  const leftX = -TOP.halfX + FENCE_INSET;
  const rightX = TOP.halfX - FENCE_INSET;
  let distance = Infinity;
  const sides = [
    { fixed: 'z', at: frontZ, from: leftX, to: rightX, rail: -1 },
    { fixed: 'z', at: backZ, from: leftX, to: rightX, rail: 1 },
    { fixed: 'x', at: leftX, from: backZ, to: frontZ, rail: 1 },
    { fixed: 'x', at: rightX, from: backZ, to: frontZ, rail: -1 },
  ];
  for (const side of sides) {
    const along = side.fixed === 'z' ? x : z;
    const across = side.fixed === 'z' ? z : x;
    if (along < side.from - 0.005 || along > side.to + 0.005) continue;
    if (Math.abs(across - side.at) > 0.05) continue;
    if (side.fixed === 'z' && side.at > 0 && along > GATE.from + 0.005 && along < GATE.to - 0.005) continue;
    const cell = Math.round((along - side.from) / VOXEL);
    const tall = side.at > 0 ? 0.06 : 0.08;
    const height = cell % 4 === 0 ? tall + VOXEL : tall;
    if (cell % 2 === 0) distance = Math.min(distance, Math.max(Math.abs(across - side.at) - 0.008, Math.abs(y - height / 2) - height / 2));
    const railAcross = side.at + side.rail * VOXEL;
    for (const railY of side.at > 0 ? [0.01, 0.05] : [0.03, 0.07]) distance = Math.min(distance, Math.max(Math.abs(across - railAcross) - 0.008, Math.abs(y - railY) - 0.008));
  }
  for (const [postX, postZ] of [[leftX, frontZ], [rightX, frontZ], [leftX, backZ], [rightX, backZ], [GATE.from, frontZ], [GATE.to, frontZ]]) {
    distance = Math.min(distance, boxDistance(x, y, z, postX, 0.05, postZ, 0.009, 0.05, 0.009));
  }
  return distance;
}

export function nearFence(x, z, reach = 0.04) {
  const frontBack = Math.abs(Math.abs(z) - (TOP.halfZ - FENCE_INSET)) < reach && Math.abs(x) < TOP.halfX;
  const sides = Math.abs(Math.abs(x) - (TOP.halfX - FENCE_INSET)) < reach && Math.abs(z) < TOP.halfZ;
  return frontBack || sides;
}

export const ROCKS = [[0.63, -0.43, 0.05], [-0.63, 0.37, 0.045], [0.21, 0.45, 0.035]];

export function onRim(x, z) {
  const rim = pondOutline(x, z);
  return rim > 0 && rim < 0.025 && hashNoise(cellOf(x), 2.2, cellOf(z)) > 0.6;
}

export function rocksDistance(x, y, z) {
  if (y < -0.02 || y > 0.08) return Infinity;
  let distance = Infinity;
  for (const [rockX, rockZ, radius] of ROCKS) distance = Math.min(distance, ellipsoidDistance(x, y, z, rockX, 0.0, rockZ, radius, radius * 0.8, radius * 0.9));
  // Small stones dotted round the pond's rim, one block each.
  if (y > 0 && y < 0.02 && onRim(x, z)) distance = Math.min(distance, -0.001);
  return distance;
}

// ---- Things that grow or lie on the ground, chosen per block column so they stay one block wide ----

export const TREE = { x: 0.25, z: -0.19 };

function keepClear(x, z) {
  const nearCabin = Math.abs(x - CABIN.x) < 0.2 && Math.abs(z - CABIN.z) < 0.18;
  const nearTree = Math.hypot(x - TREE.x, z - TREE.z) < 0.07;
  const nearPath = STONES.some(([stoneX, stoneZ]) => Math.abs(x - stoneX) < 0.06 && Math.abs(z - stoneZ) < 0.05);
  return nearCabin || nearTree || nearPath || pondOutline(x, z) < 0.03 || nearFence(x, z, 0.05) || Math.abs(x) > 0.7 || Math.abs(z) > 0.54;
}

// What grows in a block column: height in blocks and kind, or null for bare ground.
export function groundDetailAt(x, z, seasonName) {
  if (keepClear(x, z)) return null;
  const cellX = cellOf(x);
  const cellZ = cellOf(z);
  const pick = hashNoise(cellX * 1.7, 5.3, cellZ * 2.3);
  const clump = valueNoise(x * 6, 1.1, z * 6);
  if (seasonName === 'spring') {
    if (pick > 0.94) return { height: 1, kind: 'flower' };
    if (pick > 0.86 && clump > 0.55) return { height: 1, kind: 'tuft' };
  }
  if (seasonName === 'summer') {
    if (pick > 0.86 && clump > 0.5) return { height: pick > 0.96 ? 3 : 2, kind: 'tallGrass' };
    if (pick > 0.72 && pick <= 0.78 && clump > 0.4) return { height: 1, kind: 'flower' };
  }
  if (seasonName === 'autumn') {
    const fromTree = Math.hypot(x - TREE.x, z - TREE.z);
    if (fromTree < 0.4 && pick > 0.7 + fromTree * 0.6) return { height: 1, kind: 'leafPile' };
    if (pick > 0.9 && clump > 0.55) return { height: 1, kind: 'driedTuft' };
  }
  if (seasonName === 'winter') {
    const byCabin = Math.abs(x - CABIN.x) < 0.24 && Math.abs(z - CABIN.z) < 0.22;
    if ((nearFence(x, z, 0.09) || byCabin) && pick > 0.3) return { height: pick > 0.85 ? 2 : 1, kind: 'drift' };
  }
  return null;
}

export function groundDetailDistance(x, y, z, seasonName) {
  if (y < 0 || y > 0.07) return Infinity;
  const detail = groundDetailAt(x, z, seasonName);
  if (!detail) return Infinity;
  return y < detail.height * VOXEL ? -0.001 : Infinity;
}

// ---- Season props ----

export const PUMPKINS = [[-0.13, -0.01], [-0.03, 0.01]];
export const SNOWMAN = { x: -0.07, z: 0.41 };
export const BUSHES = [[-0.56, 0.0, 0.05], [0.62, -0.02, 0.05], [-0.1, -0.12, 0.045]];
export const REEDS = [[0.57, 0.27, 0.1], [0.59, 0.23, 0.13], [0.53, 0.33, 0.08], [0.61, 0.27, 0.06]];
export const LILY_PADS = [[0.41, 0.29, 0.03], [0.49, 0.19, 0.025], [0.33, 0.37, 0.022]];

export function seasonPropsDistance(x, y, z, seasonName) {
  if (y > 0.38) return Infinity;
  let distance = Infinity;
  if (seasonName === 'spring' || seasonName === 'summer') {
    for (const [bushX, bushZ, radius] of BUSHES) distance = Math.min(distance, sphereDistance(x, y, z, bushX, radius * 0.6, bushZ, radius * (seasonName === 'summer' ? 1.15 : 0.95)));
    for (const [reedX, reedZ, height] of REEDS) distance = Math.min(distance, boxDistance(x, y, z, reedX, (height - 0.04) / 2, reedZ, 0.009, (height + 0.04) / 2, 0.009));
  }
  if (seasonName === 'autumn') {
    for (const [pumpkinX, pumpkinZ] of PUMPKINS) {
      distance = Math.min(distance, ellipsoidDistance(x, y, z, pumpkinX, 0.03, pumpkinZ, 0.045, 0.035, 0.045));
      distance = Math.min(distance, boxDistance(x, y, z, pumpkinX, 0.075, pumpkinZ, 0.009, 0.012, 0.009));
    }
  }
  if (seasonName === 'winter') {
    distance = Math.min(distance, sphereDistance(x, y, z, SNOWMAN.x, 0.07, SNOWMAN.z, 0.075));
    distance = Math.min(distance, sphereDistance(x, y, z, SNOWMAN.x, 0.18, SNOWMAN.z, 0.054));
    distance = Math.min(distance, sphereDistance(x, y, z, SNOWMAN.x, 0.27, SNOWMAN.z, 0.042));
    distance = Math.min(distance, capsuleDistance(x, y, z, SNOWMAN.x, 0.27, SNOWMAN.z + 0.03, SNOWMAN.x, 0.27, SNOWMAN.z + 0.07, 0.011));
    distance = Math.min(distance, boxDistance(x, y, z, SNOWMAN.x, 0.34, SNOWMAN.z, 0.03, 0.03, 0.03));
    distance = Math.min(distance, boxDistance(x, y, z, SNOWMAN.x, 0.31, SNOWMAN.z, 0.05, 0.009, 0.05));
  }
  return distance;
}
