// "Pocket Seasons": one stepped island with a log cabin, a tree, a pond and a picket fence, in four seasons.
// Every part is snapped to the same 0.02 blocks (island-parts.js), so the ground, the tree and the house read as one
// kind of block art with one colour per block face. The seasons differ in shape as well as colour: the tree's crown
// grows, fills, thins and goes bare; the ground gets flowers, tall grass, fallen leaves or drifts; chimney smoke only
// rises when it is cold; and wind carries petals, leaves or snow across the island.
import { hashNoise, valueNoise, capsuleDistance, sphereDistance, smoothUnion, voxelizeModel, placeSplats } from './voxel-splats.js';
import {
  VOXEL, cellOf, pondOutline, waterDistance, islandDistance, cabinDistance, CHIMNEY, pathDistance, onStone, fenceDistance,
  nearFence, rocksDistance, onRim, ROCKS, groundDetailAt, groundDetailDistance, seasonPropsDistance, PUMPKINS, SNOWMAN, BUSHES,
  REEDS, LILY_PADS, TREE,
} from './island-parts.js';

const hex = value => [parseInt(value.slice(1, 3), 16) / 255, parseInt(value.slice(3, 5), 16) / 255, parseInt(value.slice(5, 7), 16) / 255];

const SEASONS = {
  spring: {
    grass: ['#9ad65e', '#78c04e'], soil: ['#8a6448', '#6e4e38', '#563c2c'], soilSpot: ['#5e9a44', '#4a7e3a'],
    water: ['#7cc8e8', '#5aaad8', '#a8e0f4'], sun: [1.15, 1.02, 0.92], ambient: [0.55, 0.6, 0.72], background: '#101826',
    crown: 'blossom', smoke: null, roofSnow: false, icicles: false,
  },
  summer: {
    grass: ['#6ec44a', '#54ac40'], soil: ['#c09060', '#a07448', '#7e5a3a'], soilSpot: ['#d8b888', '#d8b888'],
    water: ['#5ec0e8', '#3a9ad4', '#9adcf4'], sun: [1.25, 1.08, 0.88], ambient: [0.5, 0.58, 0.74], background: '#0c1624',
    crown: 'full', smoke: null, roofSnow: false, icicles: false,
  },
  autumn: {
    grass: ['#bca44a', '#a08a3c'], soil: ['#9a7050', '#7a5640', '#5a4030'], soilSpot: ['#4a3424', '#e0802c'],
    water: ['#3e86a8', '#2e6688', '#6ab4d0'], sun: [1.2, 0.92, 0.72], ambient: [0.6, 0.52, 0.6], background: '#160f18',
    crown: 'thinning', smoke: { puffs: 4, rise: 0.26, size: 0.03, colors: ['#e6e8ee', '#c8ccd6'] }, roofSnow: false, icicles: false,
  },
  winter: {
    grass: ['#f4f8fc', '#e0e9f3'], soil: ['#7e6a5e', '#5e4c44', '#43363a'], soilSpot: ['#c4d4e6', '#c4d4e6'],
    water: ['#cfe6f4', '#a8cce4', '#eef6fc'], sun: [0.95, 1.0, 1.12], ambient: [0.62, 0.68, 0.86], background: '#0a0f1c',
    crown: 'bare', smoke: { puffs: 8, rise: 0.34, size: 0.048, colors: ['#b4b8c4', '#8e94a2'] }, roofSnow: true, icicles: true,
  },
};

const LEAF_COLORS = { autumn: ['#ffc040', '#f08a2a', '#d0502a'] };
const FLOWER_COLORS = ['#ffe066', '#ff8ab0', '#ffffff', '#b48cff'];
const SNOW = '#f4f8fc';

// ---- Tree: same limbs every season, a crown that changes shape ----

