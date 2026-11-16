// "Pocket Seasons" as one continuous scene: each season holds, then turns into the next in place, block by block.
// Every block of the old season and the new one gets the same switch moment, so a block that exists in both just
// changes colour (leaves turning orange, grass under snow), a block only in the new season grows up out of the
// ground, and a block only in the old one sinks away. Leaves that leave the tree fall and blow off instead.
// The tree turns first and the ground after it, except in the thaw, when the snow melts before the tree blooms.
import { hashNoise, valueNoise } from './voxel-splats.js';
import { buildSeason, swayTree, packPoints, WIND } from './seasons.js';
import { VOXEL } from './island-parts.js';

export const SEASON_ORDER = ['spring', 'summer', 'autumn', 'winter'];
export const HOLD_SECONDS = 1.5;
export const TURN_SECONDS = 1.5;
export const CYCLE_SECONDS = SEASON_ORDER.length * (HOLD_SECONDS + TURN_SECONDS);

const PART_NAMES = ['world', 'cabin', 'tree'];
const GROW_SHARE = 0.12;

// Where the switch moments of each part fall inside a turn, as [start, length] of the 0..1 turn.
const PART_WINDOWS = [
  { world: [0.15, 0.8], cabin: [0.15, 0.8], tree: [0, 0.5] },
  { world: [0.3, 0.7], cabin: [0.3, 0.7], tree: [0, 0.4] },
  { world: [0.25, 0.75], cabin: [0.2, 0.75], tree: [0, 0.35] },
  { world: [0, 0.7], cabin: [0, 0.65], tree: [0.3, 0.7] },
];

export function seasonAt(time) {
  const phase = ((time % CYCLE_SECONDS) + CYCLE_SECONDS) % CYCLE_SECONDS;
  const index = Math.floor(phase / (HOLD_SECONDS + TURN_SECONDS));
  const within = phase - index * (HOLD_SECONDS + TURN_SECONDS);
  const progress = within < HOLD_SECONDS ? 0 : (within - HOLD_SECONDS) / TURN_SECONDS;
  return { from: index, to: (index + 1) % SEASON_ORDER.length, progress };
}

function blockKeys(list) {
  const keys = new Int32Array(list.count);
  for (let index = 0; index < list.count; index++) {
    const cellX = Math.floor(list.positions[index * 3] / VOXEL);
    const cellY = Math.floor(list.positions[index * 3 + 1] / VOXEL);
    const cellZ = Math.floor(list.positions[index * 3 + 2] / VOXEL);
    keys[index] = ((cellX + 512) * 1024 + (cellY + 512)) * 1024 + (cellZ + 512);
  }
  return keys;
}

function unpackKey(key) {
  const cellZ = (key % 1024) - 512;
  const cellY = (Math.floor(key / 1024) % 1024) - 512;
  const cellX = Math.floor(key / (1024 * 1024)) - 512;
  return [cellX, cellY, cellZ];
}

// The switch moment of one block in one turn: soft patches of noise plus a little per-block scatter, so the change
// spreads in blotches instead of a hard front or salt-and-pepper.
function switchMoment(key, turnIndex, partName) {
  const [cellX, cellY, cellZ] = unpackKey(key);
  const patch = valueNoise(cellX * 0.16, cellY * 0.16 + turnIndex * 7.3, cellZ * 0.16);
  const scatter = hashNoise(cellX, cellY + turnIndex * 13, cellZ);
  const [start, length] = PART_WINDOWS[turnIndex][partName];
  return start + length * Math.min(1, Math.max(0, patch * 0.5 + scatter * 0.5));
}

