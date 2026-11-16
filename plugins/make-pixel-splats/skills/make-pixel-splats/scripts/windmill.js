// Windmill farm diorama, rebuilt from scratch after JungleSilicon's pixel-splat windmill on X to show how
// those pieces are made: SDF shapes, one dark-to-light colour ramp per material, half-Lambert ramp shading with
// jitter, then the ink resolve in page.js. Y is up; the island top sits at y = 0.
import {
  valueNoise, hashNoise, sphereDistance, boxDistance, cylinderDistance, taperedCylinderDistance, capsuleDistance,
  islandDistance, voxelizeModel,
} from './voxel-splats.js';

const hex = value => [parseInt(value.slice(1, 3), 16) / 255, parseInt(value.slice(3, 5), 16) / 255, parseInt(value.slice(5, 7), 16) / 255];

// Index 0 is the background. Shadows of the warm materials fall into the blues, as in the reference.
export const WINDMILL_PALETTE_HEX = [
  '#080a16', '#141a33', '#232f5c', '#3a4d8a', '#6079b8', '#9fb2dc',
  '#4a2c18', '#7a4a22', '#a8692c', '#d39a32', '#f0c860', '#fff0c0', '#e0a070',
];
const PALETTE = WINDMILL_PALETTE_HEX.map(hex);
const ramp = (...indices) => indices.map(index => PALETTE[index]);
const RAMPS = {
  tower: ramp(1, 2, 3, 4, 5),
  cap: ramp(1, 2, 3, 4),
  wheat: ramp(1, 6, 7, 8, 9),
  ripe: ramp(2, 9, 10, 11),
  stubble: ramp(1, 2, 6, 7, 8),
  rock: ramp(1, 2, 7, 8, 9),
  rockBlue: ramp(1, 1, 2, 3, 4),
  hay: ramp(6, 7, 8, 9, 10),
  panel: ramp(7, 8, 9, 10, 11),
  panelRot: ramp(1, 6, 7, 8),
  towerDark: ramp(1, 1, 2, 3, 4),
  water: ramp(2, 3, 4, 5),
  plaster: ramp(3, 12, 11, 11),
  thatch: ramp(6, 7, 8, 9),
  path: ramp(1, 6, 7, 12),
  plank: ramp(6, 7, 8, 9),
  spar: ramp(1, 6, 7, 8),
  wood: ramp(1, 6, 7, 8),
  coat: ramp(1, 2, 3, 4),
  skin: ramp(7, 8, 12),
  glow: ramp(10, 11),
};
// mottle scales the broad wear patches of ramp shading for this material (light.rampMottle sets the base).
const surface = (rampColors, glow = false, mottle = 1) => Object.assign([0, 0, 0, 0, 1], { ramp: rampColors, glow, mottle });

export const WINDMILL_CAMERA_ANGLE = 0.75;
const TOWER = { x: 0.35, z: -0.2, bottomRadius: 0.3, topRadius: 0.17, height: 1.05 };
const SAIL_AXIS_YAW = WINDMILL_CAMERA_ANGLE - 0.7;
const AXIS = [Math.sin(SAIL_AXIS_YAW), 0, Math.cos(SAIL_AXIS_YAW)];
const SIDE = [AXIS[2], 0, -AXIS[0]];
const HUB_HEIGHT = 0.98;
const towerRadiusAt = height => TOWER.bottomRadius + (TOWER.topRadius - TOWER.bottomRadius) * (height / TOWER.height);
// Like a real mill, the sails clear the tapering tower and its gallery two ways: a long windshaft holds them well out
// from the cap, and the shaft tilts up at the front so the sail plane leans back and the lower tips swing outward
// (an earlier lower arm cut through the gallery).
const SHAFT_REACH = 0.1;
const SHAFT_TILT = 0.12;
const HUB = [TOWER.x + AXIS[0] * (towerRadiusAt(HUB_HEIGHT) + SHAFT_REACH), HUB_HEIGHT, TOWER.z + AXIS[2] * (towerRadiusAt(HUB_HEIGHT) + SHAFT_REACH)];
// Tilted sail frame: SAIL_UP is the sail plane's up direction, SAIL_AXIS the shaft pointing out of the plane.
const SAIL_UP = [-AXIS[0] * Math.sin(SHAFT_TILT), Math.cos(SHAFT_TILT), -AXIS[2] * Math.sin(SHAFT_TILT)];
const SAIL_AXIS = [AXIS[0] * Math.cos(SHAFT_TILT), Math.sin(SHAFT_TILT), AXIS[2] * Math.cos(SHAFT_TILT)];

// A box turned about Y by yaw (its local x points along [cos yaw, -sin yaw] in x, z).
function yawBoxDistance(x, y, z, centerX, centerY, centerZ, yaw, halfX, halfY, halfZ, rounding = 0) {
  const offsetX = x - centerX;
  const offsetZ = z - centerZ;
  const localX = offsetX * Math.cos(yaw) - offsetZ * Math.sin(yaw);
  const localZ = offsetX * Math.sin(yaw) + offsetZ * Math.cos(yaw);
  return boxDistance(localX, y, localZ, 0, centerY, 0, halfX, halfY, halfZ, rounding);
}

// Screen directions from the camera angle: RIGHT points to the right of the frame, FRONT towards the viewer.
const RIGHT = [Math.cos(WINDMILL_CAMERA_ANGLE), -Math.sin(WINDMILL_CAMERA_ANGLE)];
const FRONT = [Math.sin(WINDMILL_CAMERA_ANGLE), Math.cos(WINDMILL_CAMERA_ANGLE)];
const onScreen = (right, front) => [RIGHT[0] * right + FRONT[0] * front, RIGHT[1] * right + FRONT[1] * front];

const FIELD_WHEAT = { x: -0.09, z: 0.55, halfX: 0.4, halfZ: 0.27 };

