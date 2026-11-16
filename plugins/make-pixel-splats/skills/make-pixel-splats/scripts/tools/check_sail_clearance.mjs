// Turns the windmill sails through a full revolution and reports how close any sail splat comes to the static world
// (tower, gallery, ground, props). A negative clearance means the sails cut through something.
// Usage: node tools/check_sail_clearance.mjs [spacing]
import { buildWindmill, windmillClearance } from '../windmill.js';

const spacing = Number(process.argv[2] ?? 0.012);
const scene = buildWindmill(spacing);
const sails = scene.sails;
// Skip the hub and shaft root, which are meant to sit in the cap.
const hubRadius = 0.13;
let worst = { clearance: Infinity };
for (let step = 0; step < 72; step++) {
  const angle = step / 72 * Math.PI * 2;
  const turned = scene.dynamic((angle - 0.35) / 0.6)[0];
  for (let index = 0; index < sails.count; index++) {
    const localX = sails.positions[index * 3];
    const localY = sails.positions[index * 3 + 1];
    if (Math.hypot(localX, localY) < hubRadius) continue;
    const x = turned.positions[index * 3];
    const y = turned.positions[index * 3 + 1];
    const z = turned.positions[index * 3 + 2];
    const clearance = windmillClearance.worldDistance(x, y, z);
    if (clearance < worst.clearance) worst = { clearance, angleDegrees: Math.round(angle * 180 / Math.PI), point: [x, y, z].map(value => +value.toFixed(3)) };
  }
}
console.log('sail splats', sails.count, 'worst clearance', worst.clearance.toFixed(4), 'at', worst.angleDegrees, 'deg', worst.point);
process.exit(worst.clearance > spacing * 0.5 ? 0 : 1);
