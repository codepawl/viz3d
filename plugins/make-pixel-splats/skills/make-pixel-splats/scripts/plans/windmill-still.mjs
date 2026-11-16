// Windmill style frame: ink look vs raw splats at the same camera, 400 px art grid, 3x out.
const ink = { ink: true, supersample: 2, inkContourStrength: 1, inkDither: 0.08 };
const raw = { ink: true, supersample: 2, inkPalette: false, inkContour: false };
export const frames = [
  { file: 'windmill_ink.png', scene: 'windmill', spacing: 0.003, options: { time: 0, internalSize: 400, outputSize: 1200, style: ink, camera: { orbitSpeed: 0 } } },
];