function fieldDistance(x, y, z, field, height) {
  const bound = boxDistance(x, y, z, field.x, height / 2, field.z, field.halfX, height / 2, field.halfZ, 0.02);
  if (bound > 0.08) return bound - 0.06;
  // Stalk clumps: a fine cell noise lifts the top into tufts, rows run across the field.
  // A low-frequency term makes trampled and flattened patches, so the field is not one even slab.
  const tufts = (valueNoise(x * 60, 3.1, z * 60) - 0.5) * 0.05 + Math.sin(x * 55 + valueNoise(z * 8, 0, 0) * 3) * 0.008
    + (valueNoise(x * 7, 8.2, z * 7) - 0.5) * 0.05;
  return boxDistance(x, y, z, field.x, height / 2, field.z, field.halfX, height / 2 + tufts, field.halfZ, 0.02);
}

const islandModelDistance = (x, y, z) => islandDistance(x, y, z, 1.0, 0.85, 0, 0.1);

const towerDistance = (x, y, z) => {
  // Hand-laid stone: the wall bulges and dips a little, and each course sits slightly proud or recessed.
  const smoothBody = taperedCylinderDistance(x, y, z, TOWER.x, 0, TOWER.z, TOWER.bottomRadius, TOWER.topRadius, TOWER.height);
  const wallBumps = smoothBody > 0.04 ? 0 : (valueNoise(x * 16, y * 16, z * 16) - 0.5) * 0.016
    + (hashNoise(Math.floor(y / 0.075), 1.7, 0.3) - 0.5) * 0.008;
  const body = smoothBody - wallBumps;
  const plinth = cylinderDistance(x, y, z, TOWER.x, 0, TOWER.z, TOWER.bottomRadius + 0.035, 0.07);
  const capRing = cylinderDistance(x, y, z, TOWER.x, TOWER.height - 0.02, TOWER.z, TOWER.topRadius + 0.035, 0.04);
  const cap = taperedCylinderDistance(x, y, z, TOWER.x, TOWER.height + 0.02, TOWER.z, TOWER.topRadius + 0.03, 0.0, 0.3);
  const finial = Math.min(
    sphereDistance(x, y, z, TOWER.x, TOWER.height + 0.34, TOWER.z, 0.028),
    capsuleDistance(x, y, z, TOWER.x, TOWER.height + 0.3, TOWER.z, TOWER.x, TOWER.height + 0.44, TOWER.z, 0.009),
  );
  const doorCenter = towerRadiusAt(0.12) + 0.01;
  const door = yawBoxDistance(x, y, z, TOWER.x + Math.sin(WINDMILL_CAMERA_ANGLE) * doorCenter, 0.13, TOWER.z + Math.cos(WINDMILL_CAMERA_ANGLE) * doorCenter,
    -Math.atan2(Math.cos(WINDMILL_CAMERA_ANGLE), Math.sin(WINDMILL_CAMERA_ANGLE)) + Math.PI / 2, 0.065, 0.13, 0.03, 0.01);
  return Math.min(body, plinth, capRing, cap, finial, door);
};

const WINDOWS = [
  { height: 0.55, angle: WINDMILL_CAMERA_ANGLE - 0.9 },
  { height: 0.78, angle: WINDMILL_CAMERA_ANGLE + 0.55 },
  { height: 0.32, angle: WINDMILL_CAMERA_ANGLE + 0.95 },
];
const windowDistance = (x, y, z) => {
  let best = Infinity;
  for (const window of WINDOWS) {
    const radius = towerRadiusAt(window.height) + 0.004;
    const centerX = TOWER.x + Math.sin(window.angle) * radius;
    const centerZ = TOWER.z + Math.cos(window.angle) * radius;
    best = Math.min(best, yawBoxDistance(x, y, z, centerX, window.height, centerZ, -window.angle, 0.035, 0.05, 0.02));
  }
  return best;
};

// Round bales lying on their side, right-front of the tower: [right, front, yaw].
// [right, front, yaw, radius]: sizes differ and the straw is lumpy, so they read as baled by hand, not printed.
const HAY_BALES = [[0.75, 0.35, 0.4, 0.092]]
  .map(([right, front, yaw, radius]) => [...onScreen(right, front), yaw, radius]);
const hayDistance = (x, y, z) => {
  let best = Infinity;
  for (const [baleX, baleZ, yaw, radius] of HAY_BALES) {
    const offsetX = x - baleX;
    const offsetZ = z - baleZ;
    const along = offsetX * Math.cos(yaw) - offsetZ * Math.sin(yaw);
    const across = offsetX * Math.sin(yaw) + offsetZ * Math.cos(yaw);
    // Sagged a little: the bale squats under its own weight.
    const radial = Math.hypot(across, (y - radius * 0.94) * 1.07) - radius;
    const flat = Math.abs(along) - radius * 0.85;
    const smooth = Math.min(Math.max(radial, flat), 0) + Math.hypot(Math.max(radial, 0), Math.max(flat, 0)) - 0.006;
    const lumps = smooth > 0.03 ? 0 : (valueNoise(x * 70, y * 70, z * 70) - 0.5) * 0.012;
    best = Math.min(best, smooth - lumps);
  }
  return best;
};

const FARMER = { x: 0.14, z: 0.6 };
const farmerParts = (x, y, z) => ({
  coat: capsuleDistance(x, y, z, FARMER.x, 0.08, FARMER.z, FARMER.x, 0.26, FARMER.z, 0.05),
  head: sphereDistance(x, y, z, FARMER.x, 0.34, FARMER.z, 0.042),
  hat: Math.min(cylinderDistance(x, y, z, FARMER.x, 0.365, FARMER.z, 0.085, 0.012), cylinderDistance(x, y, z, FARMER.x, 0.365, FARMER.z, 0.045, 0.055)),
});
const farmerDistance = (x, y, z) => {
  const parts = farmerParts(x, y, z);
  return Math.min(parts.coat, parts.head, parts.hat);
};

