// Three original pixel-art splat dioramas. Each scene builds its static splats once and adds moving splats per frame.
import { buildMedieval } from './medieval.js';
import { buildSwamp, buildGallows } from './medieval2.js';
import {
  hashNoise, valueNoise, sphereDistance, ellipsoidDistance, boxDistance, cylinderDistance, taperedCylinderDistance,
  capsuleDistance, smoothUnion, islandDistance, voxelizeModel, placeSplats,
} from './voxel-splats.js';

const hex = value => [parseInt(value.slice(1, 3), 16) / 255, parseInt(value.slice(3, 5), 16) / 255, parseInt(value.slice(5, 7), 16) / 255];

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

// ---------------------------------------------------------------------------------------------------------------
// Lighthouse on a rock in a disc of night sea.
// ---------------------------------------------------------------------------------------------------------------
function buildLighthouse(spacing) {
  const palette = ['#070a14', '#0f1528', '#1a2544', '#263a66', '#36578a', '#5684b0', '#9cc8dc', '#e6f2ee',
    '#2a2430', '#4a3e48', '#76666e', '#7a2230', '#c23a44', '#f2c75c', '#fff2c0', '#e07a34'].map(hex);
  const colors = {
    rockDark: hex('#3a3040'), rock: hex('#5a4c58'), rockLight: hex('#86727c'), white: hex('#e8eef0'), red: hex('#c23a44'),
    darkMetal: hex('#262636'), lamp: hex('#fff2c0'), roof: hex('#8a2634'), wall: hex('#d8d0c8'), wood: hex('#6a4a3a'),
    seaBody: hex('#1a2a52'), window: hex('#f2c75c'),
  };
  const light = { sun: [-0.5, 0.8, 0.45], sunColor: [0.75, 0.82, 1.0], ambientColor: [0.32, 0.38, 0.58], rimColor: [0.3, 0.45, 0.8], shadowSoftness: 6 };
  const rockDistance = (x, y, z) => {
    const mound = ellipsoidDistance(x, y, z, 0.05, -0.15, 0.0, 0.62, 0.5, 0.52);
    const ledge = ellipsoidDistance(x, y, z, 0.45, -0.12, 0.35, 0.32, 0.26, 0.3);
    const noise = (valueNoise(x * 7, y * 7, z * 7) - 0.5) * 0.09 + (valueNoise(x * 19, y * 19, z * 19) - 0.5) * 0.03;
    return Math.max(smoothUnion(mound, ledge, 0.12) + noise, -y - 0.45);
  };
  const towerDistance = (x, y, z) => {
    const tower = taperedCylinderDistance(x, y, z, -0.05, 0.2, -0.02, 0.17, 0.115, 0.95);
    const gallery = cylinderDistance(x, y, z, -0.05, 1.13, -0.02, 0.16, 0.035);
    const lampRoom = cylinderDistance(x, y, z, -0.05, 1.165, -0.02, 0.085, 0.13);
    const roof = taperedCylinderDistance(x, y, z, -0.05, 1.29, -0.02, 0.12, 0.0, 0.13);
    const ball = sphereDistance(x, y, z, -0.05, 1.43, -0.02, 0.025);
    return Math.min(tower, gallery, lampRoom, roof, ball);
  };
  const cottageDistance = (x, y, z) => {
    const walls = boxDistance(x, y, z, 0.38, 0.27, 0.22, 0.13, 0.09, 0.1, 0.01);
    const roofLocalY = y - 0.36;
    const roof = Math.max(boxDistance(x, y, z, 0.38, 0.42, 0.22, 0.155, 0.08, 0.12), Math.abs(z - 0.22) * 0.8 + roofLocalY * 1.0 - 0.1);
    const chimney = boxDistance(x, y, z, 0.46, 0.47, 0.17, 0.022, 0.06, 0.022);
    return Math.min(walls, Math.max(roof, -roofLocalY), chimney);
  };
  const seaBodyDistance = (x, y, z) => cylinderDistance(x, y, z, 0, -0.42, 0, 1.25, 0.4);
  const sceneDistance = (x, y, z) => Math.min(rockDistance(x, y, z), towerDistance(x, y, z), cottageDistance(x, y, z));

  const rockModel = {
    distance: rockDistance,
    bounds: [-0.75, -0.46, -0.65, 0.85, 0.42, 0.75],
    material: (x, y, z, normalX, normalY) => {
      if (normalY > 0.75 && y > 0.12) return [...hex('#3f5a3a'), 0];
      const band = valueNoise(x * 3, y * 14, z * 3);
      return band > 0.62 ? [...colors.rockLight, 0] : band > 0.35 ? [...colors.rock, 0] : [...colors.rockDark, 0];
    },
  };
  const towerModel = {
    distance: towerDistance,
    bounds: [-0.27, 0.15, -0.24, 0.17, 1.48, 0.2],
    material: (x, y, z) => {
      if (y > 1.43 - 0.03 && y < 1.47) return [...colors.darkMetal, 0];
      if (y > 1.29) return [...colors.roof, 0];
      if (y > 1.165) {
        const radial = Math.hypot(x + 0.05, z + 0.02);
        if (radial < 0.095) {
          const mullion = Math.abs(Math.sin(Math.atan2(z + 0.02, x + 0.05) * 4)) < 0.2;
          return mullion ? [...colors.darkMetal, 0] : [...colors.lamp, 1];
        }
        return [...colors.darkMetal, 0];
      }
      if (y > 1.12) return [...colors.darkMetal, 0];
      const doorway = y < 0.38 && Math.abs(x + 0.05 - 0.0) < 0.05 && z > 0.05;
      if (doorway) return [...colors.wood, 0];
      const windowSpot = Math.abs(y - 0.72) < 0.04 && Math.abs(x + 0.05) < 0.03 && z > 0.05;
      if (windowSpot) return [...colors.window, 0.8];
      const band = Math.floor((y - 0.2) / 0.19) % 2 === 0;
      return band ? [...colors.white, 0] : [...colors.red, 0];
    },
  };
  const cottageModel = {
    distance: cottageDistance,
    bounds: [0.2, 0.15, 0.06, 0.56, 0.56, 0.38],
    material: (x, y, z) => {
      if (y > 0.36 && !(Math.abs(x - 0.46) < 0.03 && Math.abs(z - 0.17) < 0.03)) return [...colors.roof, 0];
      if (y > 0.36) return [...colors.rock, 0];
      const windowSpot = Math.abs(y - 0.28) < 0.03 && Math.abs(x - 0.33) < 0.03 && z > 0.3;
      if (windowSpot) return [...colors.window, 1];
      return [...colors.wall, 0];
    },
  };
  const seaBodyModel = {
    distance: seaBodyDistance,
    bounds: [-1.28, -0.45, -1.28, 1.28, 0.0, 1.28],
    material: (x, y) => {
      const depth = -y;
      if (depth > 0.4) return [...hex('#0f1528'), 0];
      return depth > 0.22 ? [...hex('#1a2544'), 0.25] : [...hex('#263a66'), 0.25];
    },
  };
  const shadowModel = { distance: sceneDistance };
  const staticLists = [rockModel, towerModel, cottageModel].map(model => voxelizeModel(model, spacing, light, { shadowModel }));
  const seaWall = voxelizeModel(seaBodyModel, spacing * 1.4, light, { shadowModel: { distance: seaBodyDistance } });
  // Keep only the side wall and floor of the sea body; the top is the moving water.
  const wallKeep = [];
  for (let index = 0; index < seaWall.count; index++) if (seaWall.positions[index * 3 + 1] < -0.04) wallKeep.push(index);
  staticLists.push(subsetList(seaWall, wallKeep));

  const boat = voxelizeModel({
    distance: (x, y, z) => {
      const hull = Math.max(ellipsoidDistance(x, y, z, 0, 0, 0, 0.17, 0.08, 0.07), y - 0.02, -(y + 0.06));
      const mast = capsuleDistance(x, y, z, 0.01, 0, 0, 0.01, 0.24, 0, 0.008);
      const sail = Math.max(boxDistance(x, y, z, -0.04, 0.13, 0, 0.05, 0.09, 0.006), x - 0.0 - (0.22 - y) * 0.4);
      return Math.min(hull, mast, sail);
    },
    bounds: [-0.2, -0.08, -0.1, 0.2, 0.27, 0.1],
    material: (x, y) => (y > 0.025 ? [...colors.wall, 0] : [...hex('#8a4a32'), 0]),
  }, spacing * 0.8, light);

  const waterSpacing = spacing * 1.35;
  const waterGrid = [];
  for (let x = -1.24; x <= 1.24; x += waterSpacing) {
    for (let z = -1.24; z <= 1.24; z += waterSpacing) {
      if (Math.hypot(x, z) > 1.24) continue;
      if (rockDistance(x, 0, z) < -0.02) continue;
      waterGrid.push([x + (hashNoise(x * 9, 1, z * 9) - 0.5) * waterSpacing * 0.4, z + (hashNoise(x * 9, 2, z * 9) - 0.5) * waterSpacing * 0.4]);
    }
  }
  const lampPosition = [-0.05, 1.23, -0.02];
  const boatPath = time => ({ x: 0.72 + Math.sin(time * 0.3) * 0.05, z: -0.42, heading: 0.6 + Math.sin(time * 0.5) * 0.08 });
  const waveHeight = (x, z, time) => 0.022 * Math.sin(x * 5.5 + time * 1.6) + 0.016 * Math.sin(z * 7.1 - time * 1.2 + x * 2) + 0.008 * Math.sin((x + z) * 13 + time * 2.4);

  return {
    name: 'lighthouse',
    mist: { color: hex('#7f9db4'), alpha: 0.05, low: -0.08, high: 0.3, wispColor: hex('#c8f0ff'), wispHeight: 0.35 },
    haze: { color: hex('#22314c'), lift: 0.14, bloom: 0.8, bloomThreshold: 0.45, soften: 0.35, mistTop: 0.55, mistStrength: 0.22, vignette: 1.1 },
    paletteExtra: ['#3a4c6a', '#5a7290', '#8aa4bc', '#b4cad8'],
    palette,
    background: { inner: hex('#1a2448'), outer: hex('#05070f'), stars: true },
    camera: { target: [0, 0.45, 0], distance: 5.3, height: 1.7, startAngle: 0.5 },
    staticLists,
    dynamic(time) {
      const lists = [];
      const waterPoints = waterGrid.map(([x, z]) => {
        const height = waveHeight(x, z, time);
        const shoreDistance = rockDistance(x, 0.0, z);
        const foam = height > 0.025 || shoreDistance < 0.07 + 0.03 * Math.sin(time * 2 + x * 8) || Math.hypot(x, z) > 1.2;
        const lampSide = Math.max(0, Math.cos(Math.atan2(z - lampPosition[2], x - lampPosition[0]) - time * 0.9)) ** 24;
        const base = foam ? hex('#9cc8dc') : height > 0.008 ? hex('#36578a') : hex('#263a66');
        const color = base.map((value, channel) => value + lampSide * [0.45, 0.35, 0.1][channel] * (1 - Math.min(Math.hypot(x, z) / 1.3, 1)));
        return { x, y: height - 0.01, z, color, scale: waterSpacing * 0.68 };
      });
      lists.push(makeList(waterPoints));
      const boatPlace = boatPath(time);
      lists.push(placeSplats(boat, { x: boatPlace.x, y: waveHeight(boatPlace.x, boatPlace.z, time) + 0.02, z: boatPlace.z, heading: boatPlace.heading,
        deform: (x, y, z) => [x, y + x * 0.25 * Math.sin(time * 1.6 + 0.8), z] }));
      // Two beams turning around the lamp.
      const beamPoints = [];
      for (let beam = 0; beam < 2; beam++) {
        const angle = time * 0.9 + beam * Math.PI;
        for (let step = 0; step < 70; step++) {
          const along = 0.12 + step * 0.03;
          const width = 0.02 + along * 0.11;
          for (let across = 0; across < 3; across++) {
            const sideways = (across - 1) * width * 0.8 + (hashNoise(step, across, beam) - 0.5) * width * 0.5;
            const x = lampPosition[0] + Math.cos(angle) * along - Math.sin(angle) * sideways;
            const z = lampPosition[2] + Math.sin(angle) * along + Math.cos(angle) * sideways;
            const y = lampPosition[1] - along * 0.04 + (hashNoise(step, across, beam + 7) - 0.5) * width * 0.6;
            beamPoints.push({ x, y, z, color: hex('#fff2c0'), alpha: 0.075 * (1 - along / 2.2) * Math.min(along / 0.3, 1), scale: width * 0.6 });
          }
        }
      }
      lists.push(makeList(beamPoints));
      return lists;
    },
    glows(time) {
      return [
        { position: lampPosition, color: hex('#ffd878'), radius: 0.55, strength: 0.65 },
        { position: [0.33, 0.28, 0.33], color: hex('#f2a85c'), radius: 0.16, strength: 0.4 },
      ];
    },
    contactShadows() {
      return [];
    },
  };
}

