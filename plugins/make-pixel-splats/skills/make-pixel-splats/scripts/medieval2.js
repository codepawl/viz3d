// Two more haunted medieval scenes: a witch's hut in a swamp, and a gallows crossroads where the Reaper waits.
import {
  hashNoise, valueNoise, sphereDistance, ellipsoidDistance, boxDistance, cylinderDistance, taperedCylinderDistance,
  capsuleDistance, torusDistance, smoothUnion, islandDistance, voxelizeModel, placeSplats,
} from './voxel-splats.js';
import { clamp01, easeInCubic, easeOutBack, easeInOutCubic, struckSwing, wobble } from './motion.js';

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
  const side = (Math.max(Math.abs(x - centerX), Math.abs(z - centerZ)) - half) * 0.85;
  return Math.max(side, bottomY - y, y - bottomY - height);
}

function gnarledTree(rootX, rootZ, seed, size) {
  const branches = [];
  const grow = (startX, startY, startZ, angle, tilt, length, radius, depth) => {
    const endX = startX + Math.cos(angle) * Math.sin(tilt) * length;
    const endY = startY + Math.cos(tilt) * length;
    const endZ = startZ + Math.sin(angle) * Math.sin(tilt) * length;
    branches.push([startX, startY, startZ, endX, endY, endZ, radius]);
    if (depth === 0) return;
    for (let child = 0; child < 2; child++) {
      const random = hashNoise(depth * 7 + child + seed * 13, startX * 13, startZ * 11);
      grow(endX, endY, endZ, angle + (child ? 1 : -1) * (0.5 + random * 1.1), tilt + 0.3 + random * 0.4, length * 0.7, radius * 0.6, depth - 1);
    }
  };
  grow(rootX, 0, rootZ, seed * 2.1, 0.25, 0.3 * size, 0.035 * size, 4);
  const tips = branches.filter(branch => branch[6] < 0.006 * size + 0.002).map(branch => [branch[3], branch[4], branch[5]]);
  const distance = (x, y, z) => {
    let best = Infinity;
    for (const [startX, startY, startZ, endX, endY, endZ, radius] of branches) {
      best = Math.min(best, capsuleDistance(x, y, z, startX, startY, startZ, endX, endY, endZ, radius));
    }
    return best;
  };
  return { distance, tips, branches };
}

// Points of a flapping bat or crow around its own origin, facing +x.
function wingedPoints(flap, span, color) {
  const points = [];
  for (let body = 0; body < 3; body++) points.push({ x: body * 0.01 - 0.01, y: 0, z: 0, scale: 0.009 * span });
  for (let side = -1; side <= 1; side += 2) {
    for (let feather = 1; feather <= 5; feather++) {
      const reach = feather * 0.013 * span;
      points.push({ x: -0.004 - feather * 0.003 * span + (feather === 5 ? 0.01 : 0), y: Math.sin(flap) * reach, z: side * Math.cos(flap) * reach, scale: 0.007 * span });
    }
  }
  return points.map(point => ({ ...point, color }));
}

function placePoints(points, centerX, centerY, centerZ, heading, size = 1) {
  const cosine = Math.cos(heading);
  const sine = Math.sin(heading);
  return points.map(point => ({
    ...point,
    x: centerX + (point.x * cosine + point.z * sine) * size,
    y: centerY + point.y * size,
    z: centerZ + (-point.x * sine + point.z * cosine) * size,
    scale: point.scale * size,
  }));
}