// [start, end, radius]; radii stay at 0.016 or more so a diagonal branch never breaks into loose blocks.
const TREE_LIMBS = [
  [[0.24, 0.0, -0.18], [0.24, 0.27, -0.18], 0.045],
  [[0.24, 0.26, -0.18], [0.08, 0.52, -0.2], 0.03],
  [[0.24, 0.26, -0.18], [0.42, 0.5, -0.12], 0.03],
  [[0.24, 0.26, -0.18], [0.27, 0.56, -0.36], 0.028],
  [[0.08, 0.52, -0.2], [-0.02, 0.7, -0.24], 0.021],
  [[0.08, 0.52, -0.2], [0.14, 0.74, -0.12], 0.021],
  [[0.42, 0.5, -0.12], [0.52, 0.68, -0.08], 0.021],
  [[0.42, 0.5, -0.12], [0.36, 0.76, -0.16], 0.021],
  [[0.27, 0.56, -0.36], [0.22, 0.78, -0.42], 0.02],
  [[0.27, 0.56, -0.36], [0.36, 0.72, -0.44], 0.02],
  [[-0.02, 0.7, -0.24], [-0.09, 0.79, -0.2], 0.016],
  [[-0.02, 0.7, -0.24], [0.02, 0.83, -0.3], 0.016],
  [[0.14, 0.74, -0.12], [0.2, 0.83, -0.06], 0.016],
  [[0.52, 0.68, -0.08], [0.61, 0.75, -0.02], 0.016],
  [[0.52, 0.68, -0.08], [0.5, 0.81, -0.04], 0.016],
  [[0.36, 0.76, -0.16], [0.3, 0.85, -0.12], 0.016],
  [[0.22, 0.78, -0.42], [0.16, 0.85, -0.46], 0.016],
  [[0.36, 0.72, -0.44], [0.45, 0.79, -0.48], 0.016],
  [[0.16, 0.39, -0.19], [0.04, 0.44, -0.1], 0.016],
  [[0.33, 0.38, -0.15], [0.46, 0.4, -0.24], 0.016],
];

const CROWN_BALLS = [
  [0.24, 0.52, -0.18, 0.2], [0.08, 0.62, -0.16, 0.14], [0.42, 0.6, -0.12, 0.15], [0.26, 0.62, -0.36, 0.14],
  [0.2, 0.76, -0.2, 0.13], [0.36, 0.74, -0.26, 0.11], [0.12, 0.76, -0.3, 0.1], [0.4, 0.66, -0.34, 0.1],
];

// Spring: a smaller, airy crown of separate clumps. Summer: one full, wide crown. Autumn: the summer crown with holes
// eaten through it and bare twig tips poking out. Winter: no crown.
const CROWN_SHAPES = {
  blossom: { scale: 0.66, blend: 0.06, holes: 0, twigs: false },
  full: { scale: 1.06, blend: 0.08, holes: 0, twigs: false },
  thinning: { scale: 0.92, blend: 0.07, holes: 0.3, twigs: true },
  bare: null,
};

function treeDistance(x, y, z, crownKind) {
  const shape = CROWN_SHAPES[crownKind];
  let distance = Infinity;
  for (const [start, end, radius] of TREE_LIMBS) {
    if (shape && !shape.twigs && radius < 0.025) continue;
    distance = Math.min(distance, capsuleDistance(x, y, z, start[0], start[1], start[2], end[0], end[1], end[2], radius));
  }
  if (!shape) return distance;
  // Start from the first ball: smoothUnion with Infinity gives NaN, and one NaN splat blanks the whole frame.
  let crown = Infinity;
  for (const [centerX, centerY, centerZ, radius] of CROWN_BALLS) {
    const ball = sphereDistance(x, y, z, centerX, centerY, centerZ, radius * shape.scale);
    crown = crown === Infinity ? ball : smoothUnion(crown, ball, shape.blend);
  }
  crown += (valueNoise(x * 12, y * 12, z * 12) - 0.5) * 0.03;
  if (shape.holes > 0) crown += Math.max(0, valueNoise(x * 9 + 4, y * 9, z * 9) - 0.5) * shape.holes;
  return Math.min(distance, crown);
}

// ---- Smoke, particles and wind, all snapped to the same blocks ----

const BLOCK_OFFSETS = [-0.0066, 0, 0.0066];

function pushBlock(points, cellX, cellY, cellZ, color, spacing) {
  const centreX = (cellX + 0.5) * VOXEL;
  const centreY = (cellY + 0.5) * VOXEL;
  const centreZ = (cellZ + 0.5) * VOXEL;
  for (const offsetX of BLOCK_OFFSETS) {
    for (const offsetY of BLOCK_OFFSETS) {
      for (const offsetZ of BLOCK_OFFSETS) points.push({ x: centreX + offsetX, y: centreY + offsetY, z: centreZ + offsetZ, color, scale: spacing * 0.62 });
    }
  }
}

function pushBlockAt(points, x, y, z, color, spacing) {
  pushBlock(points, cellOf(x), cellOf(y), cellOf(z), color, spacing);
}

