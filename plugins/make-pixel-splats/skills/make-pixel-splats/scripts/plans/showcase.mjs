// Showcase cut of the windmill (no tutorial): one continuous camera move, push in, drift round, pull back.
// Preview: SHOWCASE_GRID=200 SHOWCASE_SPACING=0.006. Final: 400 and 0.003.
const grid = Number(process.env.SHOWCASE_GRID ?? 200);
const spacing = Number(process.env.SHOWCASE_SPACING ?? 0.006);
const framesPerSecond = Number(process.env.SHOWCASE_FPS ?? 24);
const duration = 15;
const upscale = 1200 / grid;

const ink = { ink: true, supersample: 2, inkContourStrength: 1, inkDither: 0.08 };
const ease = amount => {
  const clamped = Math.min(Math.max(amount, 0), 1);
  return clamped * clamped * (3 - 2 * clamped);
};

function cameraAt(time) {
  const progress = time / duration;
  // Angle sweeps steadily; zoom and height breathe in and out so the move never feels like a turntable.
  const angleOffset = -0.38 + 0.8 * progress;
  const zoom = 1.12 - 0.12 * ease(time / 6) + 0.1 * ease((time - 9) / 6);
  const heightOffset = -0.25 * ease(time / 6) + 0.2 * ease((time - 9) / 6);
  const targetOffset = [0.04 * ease(time / 6), 0.08 * ease(time / 6) - 0.06 * ease((time - 9) / 6), 0];
  return { orbitSpeed: 0, angleOffset, zoom, heightOffset, targetOffset };
}

export const frames = Array.from({ length: duration * framesPerSecond }, (unused, index) => {
  const time = index / framesPerSecond;
  return {
    file: `showcase/f_${String(index).padStart(4, '0')}.png`,
    scene: 'windmill',
    spacing,
    options: { time: time + 2, internalSize: grid, outputSize: grid * upscale, style: ink, camera: cameraAt(time) },
  };
});