// ---------------------------------------------------------------------------------------------------------------
// The witch's swamp.
// ---------------------------------------------------------------------------------------------------------------
export function buildSwamp(spacing) {
  const palette = ['#050806', '#0c140e', '#16241a', '#24382a', '#3a5440', '#5a7a54', '#8aa070', '#c8d0a8',
    '#2a1e18', '#4a3424', '#6e5034', '#3cff7a', '#a8ffb8', '#ff3a20', '#ff9a3a', '#d8d0c0'].map(hex);
  const light = { sun: [0.4, 0.6, 0.7], sunColor: [0.95, 1.05, 1.1], ambientColor: [0.42, 0.46, 0.5], rimColor: [0.4, 0.75, 0.55], shadowSoftness: 7 };
  const poolCenter = [-0.2, 0.15];
  const poolRadius = 0.4;
  const hutCenter = [0.36, -0.32];
  const cauldronCenter = [0.22, 0.42];
  const groundDistance = (x, y, z) => {
    const island = islandDistance(x, y, z, 1.06, 1.15, 0, 0.12);
    const poolCut = cylinderDistance(x, y, z, poolCenter[0], -0.1, poolCenter[1], poolRadius + (valueNoise(x * 8, 0, z * 8) - 0.5) * 0.08, 0.3);
    return Math.max(island, -poolCut);
  };
  const crookedX = (x, y) => x - (y - 0.12) * 0.18;
  const hutDistance = (x, y, z) => {
    const leanX = crookedX(x, y);
    let distance = Infinity;
    for (const [offsetX, offsetZ] of [[-0.13, -0.11], [0.13, -0.11], [-0.13, 0.11], [0.13, 0.11]]) {
      distance = Math.min(distance, capsuleDistance(x, y, z, hutCenter[0] + offsetX, -0.02, hutCenter[1] + offsetZ, hutCenter[0] + offsetX + 0.01, 0.13, hutCenter[1] + offsetZ, 0.016));
    }
    const floor = boxDistance(x, y, z, hutCenter[0], 0.13, hutCenter[1], 0.19, 0.015, 0.16);
    const walls = boxDistance(leanX, y, z, hutCenter[0], 0.25, hutCenter[1], 0.16, 0.11, 0.13, 0.01);
    const roof = pyramidDistance(leanX - (y - 0.36) * 0.12, y, z, hutCenter[0], 0.35, hutCenter[1], 0.23, 0.34);
    const chimney = capsuleDistance(x, y, z, hutCenter[0] - 0.1, 0.3, hutCenter[1] - 0.06, hutCenter[0] - 0.16, 0.66, hutCenter[1] - 0.04, 0.026);
    const steps = boxDistance(x, y, z, hutCenter[0] + 0.12, 0.06, hutCenter[1] + 0.22, 0.05, 0.012, 0.06);
    return Math.min(distance, floor, walls, roof, chimney, steps);
  };
  const cauldronDistance = (x, y, z) => {
    const bowl = Math.max(sphereDistance(x, y, z, cauldronCenter[0], 0.11, cauldronCenter[1], 0.1), y - 0.17);
    const hollow = Math.max(sphereDistance(x, y, z, cauldronCenter[0], 0.11, cauldronCenter[1], 0.082), y - 0.2);
    const rim = torusDistance(x, y, z, cauldronCenter[0], 0.17, cauldronCenter[1], 0.08, 0.012);
    let legs = Infinity;
    for (let leg = 0; leg < 3; leg++) {
      const angle = leg * 2.094;
      legs = Math.min(legs, capsuleDistance(x, y, z, cauldronCenter[0] + Math.cos(angle) * 0.06, 0.04, cauldronCenter[1] + Math.sin(angle) * 0.06, cauldronCenter[0] + Math.cos(angle) * 0.09, -0.01, cauldronCenter[1] + Math.sin(angle) * 0.09, 0.01));
    }
    let logs = Infinity;
    for (let log = 0; log < 4; log++) {
      const angle = log * 1.57 + 0.4;
      logs = Math.min(logs, capsuleDistance(x, y, z, cauldronCenter[0] + Math.cos(angle) * 0.13, 0.0, cauldronCenter[1] + Math.sin(angle) * 0.13, cauldronCenter[0] + Math.cos(angle) * 0.02, 0.025, cauldronCenter[1] + Math.sin(angle) * 0.02, 0.014));
    }
    const liquid = Math.max(sphereDistance(x, y, z, cauldronCenter[0], 0.11, cauldronCenter[1], 0.085), y - 0.155, 0.13 - y);
    return Math.min(Math.max(bowl, -hollow), rim, legs, logs, liquid);
  };
  const leftTree = gnarledTree(-0.66, -0.36, 1, 1.25);
  const rightTree = gnarledTree(0.72, 0.36, 2, 1.0);
  const reedsDistance = (x, y, z) => {
    if (Math.hypot(x - poolCenter[0], z - poolCenter[1]) > poolRadius + 0.14) return 0.1;
    let distance = Infinity;
    for (let reed = 0; reed < 26; reed++) {
      const angle = reed * 0.61 + hashNoise(reed, 1, 1);
      const radius = poolRadius - 0.03 + hashNoise(reed, 2, 2) * 0.12;
      const baseX = poolCenter[0] + Math.cos(angle) * radius;
      const baseZ = poolCenter[1] + Math.sin(angle) * radius;
      const height = 0.12 + hashNoise(reed, 3, 3) * 0.14;
      distance = Math.min(distance, capsuleDistance(x, y, z, baseX, -0.05, baseZ, baseX + 0.02, height, baseZ, 0.006));
      if (reed % 3 === 0) distance = Math.min(distance, capsuleDistance(x, y, z, baseX + 0.018, height - 0.04, baseZ, baseX + 0.02, height, baseZ, 0.013));
    }
    for (const [skullX, skullZ] of [[0.4, 0.62], [0.05, 0.6], [0.52, 0.18]]) {
      const skull = sphereDistance(x, y, z, skullX, 0.035, skullZ, 0.035);
      const jaw = boxDistance(x, y, z, skullX + 0.012, 0.01, skullZ, 0.022, 0.012, 0.022);
      distance = Math.min(distance, smoothUnion(skull, jaw, 0.01));
    }
    return distance;
  };
  const sceneDistance = (x, y, z) => Math.min(groundDistance(x, y, z), hutDistance(x, y, z), cauldronDistance(x, y, z), leftTree.distance(x, y, z), rightTree.distance(x, y, z));
  const shadowModel = { distance: sceneDistance };
  const ground = voxelizeModel({
    distance: groundDistance,
    bounds: [-1.12, -1.2, -1.12, 1.12, 0.08, 1.12],
    material: (x, y, z, normalX, normalY) => {
      const nearPool = Math.hypot(x - poolCenter[0], z - poolCenter[1]) < poolRadius + 0.06;
      if (nearPool) return [...hex('#2a1e18'), 0];
      if (y > -0.06 && normalY > 0.4) {
        const mud = valueNoise(x * 7, 1, z * 7);
        return [...(mud > 0.62 ? hex('#4a5a34') : mud > 0.35 ? hex('#34402a') : hex('#3a2c20')), 0];
      }
      const strata = valueNoise(x * 3, y * 10, z * 3);
      return [...(strata > 0.55 ? hex('#4a3424') : hex('#2a1e18')), 0];
    },
  }, spacing, light, { shadowModel });
  const hut = voxelizeModel({
    distance: hutDistance,
    bounds: [0.05, -0.04, -0.6, 0.66, 0.72, -0.02],
    material: (x, y, z) => {
      const leanX = crookedX(x, y);
      if (y > 0.35 && !(Math.hypot(x - hutCenter[0] + 0.13, z - hutCenter[1] + 0.05) < 0.05 && y > 0.4)) {
        const thatch = valueNoise(x * 30, y * 50, z * 30);
        return [...(thatch > 0.55 ? hex('#6e5034') : thatch > 0.3 ? hex('#4a3a22') : hex('#2e2416')), 0];
      }
      if (y > 0.3) return [...hex('#3a3430'), 0];
      const windowSpot = Math.abs(y - 0.27) < 0.035 && Math.abs(leanX - hutCenter[0]) < 0.045 && z > hutCenter[1] + 0.11;
      if (windowSpot) return [...hex('#3cff7a'), 1];
      const doorSpot = Math.abs(z - hutCenter[1] - 0.05) < 0.04 && leanX > hutCenter[0] + 0.14 && y < 0.31;
      if (doorSpot) return [...hex('#120c08'), 0];
      const plank = Math.floor(leanX * 60 + z * 60) % 2;
      return [...(plank ? hex('#6e5034') : hex('#4a3424')), 0];
    },
  }, spacing * 0.75, light, { shadowModel });
  const cauldron = voxelizeModel({
    distance: cauldronDistance,
    bounds: [cauldronCenter[0] - 0.16, -0.03, cauldronCenter[1] - 0.16, cauldronCenter[0] + 0.16, 0.2, cauldronCenter[1] + 0.16],
    material: (x, y, z) => {
      if (y > 0.13 && y < 0.158 && Math.hypot(x - cauldronCenter[0], z - cauldronCenter[1]) < 0.084) return [...hex('#3cff7a'), 1];
      if (y < 0.035 && Math.hypot(x - cauldronCenter[0], z - cauldronCenter[1]) > 0.04) return [...hex('#3a281c'), 0];
      if (y < 0.035) return [...hex('#ff9a3a'), 1];
      return [...hex('#1c1c20'), 0];
    },
  }, spacing * 0.6, light, { shadowModel });
  const trees = voxelizeModel({
    distance: (x, y, z) => Math.min(leftTree.distance(x, y, z), rightTree.distance(x, y, z)),
    bounds: [-1.1, -0.02, -0.95, 1.12, 1.15, 0.95],
    material: (x, y, z) => [...(valueNoise(x * 30, y * 30, z * 30) > 0.5 ? hex('#2e2620') : hex('#1c1612')), 0],
  }, spacing * 0.75, light, { shadowModel });
  const reeds = voxelizeModel({
    distance: reedsDistance,
    bounds: [-0.75, -0.06, -0.4, 0.65, 0.3, 0.72],
    material: (x, y) => (y < 0.06 && y > 0.0 ? [...hex('#d8d0c0'), 0] : [...hex('#3a5440'), 0]),
  }, spacing * 0.6, light, { shadowModel });

  const charmAnchors = [...leftTree.tips.filter((tip, index) => index % 4 === 1).slice(0, 3), ...rightTree.tips.filter((tip, index) => index % 4 === 2).slice(0, 2)];
  const waterGrid = [];
  const waterSpacing = spacing * 1.3;
  for (let x = -poolRadius; x <= poolRadius; x += waterSpacing) {
    for (let z = -poolRadius; z <= poolRadius; z += waterSpacing) {
      if (Math.hypot(x, z) < poolRadius - 0.01) waterGrid.push([poolCenter[0] + x, poolCenter[1] + z]);
    }
  }
  const eyePairs = [[-0.95, 0.05, -0.3], [0.2, 0.0, -0.98], [-0.5, 0.0, 0.85], [0.95, 0.0, -0.2], [-0.25, 0.42, -0.7]];
  return {
    name: 'swamp',
    mist: { color: hex('#7a8a90'), alpha: 0.022, low: -0.25, high: 0.08, wispColor: hex('#3cff7a'), wispHeight: 0.28, trails: true },
    haze: { color: hex('#10141a'), lift: 0.08, bloom: 0.8, bloomThreshold: 0.6, soften: 0.25, mistTop: 0.65, mistStrength: 0.08, vignette: 1.15 },
    paletteExtra: ['#2e4834', '#4a6a4e', '#7a9a7a', '#1a3a24', '#7affa0', '#5a3a28'],
    palette,
    background: { inner: hex('#1a2622'), outer: hex('#030505'), stars: true, moon: { x: 0.8, y: 0.15, radius: 0.05, color: hex('#d8e8c8'), halo: hex('#3a6a4a') }, clouds: hex('#1e2a26') },
    camera: { target: [0.05, 0.32, 0.05], distance: 4.3, height: 1.2, startAngle: 0.7 },
    staticLists: [ground, hut, cauldron, trees, reeds],
    dynamic(time) {
      const lists = [];
      const water = waterGrid.map(([x, z]) => {
        const ripple = Math.sin(x * 14 + time * 1.2) * Math.sin(z * 12 - time) * 0.5 + 0.5;
        return { x, y: -0.05 + ripple * 0.004, z, color: ripple > 0.85 ? hex('#8aa070') : ripple > 0.55 ? hex('#3a5440') : hex('#24382a'), alpha: 0.9, scale: waterSpacing * 0.62 };
      });
      // Bubbles in the pool and in the cauldron that swell and pop.
      const bubbles = [];
      for (let bubble = 0; bubble < 22; bubble++) {
        const inCauldron = bubble < 12;
        const period = 1.1 + hashNoise(bubble, 1, 5) * 1.4;
        const age = ((time + hashNoise(bubble, 2, 5) * period) % period) / period;
        const angle = hashNoise(bubble, 3, Math.floor((time + hashNoise(bubble, 2, 5) * period) / period)) * Math.PI * 2;
        const radius = Math.sqrt(hashNoise(bubble, 4, Math.floor(time / period))) * (inCauldron ? 0.07 : poolRadius * 0.85);
        const center = inCauldron ? cauldronCenter : poolCenter;
        const size = easeInCubic(age) * (inCauldron ? 0.022 : 0.03);
        if (age > 0.92) continue;
        bubbles.push({
          x: center[0] + Math.cos(angle) * radius, y: (inCauldron ? 0.158 : -0.045) + size * 0.5, z: center[1] + Math.sin(angle) * radius,
          color: inCauldron ? hex('#a8ffb8') : hex('#5a7a54'), alpha: inCauldron ? 0.9 : 0.7, scale: size,
        });
      }
      // Green fumes from the cauldron and the chimney.
      const fumes = [];
      for (let puff = 0; puff < 16; puff++) {
        const fromChimney = puff >= 10;
        const period = fromChimney ? 3.2 : 2.4;
        const age = ((time / period) + puff / (fromChimney ? 6 : 10)) % 1;
        const originX = fromChimney ? hutCenter[0] - 0.16 : cauldronCenter[0];
        const originZ = fromChimney ? hutCenter[1] - 0.04 : cauldronCenter[1];
        const originY = fromChimney ? 0.68 : 0.17;
        fumes.push({
          x: originX + wobble(time + puff, puff) * 0.05 * age + age * 0.12,
          y: originY + easeInOutCubic(age) * 0.55,
          z: originZ + wobble(time * 0.7, puff + 9) * 0.05 * age,
          color: fromChimney ? hex('#5a6a5a') : hex('#3cff7a'), alpha: (fromChimney ? 0.35 : 0.3) * (1 - age) * Math.min(age * 6, 1), scale: 0.03 + age * 0.07,
        });
      }
      // Flames licking the cauldron.
      const flames = [];
      for (let flame = 0; flame < 14; flame++) {
        const age = ((time * 2.2) + flame / 14) % 1;
        const angle = flame * 2.4;
        flames.push({
          x: cauldronCenter[0] + Math.cos(angle) * 0.06 * (1 - age), y: 0.01 + age * 0.09, z: cauldronCenter[1] + Math.sin(angle) * 0.06 * (1 - age),
          color: age < 0.4 ? hex('#ffd88a') : hex('#ff6a2a'), alpha: 1 - age, scale: 0.022 * (1 - age * 0.6),
        });
      }
      // Bone charms on ropes swinging in gusts.
      const charms = [];
      charmAnchors.forEach(([anchorX, anchorY, anchorZ], charmIndex) => {
        const gust = 0.25 * wobble(time * 0.8, charmIndex) + struckSwing(time, 5.5, 0.35, 2.6, 0.7, charmIndex * 0.7);
        const ropeLength = 0.12 + charmIndex % 2 * 0.06;
        for (let knot = 0; knot <= 8; knot++) {
          const along = knot / 8 * ropeLength;
          charms.push({ x: anchorX + Math.sin(gust) * along, y: anchorY - Math.cos(gust) * along, z: anchorZ, color: hex('#2a1e18'), scale: 0.004 });
        }
        const endX = anchorX + Math.sin(gust) * ropeLength;
        const endY = anchorY - Math.cos(gust) * ropeLength;
        const doll = [[0, -0.01], [0, -0.03], [0, -0.05], [-0.02, -0.025], [0.02, -0.025], [-0.012, -0.065], [0.012, -0.065], [0, 0.006]];
        for (const [offsetX, offsetY] of doll) {
          charms.push({ x: endX + offsetX * Math.cos(gust) - offsetY * Math.sin(gust) * 0, y: endY + offsetY, z: anchorZ, color: hex('#d8d0c0'), scale: 0.008 });
        }
      });
      // Bats flying in jerky loops.
      const bats = [];
      for (let bat = 0; bat < 8; bat++) {
        const phase = bat * 1.9;
        const angle = time * (0.9 + hashNoise(bat, 1, 1) * 0.6) + phase + wobble(time * 2.2, phase) * 0.8;
        const radius = 0.55 + hashNoise(bat, 2, 2) * 0.5 + wobble(time * 1.7, phase + 3) * 0.12;
        const centerY = 0.75 + wobble(time * 2.5, phase + 5) * 0.15 + hashNoise(bat, 3, 3) * 0.3;
        const flap = Math.sin(time * 22 + phase) * 1.1;
        bats.push(...placePoints(wingedPoints(flap, 0.9, hex('#06060a')), Math.cos(angle) * radius, centerY, Math.sin(angle) * radius, -angle - Math.PI / 2, 1.5));
      }
      // Red eyes in the dark around the edge that blink.
      const eyes = [];
      eyePairs.forEach(([eyeX, eyeY, eyeZ], pair) => {
        const open = Math.sin(time * 0.7 + pair * 2.3) > -0.2 && (time * 2.3 + pair * 0.37) % 3.1 > 0.14;
        if (!open) return;
        const sideX = -eyeZ * 0.03;
        const sideZ = eyeX * 0.03;
        for (const side of [-1, 1]) {
          eyes.push({ x: eyeX + sideX * side * 1.3, y: eyeY + 0.05, z: eyeZ + sideZ * side * 1.3, color: hex('#ff3a20'), scale: 0.016 });
        }
      });
      lists.push(makeList(water), makeList(bubbles), makeList(fumes), makeList(flames), makeList(charms), makeList(bats), makeList(eyes));
      return lists;
    },
    glows(time) {
      const flicker = 0.8 + 0.2 * hashNoise(Math.floor(time * 12), 4, 4);
      return [
        { position: [cauldronCenter[0], 0.2, cauldronCenter[1]], color: hex('#3cff7a'), radius: 0.42, strength: 0.55 * flicker },
        { position: [cauldronCenter[0], 0.03, cauldronCenter[1]], color: hex('#ff8a3a'), radius: 0.22, strength: 0.45 * flicker },
        { position: [hutCenter[0], 0.27, hutCenter[1] + 0.14], color: hex('#3cff7a'), radius: 0.2, strength: 0.35 * flicker },
        ...eyePairs.filter((pair, index) => Math.sin(time * 0.7 + index * 2.3) > -0.2).map(([eyeX, eyeY, eyeZ]) => ({ position: [eyeX, eyeY + 0.05, eyeZ], color: hex('#ff3a20'), radius: 0.09, strength: 0.4 })),
      ];
    },
    contactShadows() {
      return [];
    },
  };
}

