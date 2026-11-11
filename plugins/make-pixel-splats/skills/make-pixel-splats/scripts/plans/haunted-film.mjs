// 24 s haunted medieval triptych in look C, cut on lightning:
//   chapel crag (splats rain in, ghost rises) -> flash -> witch's swamp (push into the cauldron until single splats
//   show) -> flash -> gallows crossroads (the Reaper's eyes ignite, he raises the scythe and slashes, the bolt hits,
//   everything breaks into ash and goes black).
// Camera moves are eased keyframes with a little handheld drift, never a constant orbit.
// Environment: FILM_FPS, FILM_SIZE (output pixels), FILM_UNTIL (seconds).
import { REAPER_TIMING, GALLOWS_BOLTS } from '../medieval2.js';

const framesPerSecond = Number(process.env.FILM_FPS ?? 30);
const outputSize = Number(process.env.FILM_SIZE ?? 1080);
const untilSeconds = Number(process.env.FILM_UNTIL ?? 99);
const internalBase = 360;
const style = { dither: 0.06, paletteSteps: 3 };

const clamp = value => Math.min(Math.max(value, 0), 1);
const easeInOut = value => {
  const amount = clamp(value);
  return amount < 0.5 ? 4 * amount ** 3 : 1 - (-2 * amount + 2) ** 3 / 2;
};
const easeOut = value => 1 - (1 - clamp(value)) ** 3;
const pulse = (time, at, width) => Math.max(0, 1 - Math.abs(time - at) / width);
const mix = (from, to, amount) => from + (to - from) * amount;
const drift = (time, seed) => Math.sin(time * 0.9 + seed) * 0.6 + Math.sin(time * 2.3 + seed * 2) * 0.4;

const CUT_TO_SWAMP = 8.15;
const CUT_TO_GALLOWS = 15.6;
export const DURATION = 24;

function chapelShot(localTime) {
  const move = easeInOut(localTime / 8.2);
  return {
    scene: 'medieval', sceneTime: localTime,
    assemble: clamp(localTime / 2.8),
    camera: {
      orbitSpeed: 0,
      angleOffset: mix(-0.55, 0.35, move) + drift(localTime, 1) * 0.01,
      zoom: mix(1.15, 0.97, move),
      heightOffset: mix(0.25, -0.1, move) + drift(localTime, 2) * 0.008,
      targetOffset: [0, mix(0, 0.05, move), 0],
    },
  };
}

function swampShot(localTime) {
  // Settle in from a low close angle, hold, then push into the cauldron while the resolution climbs.
  const settle = easeOut(localTime / 2.2);
  const push = easeInOut((localTime - 4.3) / 2.6);
  const reveal = easeInOut((localTime - 4.9) / 1.6);
  const cauldron = [0.22, 0.16, 0.42];
  const target = [0.05, 0.32, 0.05];
  return {
    scene: 'swamp', sceneTime: localTime + 1.5,
    reveal,
    camera: {
      orbitSpeed: 0,
      angleOffset: mix(0.55, 0.0, settle) + mix(0, 0.35, push) + drift(localTime, 4) * 0.012,
      zoom: mix(0.78, 0.95, settle) * mix(1, 0.32, push),
      heightOffset: mix(-0.5, -0.05, settle) + mix(0, -0.55, push) + drift(localTime, 5) * 0.01,
      targetOffset: [(cauldron[0] - target[0]) * push, (cauldron[1] - target[1]) * push, (cauldron[2] - target[2]) * push],
    },
  };
}

function gallowsShot(localTime) {
  const { eyes, slash } = REAPER_TIMING;
  const approach = easeInOut(localTime / (slash - 0.2));
  const jolt = Math.exp(-Math.max(localTime - slash, 0) * 9) * (localTime > slash ? 1 : 0);
  const pullBack = easeInOut((localTime - slash - 0.5) / 1.6);
  const reaperHead = [0.32, 0.6, 0.22];
  const target = [0.05, 0.5, 0.05];
  const toward = clamp(approach - pullBack);
  const holdBreath = eyes < localTime ? 0 : drift(localTime, 7) * 0.01;
  return {
    scene: 'gallows', sceneTime: localTime,
    dissolve: easeInOut((localTime - slash - 0.35) / 2.1) * 1.1,
    fadeToBlack: easeInOut((localTime - (DURATION - CUT_TO_GALLOWS) + 0.9) / 0.8),
    camera: {
      orbitSpeed: 0,
      angleOffset: mix(-0.35, 0.15, approach) + holdBreath + Math.sin(localTime * 60) * 0.02 * jolt,
      zoom: mix(1.02, 0.5, toward),
      heightOffset: mix(0.2, -0.6, toward) + Math.sin(localTime * 47) * 0.03 * jolt,
      targetOffset: [(reaperHead[0] - target[0]) * toward * 0.8, (reaperHead[1] - target[1]) * toward * 0.6, (reaperHead[2] - target[2]) * toward * 0.8],
    },
  };
}

function flashAt(time) {
  const strikes = [
    [CUT_TO_SWAMP - 0.05, 1], [CUT_TO_SWAMP + 0.18, 0.55],
    [CUT_TO_GALLOWS - 0.05, 1], [CUT_TO_GALLOWS + 0.2, 0.5],
    ...GALLOWS_BOLTS.map(boltTime => [CUT_TO_GALLOWS + boltTime, 0.9]),
  ];
  return Math.max(0, ...strikes.map(([at, strength]) => strength * pulse(time, at, 0.12)));
}

export const frames = [];
const totalFrames = Math.round(DURATION * framesPerSecond);
for (let frameIndex = 0; frameIndex < totalFrames; frameIndex++) {
  const time = frameIndex / framesPerSecond;
  if (time >= untilSeconds) break;
  const shot = time < CUT_TO_SWAMP ? chapelShot(time) : time < CUT_TO_GALLOWS ? swampShot(time - CUT_TO_SWAMP) : gallowsShot(time - CUT_TO_GALLOWS);
  const reveal = shot.reveal ?? 0;
  const internalSize = Math.round((internalBase + (1080 - internalBase) * reveal) / 8) * 8;
  frames.push({
    file: `frame_${String(frameIndex).padStart(4, '0')}.png`, scene: shot.scene, spacing: 0.015,
    options: {
      time: shot.sceneTime,
      outputSize,
      internalSize,
      style: reveal > 0.75 ? { palette: 'none' } : style,
      assemble: shot.assemble ?? 1,
      dissolve: shot.dissolve ?? 0,
      fadeToBlack: shot.fadeToBlack ?? 0,
      flash: flashAt(time),
      camera: shot.camera,
    },
  });
}
