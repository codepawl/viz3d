// Picture layers for the "how pixel-splat art is made" film (beats in notes/howto-video.md). Each frame renders only
// the layers its beat needs; tools/howto_compose.py stacks them with labels, swatches, the sample-grid zoom and the
// before/after wipe. Preview: HOWTO_GRID=200 HOWTO_SPACING=0.006. Final: 400 and 0.003.
const grid = Number(process.env.HOWTO_GRID ?? 200);
const spacing = Number(process.env.HOWTO_SPACING ?? 0.006);
const framesPerSecond = Number(process.env.HOWTO_FPS ?? 24);
const duration = 36;
const upscale = 3;

const ink = { ink: true, supersample: 2, inkContourStrength: 1, inkDither: 0.08 };
const raw = { ink: true, supersample: 2, inkPalette: false, inkContour: false };
// Slow orbit, frozen during the zoom beat (19-25 s) so the before and after of the resolve show the same spot.
const orbitSpeed = 0.035;
const orbitTime = time => (time < 19 ? time : time < 25 ? 19 : time - 6);
const cameraAt = time => ({ orbitSpeed: 0, angleOffset: orbitSpeed * orbitTime(time) });
const smooth = amount => {
  const clamped = Math.min(Math.max(amount, 0), 1);
  return clamped * clamped * (3 - 2 * clamped);
};

function layersAt(time) {
  if (time < 3) return ['ink'];
  if (time < 8) return ['clay'];
  if (time < 13) return ['clay'];
  if (time < 19) return ['raw'];
  if (time < 25) return time < 22 ? ['samples'] : ['samples', 'ink'];
  if (time < 31) return ['raw', 'ink'];
  return ['ink'];
}

function optionsFor(layer, time) {
  const base = { time, internalSize: grid, outputSize: grid * upscale, camera: cameraAt(time) };
  if (layer === 'ink') return { ...base, style: ink };
  if (layer === 'raw') return { ...base, style: raw };
  if (layer === 'samples') return { ...base, internalSize: grid * 2, outputSize: grid * 2 * upscale, style: raw };
  // Clay: shapes assemble first, then the surface is shown as sparse dots filling in to a dense skin.
  const assemble = time < 8 ? 0.35 + 0.65 * smooth((time - 3.2) / 2.6) : 1;
  const splatKeep = time < 8 ? 1 : 0.004 + 0.996 * Math.pow(smooth((time - 8.5) / 4.2), 3);
  return { ...base, style: raw, look: 'clay', assemble, splatKeep };
}

export const frames = [];
const totalFrames = Math.round(duration * framesPerSecond);
const onlyLayer = process.env.HOWTO_LAYER ?? null;
for (let frameIndex = 0; frameIndex < totalFrames; frameIndex++) {
  const time = frameIndex / framesPerSecond;
  for (const layer of layersAt(time)) {
    if (onlyLayer && layer !== onlyLayer) continue;
    frames.push({
      file: `howto/${layer}/f_${String(frameIndex).padStart(4, '0')}.png`,
      scene: 'windmill',
      spacing,
      options: optionsFor(layer, time),
    });
  }
}