// ---------------------------------------------------------------------------------------------------------------
// A snail carrying a tiny house across a floating meadow at dusk.
// ---------------------------------------------------------------------------------------------------------------
function buildSnail(spacing) {
  const palette = ['#140f1e', '#251a34', '#3a2a4a', '#2f4a34', '#4f7a3c', '#8cba52', '#d8e88a', '#5e3e2e',
    '#94603c', '#d29a5e', '#a8503a', '#e8d6b0', '#c2607e', '#f4ece0', '#7e6e94', '#ffcc66'].map(hex);
  const light = { sun: [0.6, 0.55, 0.4], sunColor: [1.15, 0.9, 0.68], ambientColor: [0.58, 0.5, 0.7], rimColor: [0.6, 0.35, 0.5], shadowSoftness: 6 };
  const meadowDistance = (x, y, z) => {
    const tuft = (valueNoise(x * 11, 0, z * 11) - 0.6) * 0.07;
    return islandDistance(x, y - Math.max(tuft, 0), z, 1.02, 0.95, 0, 0.08);
  };
  const decorDistance = (x, y, z) => {
    let distance = Infinity;
    for (const [mushroomX, mushroomZ, size] of [[-0.55, 0.35, 1], [-0.45, 0.5, 0.7], [0.55, -0.55, 0.85]]) {
      const stem = capsuleDistance(x, y, z, mushroomX, 0, mushroomZ, mushroomX, 0.14 * size, mushroomZ, 0.035 * size);
      const cap = Math.max(ellipsoidDistance(x, y, z, mushroomX, 0.15 * size, mushroomZ, 0.11 * size, 0.08 * size, 0.11 * size), -(y - 0.13 * size));
      distance = Math.min(distance, stem, cap);
    }
    const stone = ellipsoidDistance(x, y, z, 0.35, 0.02, 0.62, 0.13, 0.09, 0.1) + (valueNoise(x * 20, y * 20, z * 20) - 0.5) * 0.02;
    distance = Math.min(distance, stone);
    for (let flower = 0; flower < 9; flower++) {
      const angle = flower * 2.39;
      const radius = 0.25 + (flower % 4) * 0.17;
      const flowerX = Math.cos(angle) * radius;
      const flowerZ = Math.sin(angle) * radius;
      const stem = capsuleDistance(x, y, z, flowerX, 0, flowerZ, flowerX, 0.07, flowerZ, 0.008);
      const head = sphereDistance(x, y, z, flowerX, 0.08, flowerZ, 0.022);
      distance = Math.min(distance, stem, head);
    }
    return distance;
  };
  const sceneDistance = (x, y, z) => Math.min(meadowDistance(x, y, z), decorDistance(x, y, z));
  const meadow = voxelizeModel({
    distance: meadowDistance,
    bounds: [-1.08, -0.98, -1.08, 1.08, 0.1, 1.08],
    material: (x, y, z, normalX, normalY) => {
      if (y > -0.05 && normalY > 0.35) {
        const shade = valueNoise(x * 8, 3, z * 8);
        return [...(shade > 0.6 ? hex('#8cba52') : shade > 0.3 ? hex('#5f9a44') : hex('#4f7a3c')), 0];
      }
      if (y > -0.12) return [...hex('#4f7a3c'), 0];
      const strata = valueNoise(x * 2, y * 9, z * 2);
      return [...(strata > 0.55 ? hex('#94603c') : strata > 0.3 ? hex('#6e4a34') : hex('#4e3628')), 0];
    },
  }, spacing, light, { shadowModel: { distance: sceneDistance } });
  const decor = voxelizeModel({
    distance: decorDistance,
    bounds: [-0.7, -0.02, -0.75, 0.75, 0.24, 0.75],
    material: (x, y, z) => {
      if (Math.hypot(x - 0.35, z - 0.62) < 0.16 && y < 0.12) return [...hex('#7e6e94'), 0];
      for (let flower = 0; flower < 9; flower++) {
        const angle = flower * 2.39;
        const radius = 0.25 + (flower % 4) * 0.17;
        if (Math.hypot(x - Math.cos(angle) * radius, z - Math.sin(angle) * radius) < 0.03) {
          if (y > 0.06) return [...(flower % 3 === 0 ? hex('#f4ece0') : flower % 3 === 1 ? hex('#ffcc66') : hex('#c2607e')), 0];
          return [...hex('#4f7a3c'), 0];
        }
      }
      if (y > 0.1 * 0.7 && valueNoise(x * 40, y * 40, z * 40) > 0.72) return [...hex('#f4ece0'), 0];
      if (y > 0.09) return [...hex('#c2607e'), 0];
      return [...hex('#e8d6b0'), 0];
    },
  }, spacing * 0.8, light, { shadowModel: { distance: sceneDistance } });

  // The snail, built facing +x around its own origin on the ground.
  const shellCenter = [-0.04, 0.2, 0];
  const snailDistance = (x, y, z) => {
    const foot = smoothUnion(
      ellipsoidDistance(x, y, z, 0.02, 0.04, 0, 0.3, 0.05, 0.08),
      capsuleDistance(x, y, z, 0.18, 0.05, 0, 0.27, 0.14, 0, 0.055), 0.05);
    const eyeLeft = capsuleDistance(x, y, z, 0.27, 0.16, 0.025, 0.3, 0.27, 0.05, 0.011);
    const eyeRight = capsuleDistance(x, y, z, 0.27, 0.16, -0.025, 0.31, 0.26, -0.05, 0.011);
    const eyeBallLeft = sphereDistance(x, y, z, 0.3, 0.275, 0.05, 0.022);
    const eyeBallRight = sphereDistance(x, y, z, 0.31, 0.265, -0.05, 0.022);
    const shell = ellipsoidDistance(x, y, z, shellCenter[0], shellCenter[1], shellCenter[2], 0.17, 0.16, 0.12);
    const houseWalls = boxDistance(x, y, z, -0.04, 0.39, 0, 0.065, 0.05, 0.05, 0.006);
    const roof = Math.max(boxDistance(x, y, z, -0.04, 0.47, 0, 0.08, 0.045, 0.065), Math.abs(z) * 0.9 + (y - 0.44) - 0.055, -(y - 0.44));
    const chimney = boxDistance(x, y, z, 0.0, 0.5, -0.025, 0.012, 0.035, 0.012);
    return Math.min(foot, eyeLeft, eyeRight, eyeBallLeft, eyeBallRight, shell, houseWalls, roof, chimney);
  };
  const snail = voxelizeModel({
    distance: snailDistance,
    bounds: [-0.3, -0.02, -0.16, 0.36, 0.56, 0.16],
    material: (x, y, z) => {
      const shellDistance = ellipsoidDistance(x, y, z, shellCenter[0], shellCenter[1], shellCenter[2], 0.17, 0.16, 0.12);
      if (y > 0.335) {
        if (y > 0.44 && !(Math.abs(x) < 0.02 && z < -0.01 && y > 0.46)) return [...hex('#a8503a'), 0];
        if (y > 0.44) return [...hex('#5e3e2e'), 0];
        const windowSpot = Math.abs(y - 0.395) < 0.018 && Math.abs(x + 0.04) < 0.02 && Math.abs(z) > 0.04;
        if (windowSpot) return [...hex('#ffcc66'), 1];
        const doorSpot = x > 0.02 && Math.abs(z) < 0.02 && y < 0.41;
        if (doorSpot) return [...hex('#5e3e2e'), 0];
        return [...hex('#e8d6b0'), 0];
      }
      if (shellDistance < 0.02) {
        const spiral = Math.atan2(y - shellCenter[1], x - shellCenter[0]) + Math.hypot(x - shellCenter[0], y - shellCenter[1]) * 26;
        const stripe = Math.sin(spiral);
        return [...(stripe > 0.45 ? hex('#d29a5e') : stripe > -0.3 ? hex('#a8503a') : hex('#5e3e2e')), 0];
      }
      if (y > 0.25) return [...hex('#2a1e2a'), 0];
      return [...hex('#c8b4a0'), 0];
    },
  }, spacing * 0.75, light);

  const snailScale = 1.55;
  const pathRadius = 0.45;
  const snailPlace = time => {
    const angle = -time * 0.16 + 0.6;
    return { x: Math.cos(angle) * pathRadius, z: Math.sin(angle) * pathRadius, heading: angle + Math.PI };
  };
  const chimneyWorld = time => {
    const place = snailPlace(time);
    const cosine = Math.cos(place.heading);
    const sine = Math.sin(place.heading);
    const localX = 0.0;
    const localZ = -0.025;
    return [place.x + (localX * cosine + localZ * sine) * snailScale, 0.53 * snailScale, place.z + (-localX * sine + localZ * cosine) * snailScale];
  };
  return {
    name: 'snail',
    mist: { color: hex('#c4aed4'), alpha: 0.045, low: -0.1, high: 0.25, wispColor: hex('#ffe8a8'), wispHeight: 0.3 },
    haze: { color: hex('#3a2c4c'), lift: 0.16, bloom: 0.75, bloomThreshold: 0.5, soften: 0.35, mistTop: 0.55, mistStrength: 0.25, vignette: 1.1 },
    paletteExtra: ['#5a4870', '#86709c', '#b29cc4', '#d8c8e2'],
    palette,
    background: { inner: hex('#3a2a4a'), outer: hex('#120c1a'), stars: false },
    camera: { target: [0, 0.12, 0], distance: 3.9, height: 1.5, startAngle: 2.2 },
    staticLists: [meadow, decor],
    dynamic(time) {
      const place = snailPlace(time);
      const lists = [placeSplats(snail, {
        x: place.x, y: 0.0, z: place.z, heading: place.heading, scale: snailScale,
        deform: (x, y, z) => {
          const stretch = 1 + 0.06 * Math.sin(time * 3.2 - x * 6);
          let movedX = x * (y < 0.09 ? stretch : 1);
          let movedY = y;
          if (x > 0.22 && y > 0.15) {
            movedX += 0.012 * Math.sin(time * 2.1 + z * 30);
            movedY += 0.01 * Math.sin(time * 2.7 + z * 20);
          }
          if (y > 0.13 && x < 0.2) movedY += 0.006 * Math.sin(time * 3.2);
          return [movedX, movedY, z];
        },
      })];
      const smoke = [];
      const chimney = chimneyWorld(time);
      for (let puff = 0; puff < 9; puff++) {
        const age = ((time * 0.4 + puff / 9) % 1);
        const birthTime = time - age / 0.4;
        const origin = chimneyWorld(birthTime);
        const drift = age * 0.5;
        smoke.push({
          x: origin[0] + drift * 0.3 + Math.sin(puff * 3 + age * 5) * 0.04,
          y: chimney[1] + age * 0.6,
          z: origin[2] + drift * 0.15,
          color: hex('#d8cfe2'), alpha: 0.55 * (1 - age) * Math.min(age * 8, 1), scale: 0.03 + age * 0.06,
        });
      }
      lists.push(makeList(smoke));
      const fireflies = [];
      for (let fly = 0; fly < 10; fly++) {
        const phase = fly * 1.7;
        fireflies.push({
          x: Math.cos(time * 0.4 + phase) * (0.55 + 0.25 * Math.sin(phase)),
          y: 0.25 + 0.12 * Math.sin(time * 1.3 + phase * 2),
          z: Math.sin(time * 0.35 + phase) * (0.6 + 0.2 * Math.cos(phase)),
          color: hex('#ffeaa0'), alpha: 0.6 + 0.4 * Math.sin(time * 4 + phase), scale: 0.014,
        });
      }
      lists.push(makeList(fireflies));
      return lists;
    },
    glows(time) {
      const place = snailPlace(time);
      const glows = [{ position: [place.x, 0.4 * snailScale, place.z], color: hex('#ffcc66'), radius: 0.25, strength: 0.2 }];
      for (let fly = 0; fly < 10; fly++) {
        const phase = fly * 1.7;
        glows.push({
          position: [Math.cos(time * 0.4 + phase) * (0.55 + 0.25 * Math.sin(phase)), 0.25 + 0.12 * Math.sin(time * 1.3 + phase * 2), Math.sin(time * 0.35 + phase) * (0.6 + 0.2 * Math.cos(phase))],
          color: hex('#ffe08a'), radius: 0.07, strength: 0.3 * (0.6 + 0.4 * Math.sin(time * 4 + phase)),
        });
      }
      return glows;
    },
    contactShadows(time) {
      const place = snailPlace(time);
      return [{ x: place.x, z: place.z, radius: 0.36, strength: 0.5 }];
    },
  };
}

