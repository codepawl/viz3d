// A haunted medieval crag: ruined chapel with a bell tower, graveyard, dead tree, a hooded monk with a lantern,
// crows round the tower, a ghost rising from a grave, falling ash and lantern embers.
import {
  hashNoise, valueNoise, sphereDistance, ellipsoidDistance, boxDistance, cylinderDistance, taperedCylinderDistance,
  capsuleDistance, islandDistance, voxelizeModel, placeSplats,
} from './voxel-splats.js';
import { easeOutCubic, easeInOutCubic, stepAndHold, struckSwing, wobble } from './motion.js';

const hex = value => [1, 3, 5].map(start => parseInt(value.slice(start, start + 2), 16) / 255);

function makeList(points) {
  const count = points.length;
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 4);
  const scales = new Float32Array(count);
  points.forEach((point, index) => {
    positions.set([point.x, point.y, point.z], index * 3);
    colors.set([point.color[0], point.color[1], point.color[2], point.alpha ?? 1], index * 4);
    scales[index] = point.scale;
  });
  return { count, positions, colors, scales };
}

function pyramidDistance(x, y, z, centerX, bottomY, centerZ, halfWidth, height) {
  const amount = Math.min(Math.max((y - bottomY) / height, 0), 1);
  const half = halfWidth * (1 - amount);
  const side = (Math.max(Math.abs(x - centerX), Math.abs(z - centerZ)) - half) * 0.9;
  return Math.max(side, bottomY - y, y - bottomY - height);
}

// A pointed (gothic) arch opening on a plane: across is the coordinate along the wall, up is height.
function gothicArch(across, up, halfWidth, springY) {
  if (up < springY) return Math.max(Math.abs(across) - halfWidth, -up);
  const leftArc = Math.hypot(across + halfWidth * 0.6, up - springY) - halfWidth * 1.6;
  const rightArc = Math.hypot(across - halfWidth * 0.6, up - springY) - halfWidth * 1.6;
  return Math.max(leftArc, rightArc);
}

const GRAVES = [
  { x: 0.42, z: 0.42, lean: 0.12, kind: 'stone' }, { x: 0.62, z: 0.3, lean: -0.18, kind: 'cross' },
  { x: 0.25, z: 0.62, lean: 0.25, kind: 'stone' }, { x: 0.68, z: 0.58, lean: 0.05, kind: 'stone' },
  { x: 0.05, z: 0.72, lean: -0.22, kind: 'cross' }, { x: 0.48, z: 0.75, lean: 0.3, kind: 'stone' },
  { x: -0.2, z: 0.7, lean: 0.1, kind: 'stone' },
];
const GHOST_GRAVE = GRAVES[2];

function graveDistance(x, y, z, grave) {
  const cosine = Math.cos(grave.lean);
  const sine = Math.sin(grave.lean);
  const localX = x - grave.x;
  const localZ = z - grave.z;
  const tiltedX = localX * cosine - y * sine;
  const tiltedY = localX * sine + y * cosine;
  if (grave.kind === 'cross') {
    return Math.min(
      boxDistance(tiltedX, tiltedY, localZ, 0, 0.1, 0, 0.014, 0.11, 0.014),
      boxDistance(tiltedX, tiltedY, localZ, 0, 0.15, 0, 0.055, 0.014, 0.014));
  }
  const slab = boxDistance(tiltedX, tiltedY, localZ, 0, 0.07, 0, 0.055, 0.07, 0.018, 0.006);
  const top = Math.max(Math.hypot(tiltedX, tiltedY - 0.14) - 0.055, Math.abs(localZ) - 0.018);
  const mound = ellipsoidDistance(x, y, z, grave.x + 0.06, -0.02, grave.z + 0.08, 0.1, 0.035, 0.14);
  return Math.min(slab, top, mound);
}