// ---- Our own additions, so the piece is ours and not a copy of the reference: a thatched cottage with a smoking
// chimney where the reference has a second field, a pond whose stream spills off the island as a waterfall, a wooden
// gallery round the tower (smock-mill style), a hay cart instead of a row of bales, and a dirt path instead of a fence.
// Local x is the gable span, local z the ridge, pointing roughly at the camera so the gable end faces the viewer.
const COTTAGE = { x: -0.77, z: -0.03, yaw: WINDMILL_CAMERA_ANGLE + 0.3, halfLength: 0.1, halfWidth: 0.15, wallHeight: 0.15, ridge: 0.33 };
const toLocal = (x, z, centerX, centerZ, yaw) => {
  const offsetX = x - centerX;
  const offsetZ = z - centerZ;
  return [offsetX * Math.cos(yaw) - offsetZ * Math.sin(yaw), offsetX * Math.sin(yaw) + offsetZ * Math.cos(yaw)];
};
const fromLocal = (localX, localZ, centerX, centerZ, yaw) => [
  centerX + localX * Math.cos(yaw) + localZ * Math.sin(yaw),
  centerZ - localX * Math.sin(yaw) + localZ * Math.cos(yaw),
];
const CHIMNEY_LOCAL = [0.04, -COTTAGE.halfWidth * 0.55];
const CHIMNEY_TOP = [...fromLocal(CHIMNEY_LOCAL[0], CHIMNEY_LOCAL[1], COTTAGE.x, COTTAGE.z, COTTAGE.yaw), 0.4];

const FAR_PARTS = { walls: Infinity, roof: Infinity, chimney: Infinity, door: Infinity, window: Infinity, wood: Infinity, wheels: Infinity, heap: Infinity };
function cottageParts(x, y, z) {
  const reach = Math.hypot(x - COTTAGE.x, y - 0.2, z - COTTAGE.z) - 0.34;
  if (reach > 0.02) return { ...FAR_PARTS, walls: reach };
  const [localX, localZ] = toLocal(x, z, COTTAGE.x, COTTAGE.z, COTTAGE.yaw);
  const box = boxDistance(localX, y, localZ, 0, COTTAGE.wallHeight / 2, 0, COTTAGE.halfLength, COTTAGE.wallHeight / 2, COTTAGE.halfWidth, 0.006);
  // Gable roof: a slab bounded by two slopes, overhanging the walls, lumpy like old thatch.
  const roofRise = COTTAGE.ridge - COTTAGE.wallHeight;
  const roofHalfSpan = COTTAGE.halfLength + 0.03;
  const slope = roofRise / roofHalfSpan;
  const underSlope = (y - COTTAGE.wallHeight) - (roofRise - Math.abs(localX) * slope);
  const slopeNormal = Math.hypot(1, slope);
  const roofOuter = underSlope / slopeNormal;
  const roofInner = -(underSlope + 0.035) / slopeNormal;
  const roofEnds = Math.abs(localZ) - (COTTAGE.halfWidth + 0.025);
  const roofBottom = COTTAGE.wallHeight - 0.02 - y;
  const gable = Math.max(underSlope / slopeNormal, Math.abs(localZ) - COTTAGE.halfWidth, Math.abs(localX) - COTTAGE.halfLength, COTTAGE.wallHeight - 0.01 - y);
  const roof = Math.max(roofOuter, roofInner, roofEnds, roofBottom) - (valueNoise(x * 45, y * 45, z * 45) - 0.5) * 0.008;
  const walls = Math.min(box, gable) - (valueNoise(x * 30, y * 30, z * 30) - 0.5) * 0.006;
  const chimney = boxDistance(localX, y, localZ, CHIMNEY_LOCAL[0], 0.28, CHIMNEY_LOCAL[1], 0.024, 0.12, 0.024, 0.003);
  const window = boxDistance(localX, y, localZ, 0.0, 0.22, COTTAGE.halfWidth + 0.003, 0.018, 0.02, 0.005);
  const door = boxDistance(localX, y, localZ, -0.035, 0.055, COTTAGE.halfWidth + 0.004, 0.024, 0.055, 0.006);
  const sideWindow = boxDistance(localX, y, localZ, 0.05, 0.085, COTTAGE.halfWidth + 0.003, 0.018, 0.02, 0.005);
  return { walls, roof, chimney, door, window: Math.min(window, sideWindow) };
}
const cottageDistance = (x, y, z) => {
  const parts = cottageParts(x, y, z);
  return Math.min(parts.walls, parts.roof, parts.chimney, parts.door, parts.window);
};

// Pond and stream: carved into the island, water surface just under the rim, stream running out to the edge.
const POND = { x: 0.6, z: 0.5, radiusX: 0.15, radiusZ: 0.1 };
const STREAM_DIRECTION = (() => {
  const length = Math.hypot(POND.x, POND.z);
  return [POND.x / length, POND.z / length];
})();
const STREAM_END = [POND.x + STREAM_DIRECTION[0] * 0.24, POND.z + STREAM_DIRECTION[1] * 0.24];
const WATER_LEVEL = -0.014;
const pondPlan = (x, z) => (Math.hypot((x - POND.x) / POND.radiusX, (z - POND.z) / POND.radiusZ) - 1) * Math.min(POND.radiusX, POND.radiusZ);
const streamPlan = (x, z) => {
  const alongX = STREAM_END[0] - POND.x;
  const alongZ = STREAM_END[1] - POND.z;
  const amount = Math.min(Math.max(((x - POND.x) * alongX + (z - POND.z) * alongZ) / (alongX * alongX + alongZ * alongZ), 0), 1.3);
  const meander = Math.sin(amount * 9) * 0.012;
  return Math.hypot(x - POND.x - alongX * amount, z - POND.z - alongZ * amount) - 0.026 - meander;
};
const waterPlan = (x, z) => Math.min(pondPlan(x, z), streamPlan(x, z));
const waterHoleDistance = (x, y, z) => Math.max(waterPlan(x, z), -0.04 - y);
const waterDistance = (x, y, z) => Math.max(waterPlan(x, z) + 0.004, Math.abs(y - WATER_LEVEL) - 0.004);