// ---------------------------------------------------------------------------------------------------------------
// The gallows crossroads and the Reaper.
// ---------------------------------------------------------------------------------------------------------------
export const REAPER_TIMING = { eyes: 4.4, raise: 5.0, slash: 6.0 };
export const GALLOWS_BOLTS = [1.1, 6.05];

export function buildGallows(spacing) {
  const palette = ['#050508', '#0c0c14', '#16161f', '#24242f', '#383846', '#565666', '#7e7e8c', '#b8b8c2',
    '#2a1e18', '#4a3424', '#6e1018', '#a8202a', '#ff3a20', '#e8e4d8', '#c8d4ff', '#8a96c8'].map(hex);
  const light = { sun: [-0.5, 0.6, 0.6], sunColor: [0.75, 0.82, 1.1], ambientColor: [0.32, 0.33, 0.44], rimColor: [0.45, 0.5, 0.8], shadowSoftness: 7 };
  const hill = (x, z) => 0.22 * Math.exp(-(x * x + z * z) / 0.3);
  const gibbetBase = [-0.22, -0.12];
  const gibbetTop = 1.12;
  const armEnd = [0.2, gibbetBase[1]];
  const groundDistance = (x, y, z) => islandDistance(x, y - hill(x, z), z, 1.08, 1.2, 0, 0.12) * 0.85;
  const baseY = hill(gibbetBase[0], gibbetBase[1]);
  const gibbetDistance = (x, y, z) => {
    const post = boxDistance(x, y, z, gibbetBase[0], (gibbetTop + baseY) / 2, gibbetBase[1], 0.025, (gibbetTop - baseY) / 2 + 0.02, 0.025);
    const arm = boxDistance(x, y, z, (gibbetBase[0] + armEnd[0]) / 2, gibbetTop, gibbetBase[1], (armEnd[0] - gibbetBase[0]) / 2 + 0.02, 0.02, 0.02);
    const brace = capsuleDistance(x, y, z, gibbetBase[0], gibbetTop - 0.22, gibbetBase[1], gibbetBase[0] + 0.2, gibbetTop, gibbetBase[1], 0.013);
    const footing = Math.max(sphereDistance(x, y, z, gibbetBase[0], baseY, gibbetBase[1], 0.09) + (valueNoise(x * 30, y * 30, z * 30) - 0.5) * 0.03, -(y - baseY + 0.05));
    return Math.min(post, arm, brace, footing);
  };
  const pikes = [[0.55, 0.45], [0.7, -0.1], [-0.6, 0.45], [0.15, 0.78]];
  const propsDistance = (x, y, z) => {
    let distance = Infinity;
    for (const [pikeX, pikeZ] of pikes) {
      const groundY = hill(pikeX, pikeZ);
      distance = Math.min(distance, capsuleDistance(x, y, z, pikeX, groundY - 0.02, pikeZ, pikeX + 0.01, groundY + 0.34, pikeZ, 0.01));
      const skull = sphereDistance(x, y, z, pikeX + 0.01, groundY + 0.38, pikeZ, 0.042);
      const jaw = boxDistance(x, y, z, pikeX + 0.02, groundY + 0.345, pikeZ, 0.026, 0.014, 0.026);
      distance = Math.min(distance, smoothUnion(skull, jaw, 0.012));
    }
    const signGround = hill(-0.55, -0.45);
    const signPost = capsuleDistance(x, y, z, -0.55, signGround - 0.02, -0.45, -0.52, signGround + 0.4, -0.45, 0.013);
    const signBoard = boxDistance(x, y, z, -0.47, signGround + 0.33, -0.45, 0.09, 0.025, 0.008, 0.004);
    const signBoardLow = boxDistance(x, y, z, -0.6, signGround + 0.25, -0.43, 0.008, 0.022, 0.08, 0.004);
    const cartWheel = Math.max(torusDistance(x, y, z, 0.42, hill(0.42, -0.5) + 0.02, -0.5, 0.1, 0.013), Math.abs(y - hill(0.42, -0.5) - 0.02) - 0.02);
    return Math.min(distance, signPost, signBoard, signBoardLow, cartWheel);
  };
  const sceneDistance = (x, y, z) => Math.min(groundDistance(x, y, z), gibbetDistance(x, y, z), propsDistance(x, y, z));
  const shadowModel = { distance: sceneDistance };
  const ground = voxelizeModel({
    distance: groundDistance,
    bounds: [-1.14, -1.15, -1.14, 1.14, 0.3, 1.14],
    material: (x, y, z, normalX, normalY) => {
      const groundY = hill(x, z);
      const onPath = (Math.abs(x - z * 0.3) < 0.07 || Math.abs(z + x * 0.2) < 0.06) && y > groundY - 0.05;
      if (y > groundY - 0.06 && normalY > 0.4) {
        if (onPath) return [...(valueNoise(x * 30, 1, z * 30) > 0.5 ? hex('#4a3a2e') : hex('#3a2c22')), 0];
        const grass = valueNoise(x * 9, 3, z * 9);
        return [...(grass > 0.6 ? hex('#5a5a4a') : grass > 0.3 ? hex('#44443a') : hex('#34322c')), 0];
      }
      const strata = valueNoise(x * 3, y * 10, z * 3);
      return [...(strata > 0.6 ? hex('#565666') : strata > 0.3 ? hex('#383846') : hex('#24242f')), 0];
    },
  }, spacing, light, { shadowModel });
  const gibbet = voxelizeModel({
    distance: gibbetDistance,
    bounds: [-0.33, 0.05, -0.23, 0.25, 1.16, -0.01],
    material: (x, y, z) => (y < baseY + 0.05 && Math.hypot(x - gibbetBase[0], z - gibbetBase[1]) > 0.03
      ? [...hex('#565666'), 0]
      : [...(valueNoise(x * 6, y * 60, z * 6) > 0.5 ? hex('#4a3424') : hex('#2a1e18')), 0]),
  }, spacing * 0.7, light, { shadowModel });
  const props = voxelizeModel({
    distance: propsDistance,
    bounds: [-0.72, -0.05, -0.65, 0.8, 0.72, 0.85],
    material: (x, y, z) => {
      for (const [pikeX, pikeZ] of pikes) {
        const groundY = hill(pikeX, pikeZ);
        if (Math.hypot(x - pikeX - 0.01, y - groundY - 0.38, z - pikeZ) < 0.05 || (Math.abs(y - groundY - 0.345) < 0.02 && Math.hypot(x - pikeX, z - pikeZ) < 0.04)) {
          const socket = Math.abs(y - groundY - 0.385) < 0.012 && Math.abs(Math.atan2(z - pikeZ, x - pikeX - 0.01)) > 0.0 && valueNoise(x * 90, y * 90, z * 90) > 0.62;
          return [...(socket ? hex('#0c0c14') : hex('#d8d2c2')), 0];
        }
      }
      return [...(valueNoise(x * 40, y * 40, z * 40) > 0.5 ? hex('#4a3424') : hex('#2a1e18')), 0];
    },
  }, spacing * 0.6, light, { shadowModel });

  // Cage hanging from the arm, built around its hinge at the origin.
  const cage = voxelizeModel({
    distance: (x, y, z) => {
      const chain = capsuleDistance(x, y, z, 0, 0, 0, 0, -0.1, 0, 0.006);
      const top = torusDistance(x, y, z, 0, -0.11, 0, 0.07, 0.007);
      const bottom = torusDistance(x, y, z, 0, -0.4, 0, 0.07, 0.007);
      let bars = Infinity;
      for (let bar = 0; bar < 8; bar++) {
        const angle = bar * Math.PI / 4;
        bars = Math.min(bars, capsuleDistance(x, y, z, Math.cos(angle) * 0.07, -0.11, Math.sin(angle) * 0.07, Math.cos(angle) * 0.075, -0.4, Math.sin(angle) * 0.075, 0.005));
      }
      const skull = sphereDistance(x, y, z, 0.0, -0.17, 0, 0.034);
      const spine = capsuleDistance(x, y, z, 0, -0.2, 0, 0.005, -0.33, 0, 0.008);
      let ribs = Infinity;
      for (let rib = 0; rib < 4; rib++) ribs = Math.min(ribs, Math.max(torusDistance(x, y, z, 0.0, -0.23 - rib * 0.024, 0, 0.032 - rib * 0.002, 0.004), -x));
      const armLeft = capsuleDistance(x, y, z, 0, -0.22, 0.03, 0.03, -0.32, 0.045, 0.007);
      const armRight = capsuleDistance(x, y, z, 0, -0.22, -0.03, 0.04, -0.3, -0.045, 0.007);
      const legs = Math.min(capsuleDistance(x, y, z, 0, -0.33, 0.015, 0.02, -0.39, 0.025, 0.008), capsuleDistance(x, y, z, 0, -0.33, -0.015, 0.03, -0.38, -0.03, 0.008));
      return Math.min(chain, top, bottom, bars, skull, spine, ribs, armLeft, armRight, legs);
    },
    bounds: [-0.09, -0.42, -0.09, 0.09, 0.01, 0.09],
    material: (x, y, z) => {
      const inside = Math.hypot(x, z) < 0.06 && y < -0.13;
      if (inside) {
        const socket = y > -0.18 && y < -0.16 && x > 0.022 && Math.abs(Math.abs(z) - 0.012) < 0.008;
        return [...(socket ? hex('#050508') : hex('#d8d2c2')), 0];
      }
      return [...hex('#2a2a32'), 0];
    },
  }, spacing * 0.45, light);

  // The Reaper, facing +x, origin on the ground.
  const reaper = voxelizeModel({
    distance: (x, y, z) => {
      const tatter = (valueNoise(x * 40, y * 10, z * 40) - 0.5) * 0.03 + Math.max(0.04 - y, 0) * (valueNoise(Math.atan2(z, x) * 6, 0, 1) > 0.5 ? 1 : 0) * 1.5;
      const robe = taperedCylinderDistance(x, y, z, 0, 0, 0, 0.12, 0.06, 0.46) + tatter;
      const shoulders = ellipsoidDistance(x, y, z, 0, 0.44, 0, 0.07, 0.05, 0.1);
      const hood = Math.min(ellipsoidDistance(x, y, z, -0.005, 0.53, 0, 0.065, 0.075, 0.06), taperedCylinderDistance(x, y, z, -0.03, 0.55, 0, 0.05, 0.0, 0.11));
      const face = ellipsoidDistance(x, y, z, 0.05, 0.52, 0, 0.03, 0.05, 0.04);
      const armBack = capsuleDistance(x, y, z, 0, 0.43, -0.08, 0.06, 0.34, -0.1, 0.028);
      const skull = ellipsoidDistance(x, y, z, 0.028, 0.515, 0, 0.036, 0.043, 0.032);
      return Math.min(Math.max(smoothUnion(Math.min(robe, shoulders), hood, 0.02), -face), armBack, skull);
    },
    bounds: [-0.15, -0.02, -0.15, 0.15, 0.68, 0.15],
    material: (x, y, z) => {
      const insideSkull = Math.hypot((x - 0.028) / 0.036, (y - 0.515) / 0.043, z / 0.032) < 1.2;
      if (insideSkull) {
        const socket = y > 0.515 && y < 0.54 && Math.abs(Math.abs(z) - 0.014) < 0.009 && x > 0.04;
        const teeth = y < 0.49 && x > 0.045 && Math.floor(z * 160) % 2 === 0;
        return [...(socket ? hex('#050508') : teeth ? hex('#8a8478') : hex('#e8e2d2')), socket ? 0 : 0.3];
      }
      if (y > 0.47 && x > 0.035) return [...hex('#050508'), 0];
      return [...(y < 0.06 ? hex('#16161f') : hex('#24242f')), 0];
    },
  }, spacing * 0.6, light);
  // Scythe built around the hand that holds it at the origin: staff along +y, blade at the top curving to -x... +x.
  const scythe = voxelizeModel({
    distance: (x, y, z) => {
      const staff = capsuleDistance(x, y, z, 0, -0.3, 0, 0.02, 0.4, 0, 0.011);
      let blade = Infinity;
      for (let segment = 0; segment < 7; segment++) {
        const from = segment / 7;
        const to = (segment + 1) / 7;
        const point = amount => [0.02 + Math.sin(amount * 1.6) * 0.36, 0.4 + Math.sin(amount * 3.0) * 0.07 - amount * 0.1, 0];
        const [startX, startY] = point(from);
        const [endX, endY] = point(to);
        blade = Math.min(blade, capsuleDistance(x, y, z, startX, startY, 0, endX, endY, 0, 0.016 * (1 - from * 0.8)));
      }
      return Math.min(staff, Math.max(blade, Math.abs(z) - 0.006));
    },
    bounds: [-0.04, -0.32, -0.04, 0.42, 0.5, 0.04],
    material: (x, y) => (y > 0.3 && x > 0.04 ? [...hex('#d8dce8'), 0.35] : [...hex('#2a1e18'), 0]),
  }, spacing * 0.45, light);

  const reaperSpot = [0.32, 0.22];
  const reaperGround = hill(reaperSpot[0], reaperSpot[1]);
  const startAngle = 0.95;
  const reaperHeading = startAngle - Math.PI / 2 + 0.25;
  const scytheAngle = time => {
    const { raise, slash } = REAPER_TIMING;
    const rest = -0.15;
    const raised = 1.25;
    const struck = -1.1;
    if (time < raise) return rest + Math.sin(time * 0.8) * 0.04;
    if (time < slash) return rest + (raised - rest) * easeInOutCubic((time - raise) / (slash - raise - 0.15));
    return raised + (struck - raised) * easeOutBack((time - slash) / 0.28, 1.2);
  };
  return {
    name: 'gallows',
    mist: { color: hex('#7a7e96'), alpha: 0.035, low: -0.2, high: 0.2, wispColor: hex('#c8d4ff'), wispHeight: 0.35, trails: true },
    haze: { color: hex('#12121c'), lift: 0.14, bloom: 0.85, bloomThreshold: 0.58, soften: 0.3, mistTop: 0.6, mistStrength: 0.1, vignette: 1.2 },
    paletteExtra: ['#4a4a5a', '#6a6a7c', '#9a9aaa', '#3a1018', '#d84040', '#d8d2c2'],
    palette,
    background: { inner: hex('#1a1a28'), outer: hex('#030306'), stars: true, moon: { x: 0.2, y: 0.12, radius: 0.04, color: hex('#e0c8c0'), halo: hex('#6a3a40') }, clouds: hex('#22222e') },
    camera: { target: [0.05, 0.5, 0.05], distance: 4.3, height: 1.15, startAngle },
    staticLists: [ground, gibbet, props],
    dynamic(time) {
      const lists = [];
      const swing = 0.22 * wobble(time * 0.7, 3) + struckSwing(time, 7, 0.3, 2.2, 0.35, 0.8);
      lists.push(placeSplats(cage, {
        x: armEnd[0] - 0.03, y: gibbetTop - 0.02, z: armEnd[1],
        deform: (x, y, z) => [x * Math.cos(swing) - y * Math.sin(swing), x * Math.sin(swing) + y * Math.cos(swing), z + Math.sin(time * 0.9) * 0.01 * -y],
      }));
      // The Reaper hovers, leans in as he raises the scythe.
      const hover = 0.02 + Math.sin(time * 1.3) * 0.012;
      const lean = easeInOutCubic((time - REAPER_TIMING.raise) / 1.0) * 0.12;
      const reaperY = reaperGround + hover;
      lists.push(placeSplats(reaper, {
        x: reaperSpot[0], y: reaperY, z: reaperSpot[1], heading: reaperHeading,
        deform: (x, y, z) => [x + y * lean * 0.6 + Math.sin(time * 2 + y * 9) * 0.006 * Math.max(0.1 - y, 0) * 10, y, z + Math.sin(time * 1.7 + y * 12) * 0.008 * Math.max(0.12 - y, 0) * 8],
      }));
      const handLocal = [0.08, 0.36, 0.1];
      const angle = scytheAngle(time);
      const cosine = Math.cos(reaperHeading);
      const sine = Math.sin(reaperHeading);
      const handWorld = [reaperSpot[0] + handLocal[0] * cosine + handLocal[2] * sine, reaperY + handLocal[1], reaperSpot[1] - handLocal[0] * sine + handLocal[2] * cosine];
      lists.push(placeSplats(scythe, {
        x: handWorld[0], y: handWorld[1], z: handWorld[2], heading: reaperHeading,
        deform: (x, y, z) => [z, x * Math.sin(angle) + y * Math.cos(angle), -(x * Math.cos(angle) - y * Math.sin(angle))],
      }));
      // Eyes ignite.
      const eyeGlow = clamp01((time - REAPER_TIMING.eyes) / 0.5);
      if (eyeGlow > 0) {
        const eyes = [];
        for (const side of [-1, 1]) {
          const localX = 0.066;
          const localZ = side * 0.014;
          eyes.push({ x: reaperSpot[0] + localX * cosine + localZ * sine, y: reaperY + 0.527, z: reaperSpot[1] - localX * sine + localZ * cosine, color: hex('#ff3a20'), alpha: eyeGlow, scale: 0.0065 });
        }
        lists.push(makeList(eyes));
      }
      // Ravens on the arm, pecking.
      const ravens = [];
      for (let raven = 0; raven < 3; raven++) {
        const ravenX = gibbetBase[0] + 0.06 + raven * 0.09;
        const peck = Math.max(0, Math.sin(time * 2.4 + raven * 2)) ** 6 * 0.02;
        for (const [offsetX, offsetY, scale] of [[0, 0.04, 0.022], [0.018, 0.05, 0.018], [0.036, 0.062 - peck, 0.014], [0.048, 0.06 - peck, 0.008], [-0.03, 0.032, 0.014]]) {
          ravens.push({ x: ravenX + offsetX, y: gibbetTop + offsetY, z: gibbetBase[1], color: hex('#0a0a10'), scale });
        }
      }
      lists.push(makeList(ravens));
      // A lightning bolt in the back when the sky flashes.
      const bolt = [];
      for (const boltTime of GALLOWS_BOLTS) {
        const age = time - boltTime;
        if (age < 0 || age > 0.22) continue;
        const fade = 1 - age / 0.22;
        const strike = (startX, startY, startZ, steps, stepLength, width, seed) => {
          let boltX = startX;
          let boltY = startY;
          let boltZ = startZ;
          for (let step = 0; step < steps; step++) {
            const nextX = boltX + (hashNoise(step, boltTime, seed) - 0.5) * stepLength * 2.2;
            const nextY = boltY - stepLength;
            const nextZ = boltZ + (hashNoise(step, boltTime, seed + 1) - 0.5) * stepLength;
            for (let fill = 0; fill < 4; fill++) {
              const amount = fill / 4;
              const x = boltX + (nextX - boltX) * amount;
              const y = boltY + (nextY - boltY) * amount;
              const z = boltZ + (nextZ - boltZ) * amount;
              bolt.push({ x, y, z, color: hex('#ffffff'), alpha: fade, scale: width });
              bolt.push({ x, y, z, color: hex('#8a96ff'), alpha: fade * 0.35, scale: width * 3 });
            }
            if (seed < 10 && step % 7 === 3) strike(nextX, nextY, nextZ, 6, stepLength * 0.8, width * 0.6, seed + 10 + step);
            boltX = nextX;
            boltY = nextY;
            boltZ = nextZ;
          }
        };
        strike(-0.75, 2.4, -1.3, 34, 0.075, 0.016, 1);
      }
      if (bolt.length) lists.push(makeList(bolt));
      return lists;
    },
    glows(time) {
      const glows = [];
      const eyeGlow = clamp01((time - REAPER_TIMING.eyes) / 0.5);
      if (eyeGlow > 0) glows.push({ position: [reaperSpot[0], reaperGround + 0.55, reaperSpot[1]], color: hex('#ff3a20'), radius: 0.07, strength: 0.16 * eyeGlow * (0.85 + 0.15 * Math.sin(time * 9)) });
      for (const boltTime of GALLOWS_BOLTS) {
        const age = time - boltTime;
        if (age >= 0 && age < 0.25) glows.push({ position: [-0.75, 1.3, -1.3], color: hex('#c8d4ff'), radius: 1.5, strength: 0.8 * (1 - age / 0.25) });
      }
      return glows;
    },
    contactShadows(time) {
      return [{ x: reaperSpot[0], z: reaperSpot[1], radius: 0.18, strength: 0.4 }];
    },
    reaperFace: () => [reaperSpot[0], reaperGround + 0.55, reaperSpot[1]],
  };
}
