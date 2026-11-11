// Turns signed distance models into gaussian splats: every surface voxel of the model becomes one round splat whose
// colour carries baked light (sun, soft shadow, ambient occlusion, rim). Runs in the browser page.

export function hashNoise(x, y, z) {
  let value = Math.sin(x * 127.1 + y * 311.7 + z * 74.7) * 43758.5453;
  return value - Math.floor(value);
}

export function valueNoise(x, y, z) {
  const cellX = Math.floor(x);
  const cellY = Math.floor(y);
  const cellZ = Math.floor(z);
  const fractionX = x - cellX;
  const fractionY = y - cellY;
  const fractionZ = z - cellZ;
  const smoothX = fractionX * fractionX * (3 - 2 * fractionX);
  const smoothY = fractionY * fractionY * (3 - 2 * fractionY);
  const smoothZ = fractionZ * fractionZ * (3 - 2 * fractionZ);
  const lerp = (from, to, amount) => from + (to - from) * amount;
  const corner = (offsetX, offsetY, offsetZ) => hashNoise(cellX + offsetX, cellY + offsetY, cellZ + offsetZ);
  const bottom = lerp(lerp(corner(0, 0, 0), corner(1, 0, 0), smoothX), lerp(corner(0, 1, 0), corner(1, 1, 0), smoothX), smoothY);
  const top = lerp(lerp(corner(0, 0, 1), corner(1, 0, 1), smoothX), lerp(corner(0, 1, 1), corner(1, 1, 1), smoothX), smoothY);
  return lerp(bottom, top, smoothZ);
}

// Distance helpers. Every one takes the point first.
export function sphereDistance(x, y, z, centerX, centerY, centerZ, radius) {
  return Math.hypot(x - centerX, y - centerY, z - centerZ) - radius;
}

export function ellipsoidDistance(x, y, z, centerX, centerY, centerZ, radiusX, radiusY, radiusZ) {
  const scaledX = (x - centerX) / radiusX;
  const scaledY = (y - centerY) / radiusY;
  const scaledZ = (z - centerZ) / radiusZ;
  const length = Math.hypot(scaledX, scaledY, scaledZ);
  return (length - 1) * Math.min(radiusX, radiusY, radiusZ);
}

export function boxDistance(x, y, z, centerX, centerY, centerZ, halfX, halfY, halfZ, rounding = 0) {
  const qx = Math.abs(x - centerX) - halfX + rounding;
  const qy = Math.abs(y - centerY) - halfY + rounding;
  const qz = Math.abs(z - centerZ) - halfZ + rounding;
  const outside = Math.hypot(Math.max(qx, 0), Math.max(qy, 0), Math.max(qz, 0));
  return outside + Math.min(Math.max(qx, qy, qz), 0) - rounding;
}

export function cylinderDistance(x, y, z, centerX, bottomY, centerZ, radius, height) {
  const radial = Math.hypot(x - centerX, z - centerZ) - radius;
  const vertical = Math.abs(y - (bottomY + height / 2)) - height / 2;
  return Math.min(Math.max(radial, vertical), 0) + Math.hypot(Math.max(radial, 0), Math.max(vertical, 0));
}

// A cone standing on bottomY: radius goes from bottomRadius to topRadius over height.
export function taperedCylinderDistance(x, y, z, centerX, bottomY, centerZ, bottomRadius, topRadius, height) {
  const amount = Math.min(Math.max((y - bottomY) / height, 0), 1);
  const radius = bottomRadius + (topRadius - bottomRadius) * amount;
  const radial = (Math.hypot(x - centerX, z - centerZ) - radius) * Math.cos(Math.atan2(Math.abs(bottomRadius - topRadius), height));
  const vertical = Math.abs(y - (bottomY + height / 2)) - height / 2;
  return Math.max(radial, vertical);
}

export function capsuleDistance(x, y, z, startX, startY, startZ, endX, endY, endZ, radius) {
  const segmentX = endX - startX;
  const segmentY = endY - startY;
  const segmentZ = endZ - startZ;
  const pointX = x - startX;
  const pointY = y - startY;
  const pointZ = z - startZ;
  const lengthSquared = segmentX * segmentX + segmentY * segmentY + segmentZ * segmentZ;
  const amount = Math.min(Math.max((pointX * segmentX + pointY * segmentY + pointZ * segmentZ) / lengthSquared, 0), 1);
  return Math.hypot(pointX - segmentX * amount, pointY - segmentY * amount, pointZ - segmentZ * amount) - radius;
}