// Wooden gallery round the tower at mid height, with a rail and posts.
const GALLERY_HEIGHT = 0.42;
const galleryDistance = (x, y, z) => {
  const radial = Math.hypot(x - TOWER.x, z - TOWER.z);
  const outer = towerRadiusAt(GALLERY_HEIGHT) + 0.075;
  const deck = Math.max(radial - outer, Math.abs(y - GALLERY_HEIGHT) - 0.012);
  const rail = Math.max(Math.abs(radial - outer + 0.008) - 0.007, Math.abs(y - GALLERY_HEIGHT - 0.07) - 0.007);
  const angle = Math.atan2(z - TOWER.z, x - TOWER.x);
  const postSpacing = Math.PI / 9;
  const postAngle = (((angle % postSpacing) + postSpacing) % postSpacing) - postSpacing / 2;
  const post = Math.max(Math.abs(postAngle * radial) - 0.007, Math.abs(radial - outer + 0.008) - 0.007, Math.abs(y - GALLERY_HEIGHT - 0.035) - 0.035);
  return Math.min(deck, rail, post);
};

// Hay cart: a plank bed on two spoked-looking wheels, a heap of hay, shafts resting on the ground.
const CART = { position: onScreen(0.5, 0.62), yaw: WINDMILL_CAMERA_ANGLE + 1.9 };
function cartParts(x, y, z) {
  const reach = Math.hypot(x - CART.position[0], y - 0.08, z - CART.position[1]) - 0.36;
  if (reach > 0.02) return { ...FAR_PARTS, wood: reach };
  const [localX, localZ] = toLocal(x, z, CART.position[0], CART.position[1], CART.yaw);
  const bed = boxDistance(localX, y, localZ, 0, 0.1, 0, 0.12, 0.012, 0.07, 0.003);
  const sides = Math.max(
    boxDistance(localX, y, localZ, 0, 0.125, 0, 0.12, 0.02, 0.07),
    -boxDistance(localX, y, localZ, 0, 0.135, 0, 0.11, 0.025, 0.06),
  );
  let wheels = Infinity;
  for (const side of [-1, 1]) {
    const radial = Math.hypot(localX, y - 0.075) - 0.075;
    const tyre = Math.max(Math.abs(radial + 0.007) - 0.009, Math.abs(localZ - side * 0.09) - 0.009);
    const hubDistance = Math.max(Math.hypot(localX, y - 0.075) - 0.015, Math.abs(localZ - side * 0.09) - 0.014);
    const spokeAngle = Math.atan2(y - 0.075, localX);
    const spokeCell = (((spokeAngle % (Math.PI / 3)) + Math.PI / 3) % (Math.PI / 3)) - Math.PI / 6;
    const spokes = Math.max(Math.abs(spokeCell) * Math.hypot(localX, y - 0.075) - 0.005, radial, Math.abs(localZ - side * 0.09) - 0.006);
    wheels = Math.min(wheels, tyre, hubDistance, spokes);
  }
  const shaftTilt = (localX + 0.11) * 0.5;
  const shafts = Math.min(
    boxDistance(localX, y + shaftTilt * -1, localZ, -0.2, 0.06, 0.045, 0.1, 0.007, 0.007),
    boxDistance(localX, y + shaftTilt * -1, localZ, -0.2, 0.06, -0.045, 0.1, 0.007, 0.007),
  );
  const heap = sphereDistance(localX * 0.85, (y - 0.13) * 1.6, localZ * 1.1, 0, 0, 0, 0.055) - (valueNoise(x * 60, y * 60, z * 60) - 0.5) * 0.012;
  return { wood: Math.min(bed, sides, shafts), wheels, heap };
}
const cartDistance = (x, y, z) => {
  const parts = cartParts(x, y, z);
  return Math.min(parts.wood, parts.wheels, parts.heap);
};

// Worn dirt path from the mill door to the cottage door.
const DOOR_FRONT = [TOWER.x + Math.sin(WINDMILL_CAMERA_ANGLE) * (TOWER.bottomRadius + 0.08), TOWER.z + Math.cos(WINDMILL_CAMERA_ANGLE) * (TOWER.bottomRadius + 0.08)];
const COTTAGE_DOOR = fromLocal(-0.035, COTTAGE.halfWidth + 0.06, COTTAGE.x, COTTAGE.z, COTTAGE.yaw);
const pathPlan = (x, z) => {
  const alongX = COTTAGE_DOOR[0] - DOOR_FRONT[0];
  const alongZ = COTTAGE_DOOR[1] - DOOR_FRONT[1];
  const amount = Math.min(Math.max(((x - DOOR_FRONT[0]) * alongX + (z - DOOR_FRONT[1]) * alongZ) / (alongX * alongX + alongZ * alongZ), 0), 1);
  const curve = Math.sin(amount * Math.PI) * 0.12;
  const width = 0.035 + (valueNoise(x * 20, 0, z * 20) - 0.5) * 0.02;
  return Math.hypot(x - DOOR_FRONT[0] - alongX * amount - curve * 0.7, z - DOOR_FRONT[1] - alongZ * amount - curve) - width;
};

const groundDistance = (x, y, z) => Math.max(
  Math.min(islandModelDistance(x, y, z), fieldDistance(x, y, z, FIELD_WHEAT, 0.1)),
  -waterHoleDistance(x, y, z),
);
const worldDistance = (x, y, z) => Math.min(groundDistance(x, y, z), towerDistance(x, y, z), windowDistance(x, y, z), hayDistance(x, y, z),
  farmerDistance(x, y, z), cottageDistance(x, y, z), galleryDistance(x, y, z), cartDistance(x, y, z), waterDistance(x, y, z));