export function buildSeasonCycle(spacing, look = {}) {
  const seasons = SEASON_ORDER.map(name => buildSeason(spacing, name, look));
  const blocks = seasons.map(season => Object.fromEntries(PART_NAMES.map(partName => {
    const keys = blockKeys(season.parts[partName]);
    return [partName, { keys, present: new Set(keys) }];
  })));
  const momentCache = new Map();

  function momentsFor(seasonIndex, partName, turnIndex) {
    const cacheKey = `${seasonIndex}:${partName}:${turnIndex}`;
    let moments = momentCache.get(cacheKey);
    if (!moments) {
      const { keys } = blocks[seasonIndex][partName];
      const byBlock = new Map();
      moments = new Float32Array(keys.length);
      for (let index = 0; index < keys.length; index++) {
        let moment = byBlock.get(keys[index]);
        if (moment === undefined) {
          moment = switchMoment(keys[index], turnIndex, partName);
          byBlock.set(keys[index], moment);
        }
        moments[index] = moment;
      }
      momentCache.set(cacheKey, moments);
    }
    return moments;
  }

  // One part mid-turn: the old season's splats until their block's moment, the new season's after it.
  function blendPart(partName, turn) {
    const oldList = seasons[turn.from].parts[partName];
    const newList = seasons[turn.to].parts[partName];
    const oldBlocks = blocks[turn.from][partName];
    const newBlocks = blocks[turn.to][partName];
    const oldMoments = momentsFor(turn.from, partName, turn.from);
    const newMoments = momentsFor(turn.to, partName, turn.from);
    const positions = [];
    const colors = [];
    const scales = [];
    const keep = (list, index, x, y, z) => {
      positions.push(x, y, z);
      colors.push(list.colors[index * 4], list.colors[index * 4 + 1], list.colors[index * 4 + 2], list.colors[index * 4 + 3]);
      scales.push(list.scales[index]);
    };
    for (let index = 0; index < oldList.count; index++) {
      const x = oldList.positions[index * 3];
      const y = oldList.positions[index * 3 + 1];
      const z = oldList.positions[index * 3 + 2];
      const since = turn.progress - oldMoments[index];
      if (since < 0) {
        keep(oldList, index, x, y, z);
        continue;
      }
      if (newBlocks.present.has(oldBlocks.keys[index])) continue;
      if (partName === 'tree' && y > 0.3) {
        // A leaf block that leaves the tree drops with the wind, tumbling a little, until it reaches the ground.
        const seconds = since * TURN_SECONDS;
        const fallenY = y - 0.1 * seconds - 0.9 * seconds * seconds;
        if (fallenY < 0.01) continue;
        const sway = Math.sin(seconds * 5 + oldBlocks.keys[index] % 7) * 0.02;
        keep(oldList, index, x + WIND.x * 0.14 * seconds + sway, fallenY, z + WIND.z * 0.14 * seconds);
        continue;
      }
      if (since < GROW_SHARE) {
        const bottom = Math.floor(y / VOXEL) * VOXEL;
        keep(oldList, index, x, bottom + (y - bottom) * (1 - since / GROW_SHARE), z);
      }
    }
    for (let index = 0; index < newList.count; index++) {
      const since = turn.progress - newMoments[index];
      if (since < 0) continue;
      const x = newList.positions[index * 3];
      const y = newList.positions[index * 3 + 1];
      const z = newList.positions[index * 3 + 2];
      const sprouting = since < GROW_SHARE && !oldBlocks.present.has(newBlocks.keys[index]);
      if (sprouting) {
        const bottom = Math.floor(y / VOXEL) * VOXEL;
        keep(newList, index, x, bottom + (y - bottom) * (since / GROW_SHARE), z);
      } else {
        keep(newList, index, x, y, z);
      }
    }
    return {
      count: scales.length,
      positions: new Float32Array(positions),
      colors: new Float32Array(colors),
      scales: new Float32Array(scales),
    };
  }

  const scene = {
    name: 'cycle',
    palette: seasons[0].palette,
    background: { ...seasons[0].background },
    camera: seasons[0].camera,
    staticLists: [],
    dynamic(time) {
      const turn = seasonAt(time);
      const from = seasons[turn.from];
      const to = seasons[turn.to];
      const mix = turn.progress;
      scene.palette = mix > 0 ? [...from.palette, ...to.palette] : from.palette;
      const background = from.backgroundColor.map((value, channel) => value + (to.backgroundColor[channel] - value) * mix);
      scene.background = { inner: background, outer: background, stars: false };
      const parts = mix > 0
        ? PART_NAMES.map(partName => blendPart(partName, turn))
        : PART_NAMES.map(partName => from.parts[partName]);
      const sway = from.swayAmount + (to.swayAmount - from.swayAmount) * mix;
      parts[2] = swayTree(parts[2], time, sway);
      const effectPoints = [...from.effects(time, 1 - mix), ...to.effects(time, mix)];
      return [...parts, packPoints(effectPoints)];
    },
    glows() {
      return [];
    },
    contactShadows() {
      return [];
    },
  };
  return scene;
}