export function torusDistance(x, y, z, centerX, centerY, centerZ, majorRadius, minorRadius) {
  const ring = Math.hypot(x - centerX, z - centerZ) - majorRadius;
  return Math.hypot(ring, y - centerY) - minorRadius;
}

export function smoothUnion(first, second, softness) {
  const blend = Math.min(Math.max(0.5 + 0.5 * (second - first) / softness, 0), 1);
  return second + (first - second) * blend - softness * blend * (1 - blend);
}

// A floating island: flat top at topY, tapering to a point below, with noisy rock sides.
export function islandDistance(x, y, z, radius, depth, topY = 0, roughness = 0.07) {
  const radial = Math.hypot(x, z);
  const heightBelowTop = topY - y;
  const coneRadius = radius * Math.max(1 - Math.pow(Math.max(heightBelowTop, 0) / depth, 1.4), 0);
  const side = (radial - coneRadius) * 0.7;
  const top = y - topY;
  const noise = (valueNoise(x * 6, y * 6, z * 6) - 0.5) * roughness * 2 + (valueNoise(x * 15, y * 15, z * 15) - 0.5) * roughness * 0.6;
  return Math.max(side, top) + (heightBelowTop > 0.04 ? noise : noise * 0.15);
}

// A model is { distance(x, y, z), material(x, y, z) -> [r, g, b, emission?], bounds: [minX, minY, minZ, maxX, maxY, maxZ] }.
// Light is { sun: [x, y, z] (towards the sun), sunColor, ambientColor, rimColor, shadowSoftness }.
export function voxelizeModel(model, spacing, light, { shadowModel = model, splatScale = 0.62 } = {}) {
  const [minX, minY, minZ, maxX, maxY, maxZ] = model.bounds;
  const countX = Math.ceil((maxX - minX) / spacing) + 1;
  const countY = Math.ceil((maxY - minY) / spacing) + 1;
  const countZ = Math.ceil((maxZ - minZ) / spacing) + 1;
  const field = new Float32Array(countX * countY * countZ);
  const indexOf = (indexX, indexY, indexZ) => (indexZ * countY + indexY) * countX + indexX;
  for (let indexZ = 0; indexZ < countZ; indexZ++) {
    for (let indexY = 0; indexY < countY; indexY++) {
      for (let indexX = 0; indexX < countX; indexX++) {
        field[indexOf(indexX, indexY, indexZ)] = model.distance(minX + indexX * spacing, minY + indexY * spacing, minZ + indexZ * spacing);
      }
    }
  }
  const positions = [];
  const colors = [];
  const sunLength = Math.hypot(...light.sun);
  const sunX = light.sun[0] / sunLength;
  const sunY = light.sun[1] / sunLength;
  const sunZ = light.sun[2] / sunLength;
  for (let indexZ = 1; indexZ < countZ - 1; indexZ++) {
    for (let indexY = 1; indexY < countY - 1; indexY++) {
      for (let indexX = 1; indexX < countX - 1; indexX++) {
        if (field[indexOf(indexX, indexY, indexZ)] > 0) continue;
        const exposed = field[indexOf(indexX + 1, indexY, indexZ)] > 0 || field[indexOf(indexX - 1, indexY, indexZ)] > 0
          || field[indexOf(indexX, indexY + 1, indexZ)] > 0 || field[indexOf(indexX, indexY - 1, indexZ)] > 0
          || field[indexOf(indexX, indexY, indexZ + 1)] > 0 || field[indexOf(indexX, indexY, indexZ - 1)] > 0;
        if (!exposed) continue;
        const x = minX + indexX * spacing;
        const y = minY + indexY * spacing;
        const z = minZ + indexZ * spacing;
        let normalX = field[indexOf(indexX + 1, indexY, indexZ)] - field[indexOf(indexX - 1, indexY, indexZ)];
        let normalY = field[indexOf(indexX, indexY + 1, indexZ)] - field[indexOf(indexX, indexY - 1, indexZ)];
        let normalZ = field[indexOf(indexX, indexY, indexZ + 1)] - field[indexOf(indexX, indexY, indexZ - 1)];
        const normalLength = Math.hypot(normalX, normalY, normalZ) || 1;
        normalX /= normalLength;
        normalY /= normalLength;
        normalZ /= normalLength;
        const surface = model.material(x, y, z, normalX, normalY, normalZ);
        const shaded = shadePoint(shadowModel, x, y, z, normalX, normalY, normalZ, surface, light, sunX, sunY, sunZ, spacing);
        positions.push(x, y, z);
        colors.push(shaded[0], shaded[1], shaded[2], surface[4] ?? 1);
      }
    }
  }
  const count = positions.length / 3;
  const scales = new Float32Array(count).fill(spacing * splatScale);
  return { count, positions: new Float32Array(positions), colors: new Float32Array(colors), scales };
}