// Sails in their own frame: local x along SIDE, y up, z along AXIS (towards the viewer); the hub is the origin.
const SAIL_LENGTH = 0.8;
// An old mill: no two arms match. Each arm is a little off square, a little short or long, warped out of plane, and
// its lattice has lost slats; arm 1 has a torn, ragged end and arm 3 a broken spar tip.
const ARMS = [
  { angleOffset: 0.0, length: 0.8, panelEnd: 0.78, warp: 0.05, missingSlats: 0.12, chippedTip: 0 },
  { angleOffset: 0.035, length: 0.78, panelEnd: 0.6, warp: -0.07, missingSlats: 0.3, chippedTip: 0 },
  { angleOffset: -0.025, length: 0.82, panelEnd: 0.76, warp: 0.03, missingSlats: 0.18, chippedTip: 0 },
  { angleOffset: 0.05, length: 0.66, panelEnd: 0.64, warp: 0.09, missingSlats: 0.22, chippedTip: 1 },
];
const CELL_ALONG = 0.06;
const CELL_ACROSS = 0.0567;

function armFrame(localX, localY, localZ, arm) {
  const armAngle = arm * Math.PI / 2 + ARMS[arm].angleOffset;
  const along = localX * Math.cos(armAngle) + localY * Math.sin(armAngle);
  const across = -localX * Math.sin(armAngle) + localY * Math.cos(armAngle);
  // Warp bends the arm out of the sail plane, more towards the tip.
  const bentZ = localZ - ARMS[arm].warp * Math.max(along - 0.1, 0) ** 2;
  return { along, across, bentZ };
}

// Panel end of one arm at a given across position: a ragged line, not a clean cut.
const panelEndAt = (arm, across) => ARMS[arm].panelEnd + (valueNoise(across * 45, arm * 7.1, 2.3) - 0.5) * (arm === 1 ? 0.14 : 0.03);

function sailArmDistance(along, across, bentZ, arm) {
  const settings = ARMS[arm];
  const sparHalf = settings.length / 2;
  let spar = boxDistance(along, across, bentZ, sparHalf + 0.02, 0, 0.035, sparHalf, 0.017, 0.016);
  if (settings.chippedTip) {
    // Broken end: a slanted cut through the spar tip.
    spar = Math.max(spar, (along - settings.length + 0.02) + across * 1.4);
  }
  const panelStart = 0.18;
  const end = panelEndAt(arm, across);
  const panelHalf = (end - panelStart) / 2;
  const panel = boxDistance(along, across, bentZ, panelStart + panelHalf, 0.105, 0.03, panelHalf, 0.085, 0.008);
  const cellIndexAlong = Math.floor((along - panelStart) / CELL_ALONG);
  const cellIndexAcross = Math.floor((across - 0.02) / CELL_ACROSS);
  const cellAlong = ((along - panelStart) % CELL_ALONG + CELL_ALONG) % CELL_ALONG - CELL_ALONG / 2;
  const cellAcross = ((across - 0.02) % CELL_ACROSS + CELL_ACROSS) % CELL_ACROSS - CELL_ACROSS / 2;
  // A missing slat opens a hole into its neighbour; holes also vary a little in size, as hand-cut lattice does.
  const missing = hashNoise(cellIndexAlong * 3.1, cellIndexAcross * 5.7, arm * 11.3) < settings.missingSlats;
  const sizeWobble = (hashNoise(cellIndexAlong, cellIndexAcross, arm + 40) - 0.5) * 0.006;
  const holeAlong = missing ? CELL_ALONG / 2 + 0.002 : 0.019 + sizeWobble;
  const hole = Math.max(Math.abs(cellAlong) - holeAlong, Math.abs(cellAcross) - 0.018 - sizeWobble);
  return Math.min(spar, Math.max(panel, -hole));
}

function sailDistance(localX, localY, localZ) {
  let best = Math.min(
    sphereDistance(localX, localY, localZ, 0, 0, 0.035, 0.05),
    capsuleDistance(localX, localY, localZ, 0, 0, -0.06 - SHAFT_REACH, 0, 0, 0.03, 0.03),
  );
  for (let arm = 0; arm < 4; arm++) {
    const { along, across, bentZ } = armFrame(localX, localY, localZ, arm);
    best = Math.min(best, sailArmDistance(along, across, bentZ, arm));
  }
  return best;
}

