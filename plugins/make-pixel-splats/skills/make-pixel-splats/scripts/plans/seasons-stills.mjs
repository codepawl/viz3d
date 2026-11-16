// One still per season in the crisp look (internal 200 px, integer upscale to 1000 px, no haze or glow).
export const frames = ['spring', 'summer', 'autumn', 'winter'].map(scene => ({
  file: `${scene}.png`, scene, spacing: 0.016,
  options: { time: 3, internalSize: 200, outputSize: 1600, style: { dither: 0, paletteSteps: 1, supersample: 4, alphaCut: 0.5 }, camera: { orbitSpeed: 0 } },
}));
