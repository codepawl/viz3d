// One still of each scene in look A (216 px) and look C (360 px). Run: node render.mjs plans/stills.mjs out/stills
const looks = {
  a: { internalSize: 216, spacing: 0.02, style: { dither: 0.12 } },
  c: { internalSize: 360, spacing: 0.015, style: { dither: 0.06, paletteSteps: 3 } },
};
export const frames = [];
for (const scene of ['medieval', 'swamp', 'gallows', 'lighthouse', 'snail', 'koi']) {
  for (const [name, look] of Object.entries(looks)) {
    frames.push({ file: `${scene}_${name}.png`, scene, spacing: look.spacing,
      options: { time: 5, internalSize: look.internalSize, outputSize: 1080, style: look.style, camera: { orbitSpeed: 0 } } });
  }
}