// A lumpy cloud of blocks round a centre: the smoke puffs.
function pushCloud(points, centreX, centreY, centreZ, radius, color, spacing, seed) {
  const reach = Math.ceil(radius / VOXEL) + 1;
  const baseX = cellOf(centreX);
  const baseY = cellOf(centreY);
  const baseZ = cellOf(centreZ);
  for (let stepX = -reach; stepX <= reach; stepX++) {
    for (let stepY = -reach; stepY <= reach; stepY++) {
      for (let stepZ = -reach; stepZ <= reach; stepZ++) {
        const cellX = baseX + stepX;
        const cellY = baseY + stepY;
        const cellZ = baseZ + stepZ;
        const distance = Math.hypot((cellX + 0.5) * VOXEL - centreX, (cellY + 0.5) * VOXEL - centreY, (cellZ + 0.5) * VOXEL - centreZ);
        const lumpy = radius * (0.75 + hashNoise(cellX + seed, cellY, cellZ) * 0.45);
        if (distance < lumpy) pushBlock(points, cellX, cellY, cellZ, color, spacing);
      }
    }
  }
}

const WIND = { x: -1, z: 0.25 };

// Wind lines: one splat thick (a single pixel at this size), long, with a small curl at the head, drawn in front of
// and above the island so they never lie across the cabin.
function windStreaks(points, time, count, color, spacing) {
  for (let index = 0; index < count; index++) {
    const cycle = 3.2 + index * 0.7;
    const age = ((time + index * 1.37) % cycle) / cycle;
    const round = Math.floor((time + index * 1.37) / cycle);
    const headX = 1.0 - age * 2.1;
    const height = 0.5 + hashNoise(index, 3.3, round) * 0.4;
    const depth = 0.35 + hashNoise(index, 8.1, round) * 0.4;
    // The line grows in, then shrinks away from its tail, like a gust passing.
    const length = 0.42 * Math.sin(Math.PI * age);
    for (let along = 0; along < length; along += spacing) {
      const x = headX + along;
      const y = height + Math.sin(along * 12 + index) * 0.012;
      points.push({ x, y, z: depth - along * WIND.z, color, scale: spacing * 0.62 });
    }
    for (let turn = 0; turn < 10; turn++) {
      const angle = turn * 0.55;
      points.push({ x: headX - Math.sin(angle) * 0.025, y: height + (1 - Math.cos(angle)) * 0.025, z: depth, color, scale: spacing * 0.62 });
    }
  }
}

// A small speck (snow, firefly): a 2 x 2 x 2 cluster snapped to the block grid, two pixels across.
function pushSpeck(points, x, y, z, color, spacing) {
  const centreX = (cellOf(x) + 0.5) * VOXEL;
  const centreY = (cellOf(y) + 0.5) * VOXEL;
  const centreZ = (cellOf(z) + 0.5) * VOXEL;
  for (const offsetX of [-0.0035, 0.0035]) {
    for (const offsetY of [-0.0035, 0.0035]) {
      for (const offsetZ of [-0.0035, 0.0035]) points.push({ x: centreX + offsetX, y: centreY + offsetY, z: centreZ + offsetZ, color, scale: spacing * 0.62 });
    }
  }
}

function packPoints(points) {
  const positions = new Float32Array(points.length * 3);
  const colors = new Float32Array(points.length * 4);
  const scales = new Float32Array(points.length);
  points.forEach((point, index) => {
    positions.set([point.x, point.y, point.z], index * 3);
    colors.set([...point.color, 1], index * 4);
    scales[index] = point.scale;
  });
  return { count: points.length, positions, colors, scales };
}

// ---- Scene ----