function buildStatic(spacing, light) {
  const lists = [];
  const shadowModel = { distance: worldDistance };
  const ground = {
    distance: groundDistance,
    bounds: [-1.1, -0.82, -1.1, 1.1, 0.16, 1.1],
    material: (x, y, z, normalX, normalY) => {
      const island = islandModelDistance(x, y, z);
      const wheat = fieldDistance(x, y, z, FIELD_WHEAT, 0.1);
      if (wheat < island) return surface(RAMPS.wheat);
      // Pond banks and stream bed: wet dark earth.
      if (waterPlan(x, z) < 0.012 && y < 0.005) return surface(RAMPS.rockBlue, false, 0.5);
      if (normalY > 0.6 && y > -0.04 && pathPlan(x, z) < 0) return surface(RAMPS.path, false, 0.7);
      // Ground carries less mottle: it already has rock noise, and full mottle turned it into camouflage.
      if (normalY > 0.6 && y > -0.04) return surface(RAMPS.stubble, false, 0.45);
      return surface(valueNoise(x * 4, y * 9, z * 4) > 0.55 ? RAMPS.rock : RAMPS.rockBlue, false, 0.5);
    },
  };
  lists.push(voxelizeModel(ground, spacing, light, { shadowModel }));
  const tower = {
    distance: (x, y, z) => Math.min(towerDistance(x, y, z), windowDistance(x, y, z), galleryDistance(x, y, z)),
    bounds: [TOWER.x - 0.45, -0.01, TOWER.z - 0.45, TOWER.x + 0.45, TOWER.height + 0.46, TOWER.z + 0.45],
    material: (x, y, z) => {
      if (windowDistance(x, y, z) < spacing * 1.5) return surface(RAMPS.glow, true);
      if (galleryDistance(x, y, z) < spacing * 1.5) return surface(RAMPS.wood, false, 1.3);
      if (y > TOWER.height + 0.28) return surface(RAMPS.spar);
      if (y > TOWER.height - 0.03) return surface(RAMPS.cap);
      const radius = towerRadiusAt(Math.max(y, 0));
      const radial = Math.hypot(x - TOWER.x, z - TOWER.z);
      if (y < 0.27 && radial > radius + 0.012) return surface(RAMPS.wood);
      // Stone courses: a darker mortar line under each course and staggered vertical joints, so the tower reads as
      // masonry at art-pixel size.
      // Courses wander up and down, stones differ in width, and some stones are darker (damp or newer).
      const courseHeight = 0.075;
      const angleAround = Math.atan2(z - TOWER.z, x - TOWER.x);
      const wanderY = y + (valueNoise(angleAround * 4, y * 6, 0.5) - 0.5) * 0.02;
      const courseIndex = Math.floor(wanderY / courseHeight);
      const stoneWidth = 0.42 + hashNoise(courseIndex, 2.2, 0.1) * 0.2;
      const stoneCoordinate = (angleAround + (courseIndex % 2) * 0.25 + hashNoise(courseIndex, 9.1, 0) * 0.3) / stoneWidth;
      const stoneIndex = Math.floor(stoneCoordinate);
      const mortar = wanderY - courseIndex * courseHeight < 0.016 || (stoneCoordinate - stoneIndex) < 0.07;
      if (mortar && y > 0.07) return surface(RAMPS.tower.slice(0, 3), false, 0.6);
      const stoneShade = hashNoise(stoneIndex * 1.3, courseIndex * 2.9, 5.5);
      return surface(stoneShade < 0.22 ? RAMPS.towerDark : RAMPS.tower, false, 1.3);
    },
  };
  lists.push(voxelizeModel(tower, spacing, light, { shadowModel }));
  const props = {
    distance: (x, y, z) => Math.min(hayDistance(x, y, z), farmerDistance(x, y, z), cottageDistance(x, y, z), cartDistance(x, y, z)),
    bounds: [-1.0, -0.01, -0.6, 1.0, 0.5, 0.95],
    material: (x, y, z) => {
      if (hayDistance(x, y, z) < spacing * 1.5) return surface(RAMPS.hay);
      const cottage = cottageParts(x, y, z);
      if (Math.min(cottage.walls, cottage.roof, cottage.chimney, cottage.door) < spacing * 1.5) {
        if (cottage.window < spacing * 1.5) return surface(RAMPS.glow, true);
        if (cottage.door < spacing * 1.5) return surface(RAMPS.wood);
        if (cottage.roof < cottage.walls && cottage.roof < cottage.chimney) return surface(RAMPS.thatch, false, 1.5);
        if (cottage.chimney < cottage.walls) return surface(RAMPS.towerDark, false, 1.2);
        return surface(RAMPS.plaster, false, 1.4);
      }
      const cart = cartParts(x, y, z);
      if (Math.min(cart.wood, cart.wheels, cart.heap) < spacing * 1.5) {
        if (cart.heap < cart.wood && cart.heap < cart.wheels) return surface(RAMPS.hay, false, 1.2);
        if (cart.wheels < cart.wood) return surface(RAMPS.spar, false, 1.0);
        return surface(RAMPS.plank, false, 1.2);
      }
      const parts = farmerParts(x, y, z);
      if (parts.hat < parts.coat && parts.hat < parts.head) return surface(RAMPS.spar);
      if (parts.head < parts.coat) return surface(RAMPS.skin);
      return surface(RAMPS.coat);
    },
  };
  lists.push(voxelizeModel(props, spacing, light, { shadowModel }));
  const water = {
    distance: waterDistance,
    bounds: [POND.x - 0.2, WATER_LEVEL - 0.01, POND.z - 0.2, STREAM_END[0] + 0.12, WATER_LEVEL + 0.01, STREAM_END[1] + 0.12],
    material: () => surface(RAMPS.water, false, 1.6),
  };
  lists.push(voxelizeModel(water, spacing, light, { shadowModel }));
  return lists;
}

function buildSails(spacing, light) {
  const dot = (first, second) => first[0] * second[0] + first[1] * second[1] + first[2] * second[2];
  const sailLight = { ...light, sun: [dot(light.sun, SIDE), dot(light.sun, SAIL_UP), dot(light.sun, SAIL_AXIS)] };
  const extent = SAIL_LENGTH + 0.05;
  const model = {
    distance: sailDistance,
    bounds: [-extent, -extent, -0.1 - SHAFT_REACH, extent, extent, 0.1],
    material: (localX, localY, localZ) => {
      for (let arm = 0; arm < 4; arm++) {
        const { along, across } = armFrame(localX, localY, localZ, arm);
        if (along > 0.17 && across > 0.012 && across < 0.2) {
          // Weathered slats: some boards sun-bleached, some dark with rot.
          const board = hashNoise(Math.floor(along / CELL_ALONG) * 2.3, Math.floor(across / CELL_ACROSS) * 4.1, arm);
          if (board < 0.18) return surface(RAMPS.panelRot, false, 1.4);
          return surface(RAMPS.panel, false, 1.3);
        }
      }
      return surface(RAMPS.spar, false, 1.2);
    },
  };
  return voxelizeModel(model, spacing, sailLight);
}

// ---- Effects. Every effect splat is opaque: the ink resolve treats coverage below half as background, so smoke and
// clouds are solid pixel-art puffs that thin out by dropping splats, not by fading alpha.
const WIND = [-RIGHT[0], 0, -RIGHT[1]];
const SMOKE_SOURCE = CHIMNEY_TOP;
const fract = value => value - Math.floor(value);