function shadePoint(shadowModel, x, y, z, normalX, normalY, normalZ, surface, light, sunX, sunY, sunZ, spacing) {
  const emission = surface[3] ?? 0;
  const facing = Math.max(normalX * sunX + normalY * sunY + normalZ * sunZ, 0);
  let shadow = 1;
  if (facing > 0) {
    let travelled = spacing * 2.5;
    const startX = x + normalX * spacing * 1.2;
    const startY = y + normalY * spacing * 1.2;
    const startZ = z + normalZ * spacing * 1.2;
    for (let step = 0; step < 40 && travelled < 3; step++) {
      const distance = shadowModel.distance(startX + sunX * travelled, startY + sunY * travelled, startZ + sunZ * travelled);
      if (distance < spacing * 0.3) {
        shadow = 0;
        break;
      }
      shadow = Math.min(shadow, light.shadowSoftness * distance / travelled);
      travelled += Math.max(distance, spacing * 0.5);
    }
    shadow = Math.min(Math.max(shadow, 0), 1);
  }
  let occlusion = 0;
  for (let sample = 1; sample <= 4; sample++) {
    const reach = spacing * 1.6 * sample;
    const distance = shadowModel.distance(x + normalX * reach, y + normalY * reach, z + normalZ * reach);
    occlusion += Math.max(reach - distance, 0) / reach / sample;
  }
  const ambient = Math.max(1 - occlusion * 0.9, 0.25) * (0.6 + 0.4 * (normalY * 0.5 + 0.5));
  const rim = Math.pow(Math.max(1 - Math.abs(normalY), 0), 3) * 0.12;
  const result = [0, 0, 0];
  for (let channel = 0; channel < 3; channel++) {
    const lit = surface[channel] * (light.ambientColor[channel] * ambient + light.sunColor[channel] * facing * shadow) + light.rimColor[channel] * rim;
    result[channel] = lit * (1 - emission) + surface[channel] * emission * 1.3;
  }
  return result;
}

// Concatenate splat lists ({ count, positions, colors (0..1 floats, rgba), scales }) into one 67js splat data object.
export function packSplatData(lists) {
  let total = 0;
  for (const list of lists) total += list.count;
  const positions = new Float32Array(total * 3);
  const colors = new Uint8Array(total * 4);
  const scales = new Float32Array(total * 3);
  const rotations = new Float32Array(total * 4);
  const minimum = [Infinity, Infinity, Infinity];
  const maximum = [-Infinity, -Infinity, -Infinity];
  let offset = 0;
  for (const list of lists) {
    for (let index = 0; index < list.count; index++) {
      const target = offset + index;
      for (let axis = 0; axis < 3; axis++) {
        const value = list.positions[index * 3 + axis];
        positions[target * 3 + axis] = value;
        if (value < minimum[axis]) minimum[axis] = value;
        if (value > maximum[axis]) maximum[axis] = value;
        scales[target * 3 + axis] = list.scales[index];
      }
      for (let channel = 0; channel < 4; channel++) {
        colors[target * 4 + channel] = Math.round(Math.min(Math.max(list.colors[index * 4 + channel], 0), 1) * 255);
      }
      rotations[target * 4] = 1;
    }
    offset += list.count;
  }
  return { count: total, positions, colors, scales, rotations, bounds: { minimum, maximum } };
}

// Rigid transform of a local splat list: rotate about Y by heading, then translate.
export function placeSplats(list, { x = 0, y = 0, z = 0, heading = 0, scale = 1, deform = null }) {
  const positions = new Float32Array(list.count * 3);
  const cosine = Math.cos(heading);
  const sine = Math.sin(heading);
  for (let index = 0; index < list.count; index++) {
    let localX = list.positions[index * 3];
    let localY = list.positions[index * 3 + 1];
    let localZ = list.positions[index * 3 + 2];
    if (deform) [localX, localY, localZ] = deform(localX, localY, localZ, index);
    localX *= scale;
    localY *= scale;
    localZ *= scale;
    positions[index * 3] = x + localX * cosine + localZ * sine;
    positions[index * 3 + 1] = y + localY;
    positions[index * 3 + 2] = z - localX * sine + localZ * cosine;
  }
  const scales = scale === 1 ? list.scales : list.scales.map(value => value * scale);
  return { count: list.count, positions, colors: list.colors, scales };
}
