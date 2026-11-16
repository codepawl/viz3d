// 12 s loop of Pocket Seasons with the seasons turning in place (season-cycle.js): each season holds 1.5 s, then
// turns into the next for 1.5 s, winter back into spring so the clip loops. 360 px internal, 4x out (1440), crisp
// style, slow eased orbit. Env FILM_UNTIL cuts it short for tests; FILM_STEP renders every Nth frame.
import { CYCLE_SECONDS } from '../season-cycle.js';

const fps = 24;
const style = { dither: 0, paletteSteps: 1, supersample: 4, alphaCut: 0.5 };
const until = Number(process.env.FILM_UNTIL ?? CYCLE_SECONDS);
const step = Number(process.env.FILM_STEP ?? 1);
export const frames = [];
for (let index = 0; index < Math.round(until * fps); index += step) {
  const time = index / fps;
  const swing = Math.sin((time / CYCLE_SECONDS) * Math.PI * 2);
  frames.push({
    file: `frame_${String(index).padStart(4, '0')}.png`,
    scene: process.env.CYCLE_LOOK ? `cycle:${process.env.CYCLE_LOOK}` : 'cycle',
    spacing: 0.0075,
    options: { time, internalSize: 360, outputSize: 1440, style, camera: { orbitSpeed: 0, angleOffset: swing * 0.1 } },
  });
}