// A puff made of many small splats inside a lumpy ball: big single splats render as smooth ellipses, which breaks
// the pixel look, so volume is always filled with art-pixel-sized splats.
function fillPuff(points, center, radius, colorAt, seed, squash = 1) {
  const count = Math.max(4, Math.round((radius / 0.01) ** 2 * 3));
  for (let index = 0; index < count; index++) {
    const theta = hashNoise(seed, index, 1.1) * Math.PI * 2;
    const height = hashNoise(seed, index, 2.2) * 2 - 1;
    const reach = Math.cbrt(hashNoise(seed, index, 3.3)) * radius;
    const ring = Math.sqrt(1 - height * height);
    const offset = [Math.cos(theta) * ring * reach, height * reach * squash, Math.sin(theta) * ring * reach];
    // Top of a puff is lit, underside in shadow.
    const tone = height + (hashNoise(seed, index, 4.4) - 0.5) * 0.9;
    points.push({ position: [center[0] + offset[0], center[1] + offset[1], center[2] + offset[2]], color: colorAt(tone), scale: 0.0055 });
  }
}

function splatList(points) {
  const count = points.length;
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 4);
  const scales = new Float32Array(count);
  points.forEach((point, index) => {
    positions.set(point.position, index * 3);
    colors.set([...point.color, 1], index * 4);
    scales[index] = point.scale;
  });
  return { count, positions, colors, scales };
}

// Smoke from the cottage chimney: puffs rise, swell, bend downwind and break up near the top.
function smokePoints(time) {
  const points = [];
  // Few, separate puffs: many overlapping ones merge into a solid tube.
  const puffCount = 16;
  const lifetime = 8;
  for (let puff = 0; puff < puffCount; puff++) {
    const age = fract(time / lifetime + puff / puffCount + hashNoise(puff, 1.9, 0) * 0.02);
    const wobble = Math.sin(age * 7 + puff * 2.3) * 0.05 * age + (hashNoise(puff, 8.8, 0) - 0.5) * 0.06 * age;
    const rise = age * 1.05;
    const drift = Math.pow(age, 1.6) * 0.75;
    const center = [
      SMOKE_SOURCE[0] + WIND[0] * drift + wobble,
      SMOKE_SOURCE[2] + 0.01 + rise * 0.85,
      SMOKE_SOURCE[1] + WIND[2] * drift + wobble * 0.5,
    ];
    const size = 0.016 + age * 0.04;
    const tone = age < 0.25 ? 4 : age < 0.6 ? 3 : 2;
    for (let lump = 0; lump < 3; lump++) {
      // Breaking up: older puffs lose lumps at random.
      if (age > 0.55 && hashNoise(puff, lump, 7.3) < (age - 0.55) / 0.45) continue;
      const angle = hashNoise(puff, lump, 2.2) * Math.PI * 2;
      const offset = size * 0.6;
      const lumpCenter = [center[0] + Math.cos(angle) * offset, center[1] + Math.sin(angle) * offset * 0.6, center[2] + Math.sin(angle) * offset];
      fillPuff(points, lumpCenter, size * (0.7 + hashNoise(puff, lump, 4.4) * 0.3), height => PALETTE[height > 0.3 ? Math.min(tone + 1, 5) : tone], puff * 7 + lump);
    }
  }
  return points;
}

// Waterfall where the stream leaves the island: streaks fall and speed up, foam churns at the lip and at the bottom.
function waterfallPoints(time) {
  const points = [];
  const outward = [STREAM_DIRECTION[0], STREAM_DIRECTION[1]];
  for (let drop = 0; drop < 220; drop++) {
    const age = fract(time * 0.9 + hashNoise(drop, 1, 2));
    // The stream thins to spray and is gone before it clears the island's underside.
    if (age > 0.6 && hashNoise(drop, 7, 2) < (age - 0.6) / 0.4) continue;
    const fall = age * age * 0.6;
    const spread = (hashNoise(drop, 2, 2) - 0.5) * 0.045;
    const throwOut = 0.03 + age * 0.07;
    points.push({
      position: [
        STREAM_END[0] + outward[0] * throwOut - outward[1] * spread,
        WATER_LEVEL - fall,
        STREAM_END[1] + outward[1] * throwOut + outward[0] * spread,
      ],
      color: PALETTE[hashNoise(drop, 3, 2) > 0.7 ? 11 : hashNoise(drop, 4, 2) > 0.4 ? 5 : 4],
      scale: 0.006,
    });
  }
  for (let foam = 0; foam < 14; foam++) {
    const angle = hashNoise(foam, 5, 2) * Math.PI * 2 + time * 2;
    const radius = 0.015 + hashNoise(foam, 6, 2) * 0.03;
    points.push({
      position: [STREAM_END[0] + outward[0] * 0.02 + Math.cos(angle) * radius, WATER_LEVEL + 0.004, STREAM_END[1] + outward[1] * 0.02 + Math.sin(angle) * radius],
      color: PALETTE[foam % 3 === 0 ? 11 : 5],
      scale: 0.005,
    });
  }
  return points;
}

// Sun glints on the pond: single bright pixels that blink as ripples pass.
function glintPoints(time) {
  const points = [];
  for (let glint = 0; glint < 26; glint++) {
    if (Math.sin(time * 4 + glint * 2.3) < 0.2) continue;
    const angle = hashNoise(glint, 1, 4) * Math.PI * 2;
    const radius = Math.sqrt(hashNoise(glint, 2, 4)) * 0.85;
    points.push({
      position: [POND.x + Math.cos(angle) * POND.radiusX * radius, WATER_LEVEL + 0.005, POND.z + Math.sin(angle) * POND.radiusZ * radius],
      color: PALETTE[11],
      scale: 0.0045,
    });
  }
  return points;
}