export function buildSeason(spacing, seasonName, look = {}) {
  const season = SEASONS[seasonName];
  const usedColors = new Set();
  const paint = (value, emission = 0) => {
    usedColors.add(value);
    return [...hex(value), emission];
  };
  // look.clusters picks colours in patches a few blocks wide instead of per block, so faces read as areas, not speckle.
  const variation = (cellX, cellY, cellZ) => look.clusters ? valueNoise(cellX * 0.3, cellY * 0.3, cellZ * 0.3) : hashNoise(cellX, cellY, cellZ);
  const pick = (list, cellX, cellY, cellZ, salt = 0) => list[Math.min(list.length - 1, Math.floor(variation(cellX + salt * 17, cellY, cellZ) * list.length))];
  const light = { sun: [0.55, 0.7, 0.45], sunColor: season.sun, ambientColor: season.ambient, rimColor: [0.4, 0.4, 0.5], shadowSoftness: 2, toon: look.toon ? [[0.75, 1.08], [0.38, 0.78], [-1, 0.55]] : undefined };
  const winter = seasonName === 'winter';
  const autumn = seasonName === 'autumn';

  const solidParts = (x, y, z) => Math.min(
    islandDistance(x, y, z, season), waterDistance(x, y, z), pathDistance(x, y, z), fenceDistance(x, y, z), rocksDistance(x, y, z),
    seasonPropsDistance(x, y, z, seasonName),
  );
  const shadowDistance = (x, y, z) => Math.min(solidParts(x, y, z), cabinDistance(x, y, z, seasonName), treeDistance(x, y, z, season.crown));

  const world = voxelizeModel({
    distance: (x, y, z) => Math.min(solidParts(x, y, z), groundDetailDistance(x, y, z, seasonName)),
    bounds: [-0.82, -0.72, -0.66, 0.82, 0.36, 0.66],
    material: (x, y, z, faceX, faceY) => worldMaterial(x, y, z, faceY),
  }, spacing, light, { shadowModel: { distance: shadowDistance }, voxel: look.voxel ?? VOXEL, splatScale: look.splatScale ?? 0.62, jitter: look.jitter ?? 0 });

  function worldMaterial(x, y, z, faceY) {
    const cellX = cellOf(x);
    const cellY = cellOf(y);
    const cellZ = cellOf(z);
    const topFace = faceY > 0;
    const snowCap = winter && topFace;
    if (seasonPropsDistance(x, y, z, seasonName) <= 0) return propMaterial(x, y, z, cellX, cellY, cellZ, faceY);
    if (fenceDistance(x, y, z) <= 0) return snowCap ? paint(SNOW) : paint(topFace ? '#f6f1e6' : '#d8cfbc');
    if (pathDistance(x, y, z) <= 0) return snowCap && hashNoise(cellX, 1, cellZ) > 0.4 ? paint(SNOW) : paint(topFace ? '#c4beb2' : '#7c766c');
    if (rocksDistance(x, y, z) <= 0) {
      if (snowCap) return paint(SNOW);
      if (autumn && topFace && hashNoise(cellX, 4, cellZ) > 0.7) return paint(pick(LEAF_COLORS.autumn, cellX, 0, cellZ));
      return paint(topFace ? '#aaa69e' : '#76726c');
    }
    if (y > 0) return groundDetailMaterial(x, z, cellX, cellY, cellZ);
    const icicle = season.icicles && y < -0.11 && y > -0.24 && (cellZ === cellOf(0.61) || cellX === cellOf(0.77));
    if (icicle) return paint(faceY > 0 ? SNOW : '#cfe8f8');
    if (waterDistance(x, y, z) <= 0 && islandDistance(x, y, z, season) > 0) return waterMaterial(x, z, cellX, cellZ);
    if (topFace && cellY === -1) return grassMaterial(x, z, cellX, cellZ);
    return earthMaterial(cellX, cellY, cellZ, topFace);
  }

  function grassMaterial(x, z, cellX, cellZ) {
    const patch = valueNoise(x * 5, 0, z * 5) * 0.7 + valueNoise(x * 13, 0, z * 13) * 0.3;
    const base = season.grass[patch > 0.55 ? 0 : 1];
    if (seasonName === 'spring') {
      // A worn dirt patch in front of the door and along the start of the path.
      const worn = Math.hypot((x + 0.38) / 1.3, z - 0.05) < 0.06 + valueNoise(x * 20, 2, z * 20) * 0.03;
      if (worn) return paint('#a07850');
      if (hashNoise(cellX, 9, cellZ) > 0.97) return paint(pick(FLOWER_COLORS, cellX, 1, cellZ));
    }
    if (seasonName === 'summer' && patch < 0.3 && hashNoise(cellX, 9, cellZ) > 0.6) return paint('#8ea640');
    if (autumn) {
      // Fallen leaves: thick under the crown, thinning out toward the fence.
      const fromTree = Math.hypot(x - TREE.x, z - TREE.z);
      const density = Math.max(0, 1 - fromTree / 0.5) * 0.85 + 0.06;
      if (variation(cellX, 7, cellZ) < density) return paint(pick(LEAF_COLORS.autumn, cellX, 3, cellZ));
    }
    if (winter) {
      if (footprint(x, z)) return paint('#b6c6da');
      if (onStone(x, z)) return paint(SNOW);
    }
    return paint(base);
  }

  // Footprints in the snow from the door to the snowman: left and right prints, one block each, every few blocks.
  function footprint(x, z) {
    const fromX = -0.27;
    const fromZ = -0.02;
    const toX = SNOWMAN.x + 0.04;
    const toZ = SNOWMAN.z - 0.09;
    const lengthTotal = Math.hypot(toX - fromX, toZ - fromZ);
    const alongX = (toX - fromX) / lengthTotal;
    const alongZ = (toZ - fromZ) / lengthTotal;
    for (let step = 0; step * 0.05 < lengthTotal; step++) {
      const side = step % 2 === 0 ? 1 : -1;
      const printX = fromX + alongX * step * 0.05 - alongZ * side * 0.02;
      const printZ = fromZ + alongZ * step * 0.05 + alongX * side * 0.02;
      if (cellOf(x) === cellOf(printX) && cellOf(z) === cellOf(printZ)) return true;
    }
    return false;
  }

  function waterMaterial(x, z, cellX, cellZ) {
    const shimmer = hashNoise(cellX, 11, cellZ);
    if (winter) {
      if (valueNoise(x * 14, 5, z * 14) > 0.68) return paint(SNOW);
      return paint(shimmer > 0.88 ? season.water[1] : season.water[0]);
    }
    if (seasonName === 'summer' || seasonName === 'spring') {
      for (const [padX, padZ, radius] of LILY_PADS) {
        const reach = seasonName === 'spring' ? radius * 0.7 : radius;
        if (Math.hypot(x - padX, z - padZ) < reach) return paint(seasonName === 'summer' && Math.hypot(x - padX - 0.01, z - padZ) < 0.011 ? '#ff9ac0' : '#4e9a3c');
      }
    }
    if (autumn && shimmer > 0.93) return paint(pick(LEAF_COLORS.autumn, cellX, 5, cellZ));
    if (pondOutline(x, z) > -0.025) return paint(season.water[1]);
    return paint(shimmer > 0.86 ? season.water[2] : season.water[0]);
  }

  // The island's sides and lower ledges: soil bands with each season's own spots, roots, frost and snowy ledges.
  function earthMaterial(cellX, cellY, cellZ, topFace) {
    if (topFace) {
      if (winter) return paint(SNOW);
      if (autumn) return paint(hashNoise(cellX, cellY, cellZ) > 0.5 ? pick(LEAF_COLORS.autumn, cellX, cellY, cellZ) : season.grass[1]);
      return paint(season.grass[1]);
    }
    // The lip of the top terrace keeps the ground cover's colour.
    if (cellY === -1) return paint(winter ? SNOW : season.grass[1]);
    const spot = hashNoise(cellX * 1.3, cellY * 0.7, cellZ * 1.9);
    if (seasonName === 'spring' && spot > 0.8 && cellY > -16) return paint(season.soilSpot[spot > 0.92 ? 1 : 0]);
    if (seasonName === 'summer' && spot > 0.9) return paint(season.soilSpot[0]);
    if (autumn) {
      // Pale roots hang in vertical strands down the soil.
      const rootColumn = hashNoise(cellX, 0.5, cellZ) > 0.84 && cellY < -6 && cellY > -6 - Math.floor(hashNoise(cellX, 1.5, cellZ) * 14);
      if (rootColumn) return paint('#c49a68');
      if (spot > 0.975) return paint(season.soilSpot[1]);
    }
    if (winter && spot > 0.9 && cellY > -14) return paint(season.soilSpot[0]);
    const band = ((Math.floor(cellY / 3) % 3) + 3) % 3;
    return paint(season.soil[band]);
  }

  function groundDetailMaterial(x, z, cellX, cellY, cellZ) {
    const detail = groundDetailAt(x, z, seasonName);
    if (!detail) return paint(season.grass[1]);
    const topBlock = cellY === detail.height - 1;
    if (detail.kind === 'flower') return paint(pick(FLOWER_COLORS, cellX, 2, cellZ));
    if (detail.kind === 'tuft') return paint('#62b04a');
    if (detail.kind === 'tallGrass') return paint(topBlock ? (detail.height === 3 ? '#d6cc6a' : '#7cc456') : '#4a9a3c');
    if (detail.kind === 'leafPile') return paint(pick(LEAF_COLORS.autumn, cellX, cellY + 6, cellZ));
    if (detail.kind === 'driedTuft') return paint('#b0923e');
    return paint(topBlock ? SNOW : '#e0e9f3');
  }

  function propMaterial(x, y, z, cellX, cellY, cellZ, faceY) {
    if (seasonName === 'spring' || seasonName === 'summer') {
      for (const [reedX, reedZ, height] of REEDS) {
        if (cellX === cellOf(reedX) && cellZ === cellOf(reedZ)) return paint(y > height - 0.02 && y > 0.02 ? '#7a4e32' : '#5e9a3c');
      }
      const blossom = seasonName === 'spring' && hashNoise(cellX, cellY, cellZ) > 0.6;
      if (blossom) return paint(hashNoise(cellX, cellY + 3, cellZ) > 0.5 ? '#ffd0e0' : '#ffffff');
      if (seasonName === 'summer' && hashNoise(cellX, cellY, cellZ) > 0.93) return paint('#d83a3a');
      return paint(faceY > 0 ? (seasonName === 'spring' ? '#86cc56' : '#4a9a3c') : (seasonName === 'spring' ? '#5fae44' : '#2e7434'));
    }
    if (autumn) {
      for (const [pumpkinX, pumpkinZ] of PUMPKINS) {
        if (Math.hypot(x - pumpkinX, z - pumpkinZ) < 0.06) {
          if (y > 0.062) return paint('#4e6a2c');
          // Vertical ribs: every other column a shade darker.
          return paint((cellX + cellZ) % 2 === 0 ? '#ff9a30' : '#e07424');
        }
      }
    }
    if (winter) {
      const front = z > SNOWMAN.z + 0.02;
      if (z > SNOWMAN.z + 0.045 && Math.abs(y - 0.27) < 0.012) return paint('#ff8a30');
      if (front && cellY === cellOf(0.29) && (cellX === cellOf(SNOWMAN.x - 0.02) || cellX === cellOf(SNOWMAN.x + 0.02))) return paint('#1a2030');
      if (front && cellX === cellOf(SNOWMAN.x) && (cellY === cellOf(0.17) || cellY === cellOf(0.21))) return paint('#1a2030');
      if (cellY === cellOf(0.225)) return paint('#c83c3c');
      if (y > 0.3) return paint('#24242c');
      return paint(faceY > 0 ? SNOW : '#c8d6e6');
    }
    return paint('#8a8a8a');
  }

  const cabin = voxelizeModel({
    distance: (x, y, z) => cabinDistance(x, y, z, seasonName),
    bounds: [-0.56, -0.01, -0.4, -0.12, 0.52, 0.0],
    material: (x, y, z, faceX, faceY, faceZ) => cabinMaterial(x, y, z, faceX, faceY, faceZ),
  }, spacing, light, { shadowModel: { distance: shadowDistance }, voxel: look.voxel ?? VOXEL, splatScale: look.splatScale ?? 0.62, jitter: look.jitter ?? 0 });

  // The cabin drawn in block cells: walls span cells x -25..-10, z -17..-4, y 0..12.
  function cabinMaterial(x, y, z, faceX, faceY, faceZ) {
    const cellX = cellOf(x);
    const cellY = cellOf(y);
    const cellZ = cellOf(z);
    if (y < 0.02 && z > -0.06) return paint(winter && faceY > 0 ? SNOW : '#a09c94');
    if (cellZ === -3 && cellY >= 4 && cellY <= 5 && cellX >= -24 && cellX <= -20) {
      if (cellY === 5) return paint(pick(seasonName === 'spring' ? ['#ff9ac0', '#ffffff', '#ffd0e0'] : ['#e83c3c', '#ffd23c', '#ff8a30'], cellX, cellY, cellZ));
      if (faceY > 0) return paint(winter ? SNOW : autumn ? '#8a6a3a' : '#5e9a3c');
      return paint('#7a5236');
    }
    const chimney = (cellX === -23 || cellX === -22) && (cellZ === -15 || cellZ === -14) && y > 0.25;
    if (chimney) {
      if (winter && faceY > 0 && cellY < 24) return paint(SNOW);
      return paint((cellY + (cellX === -23 ? 0 : 1)) % 2 === 0 ? '#9a6a54' : '#7a5040');
    }
    if (y > 0.25) {
      if (season.roofSnow && faceY > 0) return paint(hashNoise(cellX, cellY, cellZ) > 0.9 ? '#dce6f0' : SNOW);
      return paint(cellY % 2 === 0 ? '#c8583c' : '#9a3e2e');
    }
    const front = faceZ > 0 && cellZ === -4;
    const side = faceX > 0 && cellX === -10;
    if (front) {
      const window = cellX >= -23 && cellX <= -21 && cellY >= 5 && cellY <= 7;
      if (window) return cellX === -22 || cellY === 6 ? paint('#5e3e2e') : paint('#ffcc66', 1);
      if (cellX >= -24 && cellX <= -20 && cellY >= 4 && cellY <= 8) return paint('#f4efe6');
      const door = cellX >= -15 && cellX <= -13 && cellY <= 6;
      if (door) return paint(cellX === -13 && cellY === 3 ? '#ffcc66' : cellY % 2 === 0 ? '#6e4a34' : '#5e3e2e');
      if (cellX >= -16 && cellX <= -12 && cellY <= 7) return paint('#f4efe6');
    }
    if (side) {
      const window = cellZ >= -12 && cellZ <= -10 && cellY >= 5 && cellY <= 7;
      if (window) return cellZ === -11 || cellY === 6 ? paint('#5e3e2e') : paint('#ffcc66', 1);
      if (cellZ >= -13 && cellZ <= -9 && cellY >= 4 && cellY <= 8) return paint('#f4efe6');
    }
    // Log ends stick out at the corners; elsewhere horizontal logs with a darker gap every third row.
    const corner = (cellX === -25 || cellX === -10) && (cellZ === -17 || cellZ === -4);
    if (corner) return paint(cellY % 2 === 0 ? '#b8865a' : '#8a5a3a');
    return paint(cellY % 3 === 2 ? '#9a6a44' : '#d2a274');
  }

  const crownShape = CROWN_SHAPES[season.crown];
  const tree = voxelizeModel({
    distance: (x, y, z) => treeDistance(x, y, z, season.crown),
    bounds: [-0.16, -0.01, -0.58, 0.68, 0.94, 0.14],
    material: (x, y, z, faceX, faceY) => treeMaterial(x, y, z, faceY),
  }, spacing, light, { shadowModel: { distance: shadowDistance }, voxel: look.voxel ?? VOXEL, splatScale: look.splatScale ?? 0.62, jitter: look.jitter ?? 0 });

  function treeMaterial(x, y, z, faceY) {
    const cellX = cellOf(x);
    const cellY = cellOf(y);
    const cellZ = cellOf(z);
    let limbDistance = Infinity;
    for (const [start, end, radius] of TREE_LIMBS) limbDistance = Math.min(limbDistance, capsuleDistance(x, y, z, start[0], start[1], start[2], end[0], end[1], end[2], radius));
    const isWood = !crownShape || limbDistance <= 0.002 && (y < 0.34 || crownShape.twigs);
    if (isWood) {
      if (winter && faceY > 0 && y > 0.2) return paint(SNOW);
      return paint(cellY % 3 === 0 ? '#5a3c2a' : '#6e4a34');
    }
    const roll = variation(cellX, cellY, cellZ);
    if (seasonName === 'spring') {
      if (roll > 0.42) return paint(roll > 0.88 ? '#ffffff' : faceY > 0 ? '#ffc4dc' : '#f294b8');
      return paint(faceY > 0 ? '#a6dc6a' : '#7cc456');
    }
    if (seasonName === 'summer') return paint(faceY > 0 ? (roll > 0.7 ? '#8ad45e' : '#6cc04c') : (roll > 0.6 ? '#3e9a40' : '#2e7a38'));
    return paint(pick(LEAF_COLORS.autumn, cellX, cellY, cellZ, faceY > 0 ? 0 : 1));
  }

  // Colours the particles use, so the palette keeps them.
  const particleColors = {
    spring: ['#ffc4dc', '#fff0f6'], summer: ['#f8f080', '#fffbc8'], autumn: LEAF_COLORS.autumn, winter: ['#ffffff', '#e6eef8'],
  }[seasonName];
  const streakColor = winter ? '#dfe8f4' : '#eef4ff';
  for (const value of [...particleColors, streakColor, ...(season.smoke ? season.smoke.colors : []), season.background, '#1a2030']) usedColors.add(value);
  const palette = [];
  for (const value of usedColors) for (const level of look.toon ? [1.08, 0.78, 0.55] : [1.25, 1, 0.78, 0.6, 0.45]) palette.push(hex(value).map(channel => Math.min(1, channel * level)));
  palette.unshift(hex(season.background));

  const swayAmount = { spring: 0.008, summer: 0.006, autumn: 0.01, winter: 0.004 }[seasonName];

  return {
    name: seasonName,
    palette,
    background: { inner: hex(season.background), outer: hex(season.background), stars: false },
    camera: { target: [0.03, -0.01, 0], distance: 3.8, height: 1.15, startAngle: 0.9 },
    staticLists: [world, cabin],
    // Parts kept apart so season-cycle.js can blend two seasons block by block.
    parts: { world, cabin, tree },
    swayAmount,
    backgroundColor: hex(season.background),
    dynamic(time) {
      return [swayTree(tree, time, swayAmount), packPoints(effects(time, 1))];
    },
    effects,
    glows() {
      return [];
    },
    contactShadows() {
      return [];
    },
  };

  // Smoke, falling things and wind lines; amount 0..1 thins them out while a season fades in or out.
  function effects(time, amount) {
    const points = [];
    if (amount <= 0) return points;
    {
      const colors = particleColors.map(hex);
      if (season.smoke) {
        const { rise, size } = season.smoke;
        const puffs = Math.round(season.smoke.puffs * amount);
        const smokeColors = season.smoke.colors.map(hex);
        for (let index = 0; index < puffs; index++) {
          const age = (time * 0.2 + index / puffs) % 1;
          const radius = size * (0.45 + age * 0.75);
          const centreX = CHIMNEY.x + age * 0.2 * WIND.x + Math.sin(age * 5 + index) * 0.012;
          const centreY = CHIMNEY.top + 0.03 + age * rise;
          const centreZ = CHIMNEY.z + age * 0.2 * WIND.z;
          pushCloud(points, centreX, centreY, centreZ, radius, smokeColors[age > 0.5 ? 1 : 0], spacing, index * 31);
        }
      }
      if (seasonName === 'summer') {
        // Fireflies drifting low over the grass and the pond, each blinking on its own beat.
        for (let index = 0; index < Math.round(14 * amount); index++) {
          if (Math.sin(time * 3 + index * 2.1) < -0.5) continue;
          const x = Math.sin(time * 0.4 + index * 1.9) * 0.6;
          const z = Math.cos(time * 0.33 + index * 2.7) * 0.5 + 0.1;
          const y = 0.12 + (Math.sin(time * 0.9 + index) + 1) * 0.09;
          pushBlockAt(points, x, y, z, colors[index % 2], spacing);
        }
      } else {
        // Petals, leaves or snow, blown along the wind as they fall.
        const count = Math.round({ spring: 16, autumn: 18, winter: 80 }[seasonName] * amount);
        const fallSpeed = winter ? 0.24 : 0.16;
        for (let index = 0; index < count; index++) {
          const age = (time * fallSpeed + index * 0.618) % 1;
          const startX = winter ? Math.sin(index * 12.9) * 0.9 + 0.3 : TREE.x + Math.sin(index * 7.1) * 0.2;
          const startZ = winter ? Math.cos(index * 4.7) * 0.65 : TREE.z + Math.cos(index * 3.3) * 0.18;
          const startY = winter ? 1.2 : 0.7;
          const drop = winter ? 1.3 : 0.72;
          const drift = (winter ? 0.4 : 0.5) * age;
          const flutter = winter ? 0 : Math.sin(age * 9 + index) * 0.03;
          const place = winter ? pushSpeck : pushBlockAt;
          place(points, startX + drift * WIND.x + flutter, startY - age * drop, startZ + drift * WIND.z, colors[index % colors.length], spacing);
        }
      }
      windStreaks(points, time, Math.round((winter ? 4 : 3) * amount), hex(streakColor), spacing);
    }
    return points;
  }
}

// The tree leans with the wind: more at the top, a slow sway with a quicker gust on top.
export function swayTree(list, time, swayAmount) {
  const gust = Math.sin(time * 1.7) * 0.6 + Math.sin(time * 4.3 + 1) * 0.4;
  return placeSplats(list, {
    deform: (localX, localY, localZ) => {
      const lean = Math.max(0, localY - 0.2) ** 2 * swayAmount * 2.2 * gust;
      return [localX + lean * WIND.x, localY, localZ + lean * WIND.z];
    },
  });
}

export { packPoints, WIND };

// Kept for scenes.js and the film plans.
export { SEASONS, BUSHES, ROCKS, nearFence, onRim };