export function buildMedieval(spacing) {
  const palette = ['#06060c', '#0e0e1a', '#181a2a', '#262a3e', '#3a3e54', '#5a5e74', '#8a8c9e', '#c4c4cc',
    '#1e2a22', '#34463a', '#56664e', '#3e2a26', '#ff9a3a', '#ffd88a', '#7ef2d0', '#c8fff0'].map(hex);
  const light = { sun: [-0.35, 0.6, 0.75], sunColor: [0.85, 0.92, 1.15], ambientColor: [0.42, 0.44, 0.6], rimColor: [0.45, 0.6, 0.9], shadowSoftness: 7 };
  const stone = hex('#6a6c7c');
  const stoneDark = hex('#44465a');
  const moss = hex('#4a5a46');

  const cragDistance = (x, y, z) => {
    const path = Math.abs(Math.hypot(x - 0.55, z - 0.5) - 0.3) < 0.05 ? 0.012 : 0;
    return islandDistance(x, y + path, z, 1.08, 1.25, 0, 0.11);
  };
  const chapelCenter = [0.12, 0.06];
  const chapelDistance = (x, y, z) => {
    const localX = x - chapelCenter[0];
    const localZ = z - chapelCenter[1];
    const outer = boxDistance(localX, y, localZ, 0, 0.25, 0, 0.32, 0.25, 0.19);
    const inner = boxDistance(localX, y, localZ, 0, 0.3, 0, 0.27, 0.32, 0.14);
    let walls = Math.max(outer, -inner);
    const gable = Math.max(boxDistance(localX, y, localZ, 0.295, 0.62, 0, 0.025, 0.14, 0.19), Math.abs(localZ) * 0.95 + (y - 0.5) - 0.17);
    walls = Math.min(walls, gable);
    const ruinTop = 0.4 + valueNoise(x * 9, 0, z * 9) * 0.16 + (localX < -0.05 ? -0.08 : 0);
    const isGableEnd = localX > 0.26;
    if (!isGableEnd) walls = Math.max(walls, y - ruinTop);
    const frontWindow = gothicArch(localZ, y - 0.3, 0.06, 0.38 - 0.3);
    const door = gothicArch(localZ, y - 0.0, 0.055, 0.16);
    const sideWindows = Math.min(gothicArch(localX - 0.12, y - 0.18, 0.04, 0.12), gothicArch(localX + 0.12, y - 0.18, 0.04, 0.12));
    if (localX > 0.2) walls = Math.max(walls, -Math.max(frontWindow, -(localX - 0.2)), -Math.max(door, -(localX - 0.2)));
    if (Math.abs(localZ) > 0.12) walls = Math.max(walls, -sideWindows);
    const buttresses = Math.min(
      boxDistance(localX, y, localZ, 0.12, 0.13, 0.21, 0.025, 0.13, 0.03),
      boxDistance(localX, y, localZ, -0.12, 0.13, 0.21, 0.025, 0.13, 0.03),
      boxDistance(localX, y, localZ, 0.12, 0.13, -0.21, 0.025, 0.13, 0.03));
    const rubble = sphereDistance(x, y, z, chapelCenter[0] - 0.36, 0.0, chapelCenter[1] + 0.22, 0.07) + (valueNoise(x * 30, y * 30, z * 30) - 0.5) * 0.04;
    return Math.min(walls, buttresses, rubble);
  };
  const towerCenter = [-0.32, -0.2];
  const towerDistance = (x, y, z) => {
    const localX = x - towerCenter[0];
    const localZ = z - towerCenter[1];
    let tower = boxDistance(localX, y, localZ, 0, 0.47, 0, 0.11, 0.47, 0.11);
    const hollow = boxDistance(localX, y, localZ, 0, 0.78, 0, 0.085, 0.12, 0.085);
    tower = Math.max(tower, -hollow);
    const belfryX = gothicArch(localZ, y - 0.68, 0.055, 0.1);
    const belfryZ = gothicArch(localX, y - 0.68, 0.055, 0.1);
    tower = Math.max(tower, -belfryX, -belfryZ);
    const slit = Math.max(Math.abs(localZ) - 0.012, Math.abs(y - 0.42) - 0.05);
    tower = Math.max(tower, -slit);
    const cornice = boxDistance(localX, y, localZ, 0, 0.95, 0, 0.13, 0.02, 0.13);
    const spire = pyramidDistance(x, y, z, towerCenter[0], 0.97, towerCenter[1], 0.12, 0.42);
    const finial = Math.min(
      capsuleDistance(x, y, z, towerCenter[0], 1.38, towerCenter[1], towerCenter[0], 1.5, towerCenter[1], 0.008),
      capsuleDistance(x, y, z, towerCenter[0] - 0.03, 1.46, towerCenter[1], towerCenter[0] + 0.03, 1.46, towerCenter[1], 0.008));
    return Math.min(tower, cornice, spire, finial);
  };
  const treeBranches = (() => {
    const branches = [];
    const grow = (startX, startY, startZ, angle, tilt, length, radius, depth) => {
      const endX = startX + Math.cos(angle) * Math.sin(tilt) * length;
      const endY = startY + Math.cos(tilt) * length;
      const endZ = startZ + Math.sin(angle) * Math.sin(tilt) * length;
      branches.push([startX, startY, startZ, endX, endY, endZ, radius]);
      if (depth === 0) return;
      for (let child = 0; child < 2; child++) {
        const random = hashNoise(depth * 7 + child, startX * 13, startZ * 11);
        grow(endX, endY, endZ, angle + (child ? 1 : -1) * (0.6 + random * 0.9), tilt + 0.25 + random * 0.35, length * 0.68, radius * 0.62, depth - 1);
      }
    };
    grow(0.66, 0, -0.42, 0.5, 0.18, 0.32, 0.032, 4);
    return branches;
  })();
  const treeDistance = (x, y, z) => {
    if (x < 0.2 || x > 1.15 || y > 1.1 || z < -0.95 || z > 0.1) return 0.2;
    let distance = Infinity;
    for (const [startX, startY, startZ, endX, endY, endZ, radius] of treeBranches) {
      distance = Math.min(distance, capsuleDistance(x, y, z, startX, startY, startZ, endX, endY, endZ, radius));
    }
    return distance;
  };
  const graveyardDistance = (x, y, z) => {
    let distance = Infinity;
    for (const grave of GRAVES) {
      if (Math.abs(x - grave.x) > 0.25 || Math.abs(z - grave.z) > 0.3) continue;
      distance = Math.min(distance, graveDistance(x, y, z, grave));
    }
    const post = capsuleDistance(x, y, z, 0.86, 0, 0.12, 0.86, 0.36, 0.12, 0.012);
    const arm = capsuleDistance(x, y, z, 0.86, 0.36, 0.12, 0.8, 0.36, 0.12, 0.008);
    const lantern = boxDistance(x, y, z, 0.8, 0.3, 0.12, 0.022, 0.03, 0.022, 0.004);
    return Math.min(distance, post, arm, lantern);
  };
  const sceneDistance = (x, y, z) => Math.min(cragDistance(x, y, z), chapelDistance(x, y, z), towerDistance(x, y, z), treeDistance(x, y, z), graveyardDistance(x, y, z));
  const shadowModel = { distance: sceneDistance };

  const crag = voxelizeModel({
    distance: cragDistance,
    bounds: [-1.15, -1.3, -1.15, 1.15, 0.08, 1.15],
    material: (x, y, z, normalX, normalY) => {
      const onPath = Math.abs(Math.hypot(x - 0.55, z - 0.5) - 0.3) < 0.05;
      if (y > -0.06 && normalY > 0.4) {
        if (onPath) return [...hex('#5a5048'), 0];
        const grass = valueNoise(x * 9, 2, z * 9);
        return [...(grass > 0.62 ? hex('#56664e') : grass > 0.3 ? hex('#3e4e3e') : hex('#2e3a30')), 0];
      }
      const strata = valueNoise(x * 3, y * 11, z * 3);
      return [...(strata > 0.6 ? hex('#5a5e74') : strata > 0.32 ? hex('#3a3e54') : hex('#262a3e')), 0];
    },
  }, spacing, light, { shadowModel });
  const stoneMaterial = (x, y, z) => {
    const brickRow = Math.floor(y / 0.035);
    const brickColumn = Math.floor((x + z + (brickRow % 2) * 0.03) / 0.06);
    const mortar = (y / 0.035) % 1 < 0.14;
    const tone = hashNoise(brickRow, brickColumn, 3.3);
    if (y < 0.12 && valueNoise(x * 18, y * 18, z * 18) > 0.55) return [...moss, 0];
    if (mortar) return [...stoneDark, 0];
    return [...(tone > 0.66 ? hex('#7c7e8e') : tone > 0.3 ? stone : hex('#585a6c')), 0];
  };
  const chapel = voxelizeModel({
    distance: chapelDistance,
    bounds: [-0.3, -0.02, -0.18, 0.5, 0.82, 0.3],
    material: stoneMaterial,
  }, spacing * 0.8, light, { shadowModel });
  const tower = voxelizeModel({
    distance: towerDistance,
    bounds: [-0.47, -0.02, -0.35, -0.17, 1.52, -0.05],
    material: (x, y, z) => (y > 0.97 ? [...(valueNoise(x * 40, y * 40, z * 40) > 0.5 ? hex('#3a3e54') : hex('#2a2c40')), 0] : stoneMaterial(x, y, z)),
  }, spacing * 0.8, light, { shadowModel });
  const tree = voxelizeModel({
    distance: treeDistance,
    bounds: [0.3, -0.02, -0.85, 1.1, 1.0, 0.05],
    material: (x, y, z) => [...(valueNoise(x * 30, y * 30, z * 30) > 0.5 ? hex('#3e2a26') : hex('#2a1e1e')), 0],
  }, spacing * 0.7, light, { shadowModel });
  const graveyard = voxelizeModel({
    distance: graveyardDistance,
    bounds: [-0.35, -0.06, -0.02, 0.95, 0.42, 0.95],
    material: (x, y, z) => {
      if (Math.abs(x - 0.8) < 0.03 && Math.abs(y - 0.3) < 0.035 && Math.abs(z - 0.12) < 0.03) return [...hex('#ffb24a'), 1];
      if (Math.abs(x - 0.86) < 0.02 && z > 0.08 && z < 0.16) return [...hex('#2a2a30'), 0];
      if (y < 0.0) return [...hex('#34302c'), 0];
      const lichen = valueNoise(x * 35, y * 35, z * 35);
      return [...(lichen > 0.68 ? moss : lichen > 0.3 ? hex('#7a7c8a') : hex('#5c5e6e')), 0];
    },
  }, spacing * 0.65, light, { shadowModel });

  // Interior glow: candles behind the front window and door, drawn as emissive splats inside the nave.
  const candlePoints = [];
  for (let candle = 0; candle < 9; candle++) {
    const candleX = chapelCenter[0] + 0.05 + (candle % 3) * 0.06;
    const candleZ = chapelCenter[1] - 0.08 + Math.floor(candle / 3) * 0.08;
    for (let piece = 0; piece < 4; piece++) candlePoints.push({ x: candleX, y: 0.02 + piece * 0.012, z: candleZ, color: hex('#e8e0d0'), scale: 0.008, candle: -1 });
    candlePoints.push({ x: candleX, y: 0.075, z: candleZ, color: hex('#ffd88a'), scale: 0.01, candle });
  }

  const monk = voxelizeModel({
    distance: (x, y, z) => {
      const robe = taperedCylinderDistance(x, y, z, 0, 0, 0, 0.065, 0.035, 0.2);
      const hood = Math.min(sphereDistance(x, y, z, 0, 0.23, 0, 0.045), taperedCylinderDistance(x, y, z, -0.012, 0.23, 0, 0.04, 0.0, 0.07));
      const arm = capsuleDistance(x, y, z, 0.0, 0.17, 0.035, 0.06, 0.12, 0.05, 0.016);
      const staff = capsuleDistance(x, y, z, 0.05, 0.0, -0.05, 0.05, 0.3, -0.05, 0.007);
      return Math.min(robe, hood, arm, staff);
    },
    bounds: [-0.08, -0.02, -0.08, 0.1, 0.32, 0.08],
    material: (x, y, z) => {
      if (Math.abs(x - 0.05) < 0.012 && z < -0.04) return [...hex('#3e2a26'), 0];
      if (y > 0.2 && x > 0.025 && Math.abs(z) < 0.025) return [...hex('#06060c'), 0];
      return [...(y < 0.03 ? hex('#3a3448') : hex('#4e4660')), 0];
    },
  }, spacing * 0.5, light);
  const monkPlace = time => {
    const step = stepAndHold(time, 3.4, 0.62);
    const angle = step.progress * 0.75 + 2.4;
    const x = 0.55 + Math.cos(angle) * 0.3;
    const z = 0.5 + Math.sin(angle) * 0.3;
    const lookAround = step.moving ? 0 : Math.sin((time % 3.4) * 2.2) * 0.5 * Math.sin(Math.PI * Math.min(((time % 3.4) - 3.4 * 0.62) / (3.4 * 0.38), 1));
    return { x, z, heading: -angle + Math.PI / 2 + Math.PI + lookAround, angle, moving: step.moving };
  };
  const monkLantern = time => {
    const place = monkPlace(time);
    const sway = (place.moving ? Math.sin(time * 5.2) * 0.012 : Math.sin(time * 1.4) * 0.005);
    const cosine = Math.cos(place.heading);
    const sine = Math.sin(place.heading);
    const localX = (0.075 + sway) * 1.6;
    const localZ = 0.055 * 1.6;
    return [place.x + localX * cosine + localZ * sine, 0.16 + Math.abs(Math.sin(time * 2.6)) * 0.01, place.z - localX * sine + localZ * cosine];
  };

  const bell = voxelizeModel({
    distance: (x, y, z) => Math.max(taperedCylinderDistance(x, y, z, 0, -0.07, 0, 0.05, 0.028, 0.07), -taperedCylinderDistance(x, y, z, 0, -0.08, 0, 0.04, 0.018, 0.065)),
    bounds: [-0.06, -0.08, -0.06, 0.06, 0.01, 0.06],
    material: () => [...hex('#8a6a3a'), 0.25],
  }, spacing * 0.5, light);

  const crowPoints = (phase, flap) => {
    const points = [];
    for (let body = 0; body < 5; body++) points.push([body * 0.012 - 0.024, 0, 0, 0.011]);
    points.push([0.034, 0.004, 0, 0.008]);
    for (let side = -1; side <= 1; side += 2) {
      for (let feather = 1; feather <= 5; feather++) {
        const reach = feather * 0.014;
        points.push([-0.004 - feather * 0.002, Math.sin(flap) * reach * 0.9, side * Math.cos(flap) * reach, 0.008]);
      }
    }
    return points;
  };

  const ashCount = 160;
  const emberCount = 12;
  return {
    name: 'medieval',
    mist: { color: hex('#8a92b0'), alpha: 0.03, low: -0.25, high: 0.15, wispColor: hex('#7ef2d0'), wispHeight: 0.32, trails: true },
    haze: { color: hex('#1a1c2e'), lift: 0.15, bloom: 0.85, bloomThreshold: 0.58, soften: 0.3, mistTop: 0.6, mistStrength: 0.1, vignette: 1.1 },
    paletteExtra: ['#4e5672', '#7a84a2', '#a8b0c8', '#2a4a44', '#4e8a7a', '#ffbe66'],
    palette,
    background: { inner: hex('#20243c'), outer: hex('#04040a'), stars: true, moon: { x: 0.84, y: 0.13, radius: 0.045, color: hex('#cdd6e4'), halo: hex('#5a6a96') }, clouds: hex('#2a2e46') },
    camera: { target: [0.05, 0.5, 0.1], distance: 4.4, height: 1.25, startAngle: 0.35 },
    staticLists: [crag, chapel, tower, tree, graveyard],
    dynamic(time) {
      const lists = [];
      const candleList = makeList(candlePoints.map(point => point.candle < 0 ? point : {
        ...point, y: point.y + Math.sin(time * 13 + point.candle) * 0.003, scale: point.scale * (0.85 + 0.3 * hashNoise(Math.floor(time * 12), point.candle, 1)),
      }));
      lists.push(candleList);
      const place = monkPlace(time);
      lists.push(placeSplats(monk, { x: place.x, y: -0.005 + (place.moving ? Math.abs(Math.sin(time * 5.2)) * 0.008 : 0), z: place.z, heading: place.heading, scale: 1.6 }));
      // Two red eyes inside the hood.
      const eyes = [];
      for (const side of [-1, 1]) {
        const localX = 0.036 * 1.6;
        const localZ = side * 0.012 * 1.6;
        const cosine = Math.cos(place.heading);
        const sine = Math.sin(place.heading);
        eyes.push({ x: place.x + localX * cosine + localZ * sine, y: 0.232 * 1.6, z: place.z - localX * sine + localZ * cosine, color: hex('#ff2a1a'), scale: 0.0075 });
      }
      // Something watches from the belfry: eye pairs that blink and sometimes go dark.
      for (const [faceX, faceZ, seed] of [[0.1, 0, 1], [0, 0.1, 2], [-0.1, 0, 3]]) {
        const open = Math.sin(time * 0.8 + seed * 2.1) > -0.3 && (time * 3 + seed) % 2.7 > 0.12;
        if (!open) continue;
        for (const side of [-1, 1]) {
          eyes.push({
            x: towerCenter[0] + faceX * 0.6 + (faceZ ? side * 0.018 : 0), y: 0.735 + wobble(time, seed) * 0.004,
            z: towerCenter[1] + faceZ * 0.6 + (faceX ? side * 0.018 : 0), color: hex('#ff3a20'), scale: 0.007,
          });
        }
      }
      lists.push(makeList(eyes));
      const lantern = monkLantern(time);
      lists.push(makeList([{ x: lantern[0], y: lantern[1], z: lantern[2], color: hex('#ffd88a'), scale: 0.02 }]));
      const swing = struckSwing(time, 4.5, 0.55, 3.4, 0.55, 1.2);
      lists.push(placeSplats(bell, {
        x: towerCenter[0], y: 0.84, z: towerCenter[1], heading: 0,
        deform: (x, y, z) => [x * Math.cos(swing) - y * Math.sin(swing), x * Math.sin(swing) + y * Math.cos(swing), z],
      }));
      // Crows circling the spire.
      const crows = [];
      for (let crow = 0; crow < 6; crow++) {
        const phase = crow * 1.13;
        const angle = time * (0.45 + crow * 0.04) + phase + Math.sin(time * 0.6 + phase) * 0.6;
        const radius = 0.22 + crow * 0.05;
        const centerX = towerCenter[0] + Math.cos(angle) * radius;
        const centerZ = towerCenter[1] + Math.sin(angle) * radius;
        const dive = Math.pow(Math.max(0, Math.sin(time * 0.45 + phase * 2)), 8) * 0.35;
        const centerY = 1.05 + wobble(time * 0.6, phase) * 0.08 + crow * 0.05 - dive;
        const heading = -angle - Math.PI / 2;
        const gliding = Math.sin(time * 0.9 + phase * 3) > 0.25 || dive > 0.05;
        const flap = gliding ? 0.35 + Math.sin(time * 2 + phase) * 0.05 : Math.sin(time * 11 + phase * 5) * 0.95;
        for (const [localX, localY, localZ, scale] of crowPoints(phase, flap)) {
          crows.push({
            x: centerX + (localX * Math.cos(heading) + localZ * Math.sin(heading)) * 2.3,
            y: centerY + localY * 2.3,
            z: centerZ + (-localX * Math.sin(heading) + localZ * Math.cos(heading)) * 2.3,
            color: hex('#141420'), scale: scale * 2,
          });
        }
      }
      lists.push(makeList(crows));
      // A ghost rising out of a grave, swaying, then thinning out.
      const ghostAge = ((time - 3.5) % 11) / 4.5;
      if (ghostAge > 0 && ghostAge < 1) {
        const ghost = [];
        const rise = easeOutCubic(ghostAge * 2.2) * 0.3 + easeInOutCubic((ghostAge - 0.5) * 2) * 0.35;
        const strength = Math.sin(Math.min(ghostAge, 1) * Math.PI);
        const baseX = GHOST_GRAVE.x + 0.06;
        const baseZ = GHOST_GRAVE.z + 0.06;
        const sway = height => Math.sin(time * 2.2 - height * 12) * 0.035 * (1 - height / 0.36);
        for (let index = 0; index < 420; index++) {
          const pick = hashNoise(index, 9.1, 0.3);
          const around = hashNoise(index, 3.3, 4.4) * Math.PI * 2;
          const radial = Math.sqrt(hashNoise(index, 5.5, 6.6));
          let x;
          let y;
          let z;
          let tone = hex('#7ef2d0');
          if (pick < 0.18) {
            x = baseX + Math.cos(around) * 0.034 * radial;
            y = rise + 0.32 + Math.sin(around * 1.7) * 0.034 * radial;
            z = baseZ + Math.sin(around) * 0.034 * radial;
            tone = hex('#c8fff0');
          } else if (pick < 0.36) {
            const side = pick < 0.27 ? -1 : 1;
            const along = hashNoise(index, 7.7, 8.8);
            // Arms reach forward toward the viewer and droop into long claws.
            x = baseX + side * (0.028 + along * 0.035) + Math.sin(time * 3 + side) * 0.008 * along;
            y = rise + 0.27 - along * along * 0.06 + Math.sin(time * 2.4 + along * 4) * 0.01;
            z = baseZ + along * 0.11 + (hashNoise(index, 1, 9) - 0.5) * 0.012;
          } else {
            const height = hashNoise(index, 1.1, 2.2) * 0.3;
            const width = 0.006 + (height / 0.3) ** 0.7 * 0.045;
            x = baseX + Math.cos(around) * width * radial + sway(height);
            y = rise - 0.04 + height;
            z = baseZ + Math.sin(around) * width * radial * 0.8;
            if (height < 0.08) tone = hex('#4e8a7a');
          }
          ghost.push({ x, y, z, color: tone, alpha: 0.3 * strength, scale: 0.011 });
        }
        // Hollow eyes and a long gaping mouth.
        const face = [[-0.013, 0.33, 0.012], [0.013, 0.33, 0.012], [0, 0.302, 0.011], [0, 0.29, 0.012], [0, 0.278, 0.01]];
        for (const [offsetX, offsetY, size] of face) {
          ghost.push({ x: baseX + offsetX, y: rise + offsetY, z: baseZ + 0.03, color: hex('#020406'), alpha: 0.95 * strength, scale: size });
        }
        lists.push(makeList(ghost));
      }
      // Ash falling through the scene and embers rising from the monk's lantern.
      const ash = [];
      for (let flake = 0; flake < ashCount; flake++) {
        const fall = (time * (0.05 + hashNoise(flake, 1, 1) * 0.05) + hashNoise(flake, 2, 2)) % 1;
        const angle = hashNoise(flake, 3, 3) * Math.PI * 2;
        const radius = Math.sqrt(hashNoise(flake, 4, 4)) * 1.5;
        ash.push({
          x: Math.cos(angle) * radius + Math.sin(time * 0.6 + flake) * 0.05,
          y: 1.7 - fall * 2.2,
          z: Math.sin(angle) * radius + Math.cos(time * 0.5 + flake) * 0.05,
          color: hex('#c8b4a0'), alpha: 0.6 * Math.min(fall * 6, 1) * Math.min((1 - fall) * 6, 1), scale: 0.01,
        });
      }
      for (let ember = 0; ember < emberCount; ember++) {
        const age = (time * 0.6 + ember / emberCount) % 1;
        const origin = monkLantern(time - age / 0.6);
        ash.push({
          x: origin[0] + Math.sin(ember * 2 + age * 6) * 0.03 * age,
          y: origin[1] + age * 0.35,
          z: origin[2] + Math.cos(ember * 3 + age * 5) * 0.03 * age,
          color: hex('#ff9a3a'), alpha: 0.9 * (1 - age), scale: 0.006,
        });
      }
      lists.push(makeList(ash));
      return lists;
    },
    glows(time) {
      const lantern = monkLantern(time);
      const flicker = 0.85 + 0.15 * hashNoise(Math.floor(time * 10), 1, 1);
      const glows = [
        { position: lantern, color: hex('#ffb24a'), radius: 0.24, strength: 0.55 * flicker },
        { position: [0.8, 0.3, 0.12], color: hex('#ffb24a'), radius: 0.2, strength: 0.42 * flicker },
        { position: [chapelCenter[0] + 0.3, 0.3, chapelCenter[1]], color: hex('#ff9a3a'), radius: 0.34, strength: 0.36 * flicker },
        { position: [chapelCenter[0] + 0.3, 0.08, chapelCenter[1]], color: hex('#ff9a3a'), radius: 0.3, strength: 0.42 * flicker },
      ];
      const ghostAge = ((time - 3.5) % 11) / 4.5;
      if (ghostAge > 0 && ghostAge < 1) {
        const rise = easeOutCubic(ghostAge * 2.2) * 0.3 + easeInOutCubic((ghostAge - 0.5) * 2) * 0.35;
        glows.push({ position: [GHOST_GRAVE.x + 0.06, rise + 0.25, GHOST_GRAVE.z + 0.06], color: hex('#7ef2d0'), radius: 0.26, strength: 0.25 * Math.sin(ghostAge * Math.PI) });
      }
      return glows;
    },
    contactShadows(time) {
      const place = monkPlace(time);
      return [{ x: place.x, z: place.z, radius: 0.09, strength: 0.4 }];
    },
  };
}