// Chaff blown off the wheat: bits flutter downwind in gusts, then loop back to the field.
function chaffPoints(time) {
  const points = [];
  for (let bit = 0; bit < 110; bit++) {
    const lifetime = 4 + hashNoise(bit, 1, 9) * 3;
    const age = fract(time / lifetime + hashNoise(bit, 2, 9));
    const startX = FIELD_WHEAT.x + (hashNoise(bit, 3, 9) - 0.5) * 2 * FIELD_WHEAT.halfX;
    const startZ = FIELD_WHEAT.z + (hashNoise(bit, 4, 9) - 0.5) * 2 * FIELD_WHEAT.halfZ;
    const gust = age * 0.9 + Math.sin(age * 6 + bit) * 0.05;
    points.push({
      position: [
        startX + WIND[0] * gust + Math.sin(time * 3 + bit) * 0.02,
        0.12 + Math.sin(age * Math.PI) * (0.15 + hashNoise(bit, 5, 9) * 0.35) + Math.sin(time * 7 + bit * 3) * 0.015,
        startZ + WIND[2] * gust + Math.cos(time * 2.6 + bit) * 0.02,
      ],
      color: PALETTE[[9, 10, 11][bit % 3]],
      scale: 0.0045,
    });
  }
  return points;
}

// Dust motes catching the light on the sunny side of the tower; they wink on and off as they turn.
function motePoints(time) {
  const points = [];
  for (let mote = 0; mote < 45; mote++) {
    if (Math.sin(time * 2.2 + mote * 1.7) < -0.3) continue;
    const angle = hashNoise(mote, 1, 3) * Math.PI * 2 + time * 0.05;
    const radius = 0.25 + hashNoise(mote, 2, 3) * 0.6;
    points.push({
      position: [
        TOWER.x + Math.cos(angle) * radius,
        0.15 + fract(hashNoise(mote, 3, 3) + time * 0.02) * 1.1,
        TOWER.z + Math.sin(angle) * radius,
      ],
      color: PALETTE[mote % 4 === 0 ? 11 : 5],
      scale: 0.0035,
    });
  }
  return points;
}

// A few birds circling the mill, wings flapping out of phase.
function birdPoints(time) {
  const points = [];
  for (let bird = 0; bird < 4; bird++) {
    const radius = 0.75 + bird * 0.13;
    const angle = time * (0.35 + bird * 0.04) + bird * 1.7;
    const center = [TOWER.x + Math.cos(angle) * radius, 1.45 + bird * 0.09 + Math.sin(time * 0.7 + bird) * 0.04, TOWER.z + Math.sin(angle) * radius];
    // Wings spread across the flight direction (radial), tips beat up and down.
    const across = [Math.cos(angle), 0, Math.sin(angle)];
    const beat = Math.sin(time * 9 + bird * 2.1);
    points.push({ position: center, color: PALETTE[4], scale: 0.009 });
    for (const side of [-1, 1]) {
      for (let segment = 1; segment <= 4; segment++) {
        const reach = segment * 0.015;
        points.push({
          position: [center[0] + across[0] * reach * side, center[1] + beat * reach * 0.9, center[2] + across[2] * reach * side],
          color: PALETTE[segment === 4 ? 5 : 4],
          scale: 0.0075,
        });
      }
    }
  }
  return points;
}

// Low cloud banks drifting under the island, so it floats in air rather than in a void.
function cloudPoints(time) {
  const points = [];
  for (let bank = 0; bank < 7; bank++) {
    const angle = bank / 7 * Math.PI * 2 + time * 0.03;
    const radius = 1.0 + hashNoise(bank, 1, 5) * 0.35;
    const center = [Math.cos(angle) * radius, -0.62 + hashNoise(bank, 2, 5) * 0.2, Math.sin(angle) * radius];
    for (let lump = 0; lump < 7; lump++) {
      const spread = (hashNoise(bank, lump, 6) - 0.5) * 0.4;
      const lumpCenter = [center[0] - Math.sin(angle) * spread, center[1] + hashNoise(bank, lump, 7) * 0.04, center[2] + Math.cos(angle) * spread];
      fillPuff(points, lumpCenter, 0.035 + hashNoise(bank, lump, 9) * 0.03, height => PALETTE[height > 0.35 ? 3 : 2], 500 + bank * 13 + lump, 0.55);
    }
  }
  return points;
}

function effectLists(time) {
  return [smokePoints(time), waterfallPoints(time), glintPoints(time), chaffPoints(time), motePoints(time), birdPoints(time), cloudPoints(time)].map(splatList);
}

function turnSails(sails, angle) {
  const positions = new Float32Array(sails.count * 3);
  const cosine = Math.cos(angle);
  const sine = Math.sin(angle);
  for (let index = 0; index < sails.count; index++) {
    const localX = sails.positions[index * 3];
    const localY = sails.positions[index * 3 + 1];
    const localZ = sails.positions[index * 3 + 2];
    const turnedX = localX * cosine - localY * sine;
    const turnedY = localX * sine + localY * cosine;
    for (let axis = 0; axis < 3; axis++) {
      positions[index * 3 + axis] = HUB[axis] + turnedX * SIDE[axis] + turnedY * SAIL_UP[axis] + localZ * SAIL_AXIS[axis];
    }
  }
  return { count: sails.count, positions, colors: sails.colors, scales: sails.scales };
}

export const windmillClearance = { worldDistance: (x, y, z) => worldDistance(x, y, z) };

export function buildWindmill(spacing) {
  // Deeper shading than the first frame: shadows and creases drop further down the ramp, and broad mottle breaks every
  // flat face into worn patches.
  const light = {
    sun: [-0.27, 0.8, 0.87], shadowSoftness: 8, rampJitter: 0.16, rampGain: 1.08,
    rampShadowFloor: 0.3, rampOcclusion: 0.65, rampMottle: 0.2,
  };
  const staticLists = buildStatic(spacing, light);
  const sails = buildSails(spacing, light);
  return {
    name: 'windmill',
    palette: PALETTE,
    background: { inner: PALETTE[0], outer: PALETTE[0] },
    camera: { target: [0.05, 0.36, 0], distance: 4.9, height: 1.55, startAngle: WINDMILL_CAMERA_ANGLE },
    staticLists,
    sails,
    dynamic(time) {
      return [turnSails(sails, 0.35 + time * 0.6), ...effectLists(time)];
    },
    glows: () => [],
    contactShadows: () => [],
  };
}
