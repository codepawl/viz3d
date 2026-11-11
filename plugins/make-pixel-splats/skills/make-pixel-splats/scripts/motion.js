// Timing helpers so motion has rhythm: easing, walk-then-pause steps, struck-and-decaying swings, smooth noise.
export const clamp01 = value => Math.min(Math.max(value, 0), 1);
export const easeInOutCubic = value => {
  const amount = clamp01(value);
  return amount < 0.5 ? 4 * amount * amount * amount : 1 - Math.pow(-2 * amount + 2, 3) / 2;
};
export const easeOutCubic = value => 1 - Math.pow(1 - clamp01(value), 3);
export const easeInCubic = value => Math.pow(clamp01(value), 3);
export const easeOutBack = (value, overshoot = 1.7) => {
  const amount = clamp01(value) - 1;
  return 1 + (overshoot + 1) * amount * amount * amount + overshoot * amount * amount;
};

// Moves for `moveShare` of each period with an ease in and out, then holds still: returns the progress and whether moving.
export function stepAndHold(time, period, moveShare) {
  const cycles = time / period;
  const whole = Math.floor(cycles);
  const within = (cycles - whole) / moveShare;
  return { progress: whole + easeInOutCubic(within), moving: within > 0 && within < 1, within: clamp01(within) };
}

// A pendulum struck every `period` seconds that rings down.
export function struckSwing(time, period, amplitude, frequency, damping, offset = 0) {
  const since = ((time + offset) % period + period) % period;
  return amplitude * Math.exp(-since * damping) * Math.sin(since * frequency);
}

// Smooth 1D noise from a few sines, in about -1..1.
export function wobble(time, seed) {
  return (Math.sin(time * 0.71 + seed * 3.1) * 0.5 + Math.sin(time * 1.37 + seed * 1.7) * 0.3 + Math.sin(time * 2.83 + seed * 5.3) * 0.2);
}
