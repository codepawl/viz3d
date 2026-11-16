// Detail levels for An to pick: art grid and splat spacing rise together; every frame comes out at 1200 px with a
// whole-number upscale, so pixels stay square and the comparison is fair.
const ink = { ink: true, supersample: 2, inkContourStrength: 1, inkDither: 0.08 };
const levels = [[200, 0.006], [240, 0.005], [300, 0.004], [400, 0.003]];
export const frames = levels.map(([grid, spacing]) => ({
  file: `density/grid_${grid}.png`,
  scene: 'windmill',
  spacing,
  options: { time: 1.5, internalSize: grid, outputSize: 1200, style: ink, camera: { orbitSpeed: 0 } },
}));