// ---------------------------------------------------------------------------------------------------------------
// A koi pond island with a blossom tree and a stone lantern.
// ---------------------------------------------------------------------------------------------------------------
function buildKoi(spacing) {
  const palette = ['#0b1418', '#132a32', '#1c4650', '#2a6e72', '#5cb2a4', '#d6f4e8', '#f29ab2', '#c0587a',
    '#fbd2dc', '#3e302e', '#6e5650', '#355e36', '#74a454', '#ee7426', '#fff4e4', '#ffd070'].map(hex);
  const light = { sun: [0.45, 0.85, -0.35], sunColor: [1.05, 0.95, 0.88], ambientColor: [0.55, 0.6, 0.66], rimColor: [0.6, 0.4, 0.5], shadowSoftness: 6 };
  const pondRadius = 0.56;
  const pondCenter = [0.12, 0.12];
  const islandWithPond = (x, y, z) => {
    const island = islandDistance(x, y, z, 1.05, 0.95, 0, 0.08);
    const pond = cylinderDistance(x, y, z, pondCenter[0], -0.14, pondCenter[1], pondRadius, 0.3);
    return Math.max(island, -pond);
  };
  const treeDistance = (x, y, z) => {
    const trunk = Math.min(
      capsuleDistance(x, y, z, -0.6, 0, -0.45, -0.55, 0.38, -0.42, 0.055),
      capsuleDistance(x, y, z, -0.55, 0.38, -0.42, -0.38, 0.62, -0.3, 0.035),
      capsuleDistance(x, y, z, -0.55, 0.36, -0.42, -0.7, 0.62, -0.5, 0.03));
    const canopyNoise = (valueNoise(x * 9, y * 9, z * 9) - 0.5) * 0.1;
    const canopy = Math.min(
      ellipsoidDistance(x, y, z, -0.38, 0.72, -0.3, 0.3, 0.2, 0.26),
      ellipsoidDistance(x, y, z, -0.72, 0.7, -0.52, 0.24, 0.18, 0.22),
      ellipsoidDistance(x, y, z, -0.55, 0.86, -0.42, 0.24, 0.16, 0.22)) + canopyNoise;
    return Math.min(trunk, canopy);
  };
  const lanternDistance = (x, y, z) => {
    const lanternX = 0.68;
    const lanternZ = -0.5;
    return Math.min(
      cylinderDistance(x, y, z, lanternX, 0, lanternZ, 0.07, 0.04),
      cylinderDistance(x, y, z, lanternX, 0.04, lanternZ, 0.03, 0.17),
      boxDistance(x, y, z, lanternX, 0.25, lanternZ, 0.07, 0.04, 0.07, 0.008),
      Math.max(taperedCylinderDistance(x, y, z, lanternX, 0.29, lanternZ, 0.12, 0.02, 0.09), -(y - 0.29)),
      sphereDistance(x, y, z, lanternX, 0.39, lanternZ, 0.02));
  };
  const sceneDistance = (x, y, z) => Math.min(islandWithPond(x, y, z), treeDistance(x, y, z), lanternDistance(x, y, z));
  const island = voxelizeModel({
    distance: islandWithPond,
    bounds: [-1.1, -0.98, -1.1, 1.1, 0.1, 1.1],
    material: (x, y, z, normalX, normalY) => {
      const insidePond = Math.hypot(x - pondCenter[0], z - pondCenter[1]) < pondRadius + 0.02;
      if (insidePond) return [...(valueNoise(x * 25, 1, z * 25) > 0.5 ? hex('#6e5650') : hex('#3e302e')), 0];
      if (y > -0.05 && normalY > 0.35) {
        const moss = valueNoise(x * 8, 5, z * 8);
        const pebble = Math.abs(Math.hypot(x - pondCenter[0], z - pondCenter[1]) - pondRadius - 0.05) < 0.04 && valueNoise(x * 30, 1, z * 30) > 0.45;
        if (pebble) return [...hex('#b8b0aa'), 0];
        return [...(moss > 0.55 ? hex('#74a454') : hex('#4f8240')), 0];
      }
      const strata = valueNoise(x * 2, y * 9, z * 2);
      return [...(strata > 0.5 ? hex('#6e5650') : hex('#3e302e')), 0];
    },
  }, spacing, light, { shadowModel: { distance: sceneDistance } });
  const tree = voxelizeModel({
    distance: treeDistance,
    bounds: [-1.0, -0.02, -0.82, -0.05, 1.06, -0.04],
    material: (x, y, z) => {
      const trunk = Math.min(
        capsuleDistance(x, y, z, -0.6, 0, -0.45, -0.55, 0.38, -0.42, 0.06),
        capsuleDistance(x, y, z, -0.55, 0.38, -0.42, -0.38, 0.62, -0.3, 0.04),
        capsuleDistance(x, y, z, -0.55, 0.36, -0.42, -0.7, 0.62, -0.5, 0.035));
      if (trunk < 0.012) return [...hex('#4a3634'), 0];
      const blossom = valueNoise(x * 22, y * 22, z * 22);
      return [...(blossom > 0.62 ? hex('#fbd2dc') : blossom > 0.32 ? hex('#f29ab2') : hex('#d06888')), 0.35];
    },
  }, spacing * 0.9, light, { shadowModel: { distance: sceneDistance } });
  const lantern = voxelizeModel({
    distance: lanternDistance,
    bounds: [0.5, -0.02, -0.68, 0.86, 0.43, -0.32],
    material: (x, y) => {
      if (Math.abs(y - 0.25) < 0.03) return [...hex('#ffd070'), 1];
      return [...(valueNoise(x * 30, y * 30, 0) > 0.5 ? hex('#a8a4a0') : hex('#8a8686')), 0];
    },
  }, spacing * 0.8, light, { shadowModel: { distance: sceneDistance } });

  const koi = [0, 1, 2].map(fish => voxelizeModel({
    distance: (x, y, z) => {
      const body = ellipsoidDistance(x, y, z, 0, 0, 0, 0.11, 0.035, 0.04);
      const tail = Math.max(ellipsoidDistance(x, y, z, -0.13, 0, 0, 0.045, 0.012, 0.045), x + 0.09);
      const fins = Math.max(ellipsoidDistance(x, y, z, 0.03, -0.01, 0, 0.03, 0.008, 0.07), -(Math.abs(z) - 0.03));
      return Math.min(body, tail, fins);
    },
    bounds: [-0.19, -0.05, -0.08, 0.13, 0.05, 0.08],
    material: (x, y, z) => {
      const patch = valueNoise(x * 30 + fish * 7, y * 30, z * 30 + fish * 3);
      if (fish === 1) return [...(patch > 0.55 ? hex('#ee7426') : hex('#fff4e4')), 0.15];
      if (fish === 2) return [...(patch > 0.6 ? hex('#202020') : patch > 0.35 ? hex('#ee7426') : hex('#fff4e4')), 0.15];
      return [...(patch > 0.3 ? hex('#ee7426') : hex('#fff4e4')), 0.15];
    },
  }, spacing * 0.55, { ...light, sun: [0, 1, 0] }));

  const waterSpacing = spacing * 1.3;
  const waterGrid = [];
  for (let x = -pondRadius; x <= pondRadius; x += waterSpacing) {
    for (let z = -pondRadius; z <= pondRadius; z += waterSpacing) {
      if (Math.hypot(x, z) > pondRadius - 0.01) continue;
      waterGrid.push([pondCenter[0] + x, pondCenter[1] + z]);
    }
  }
  const fishPlace = (fish, time) => {
    const radius = 0.22 + fish * 0.09;
    const speed = 0.55 - fish * 0.1;
    const angle = time * speed * (fish === 1 ? -1 : 1) + fish * 2.1;
    return { x: pondCenter[0] + Math.cos(angle) * radius, z: pondCenter[1] + Math.sin(angle) * radius, heading: fish === 1 ? -angle + Math.PI / 2 * -1 : -angle - Math.PI / 2 };
  };
  const petalAt = (petal, time) => {
    const period = 5.5;
    const age = ((time + petal * 0.61) % period) / period;
    const startX = -0.55 + (hashNoise(petal, 1, 0) - 0.5) * 0.7;
    const startZ = -0.4 + (hashNoise(petal, 2, 0) - 0.5) * 0.6;
    const fallHeight = 0.75 - age * 0.82;
    return {
      x: startX + age * 0.6 + Math.sin(age * 9 + petal) * 0.06,
      y: Math.max(fallHeight, 0.0),
      z: startZ + age * 0.45 + Math.cos(age * 7 + petal) * 0.05,
      color: petal % 2 ? hex('#fbd2dc') : hex('#f29ab2'), scale: 0.014,
    };
  };
  return {
    name: 'koi',
    mist: { color: hex('#a8d4cc'), alpha: 0.045, low: -0.1, high: 0.3, wispColor: hex('#ffd6e4'), wispHeight: 0.4 },
    haze: { color: hex('#1e3a40'), lift: 0.15, bloom: 0.75, bloomThreshold: 0.5, soften: 0.35, mistTop: 0.55, mistStrength: 0.22, vignette: 1.1 },
    paletteExtra: ['#2e5458', '#4e7a7a', '#7eaaa4', '#b6d6ce'],
    palette,
    background: { inner: hex('#1c3a40'), outer: hex('#060d10'), stars: false },
    camera: { target: [0, 0.18, 0], distance: 4.5, height: 2.1, startAngle: 4.0 },
    staticLists: [island, tree, lantern],
    dynamic(time) {
      const lists = [];
      koi.forEach((fishModel, fish) => {
        const place = fishPlace(fish, time);
        lists.push(placeSplats(fishModel, {
          x: place.x, y: -0.075, z: place.z, heading: place.heading, scale: 1.45,
          deform: (x, y, z) => [x, y, z + (x < 0 ? Math.sin(time * 7 + fish) * x * x * 2.4 : 0)],
        }));
      });
      const waterPoints = waterGrid.map(([x, z]) => {
        let ripple = 0;
        for (let fish = 0; fish < 3; fish++) {
          const place = fishPlace(fish, time);
          const distance = Math.hypot(x - place.x, z - place.z);
          ripple += Math.max(0, 1 - distance / 0.12) * 0.5;
        }
        const wave = Math.sin(x * 9 + time * 1.4) * Math.sin(z * 8 - time * 1.1);
        const color = wave + ripple > 0.75 ? hex('#5cb2a4') : wave > -0.2 ? hex('#2a6e72') : hex('#1c4650');
        return { x, y: -0.035 + wave * 0.004, z, color, alpha: 0.26, scale: waterSpacing * 0.6 };
      });
      lists.push(makeList(waterPoints));
      const petals = [];
      for (let petal = 0; petal < 26; petal++) petals.push(petalAt(petal, time));
      lists.push(makeList(petals));
      return lists;
    },
    glows() {
      return [{ position: [0.68, 0.25, -0.5], color: hex('#ffd070'), radius: 0.22, strength: 0.45 }];
    },
    contactShadows() {
      return [];
    },
  };
}

function subsetList(list, indices) {
  const positions = new Float32Array(indices.length * 3);
  const colors = new Float32Array(indices.length * 4);
  const scales = new Float32Array(indices.length);
  indices.forEach((source, target) => {
    positions.set(list.positions.subarray(source * 3, source * 3 + 3), target * 3);
    colors.set(list.colors.subarray(source * 4, source * 4 + 4), target * 4);
    scales[target] = list.scales[source];
  });
  return { count: indices.length, positions, colors, scales };
}

export const SCENE_BUILDERS = { lighthouse: buildLighthouse, snail: buildSnail, koi: buildKoi, medieval: buildMedieval, swamp: buildSwamp, gallows: buildGallows };
