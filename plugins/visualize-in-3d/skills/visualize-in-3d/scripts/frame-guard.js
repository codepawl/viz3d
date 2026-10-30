// Contact guard (measureContacts): for objects that rest on a surface (papers, a mug, a folder on a desk), checks every
// frame that nothing sinks into the surface or sits so close that it z-fights. Usage inside renderAt(time):
//   const contacts = measureContacts([{ name: 'invoice', object: invoiceGroup, surface: deskMesh }], { minimumGap: 0.0003 });
//   if (contacts.some((entry) => !entry.ok)) { /* log it with the time and fail the render */ }
// `surface` is a horizontal mesh (its top is found by a ray from above), a world height (number) or a function
// (worldX, worldZ) => worldY. Every vertex of every visible mesh under `object` is taken to world space and compared with
// the surface below it. A vertex lower than the surface is a 'penetration'; one above it by less than `minimumGap` is a
// 'z-fight'. Meshes with userData.contactIgnore = true are skipped. Each result is
// { name, ok, lowestGap, vertexCount, faults: [{ kind, gap, worldPosition }] }, faults capped by maxFaultsPerObject.
// Skinned meshes (a rigged character lying on a bed) are sampled with skinning applied (SkinnedMesh.getVertexPosition),
// measureContacts refreshes their world matrices itself; pose the bones before calling it.
// A pair may also set side: 'below' (the object must stay under the surface, e.g. a body under a blanket; the gap is
// surface minus vertex) and vertexFilter(mesh, vertexIndex) => boolean to measure only some vertices (e.g. not the hands).
// Dependencies: none beyond "three" (tested with 0.186). Copy this file into the app next to your render code.
// Frame guard: measures where the film's subjects land on screen, every frame, so a render
// fails on the faults a viewer sees first (a creature cut by the frame edge, shrunk to a few
// pixels, or buried under smoke) instead of being caught by eye after a 20 minute render.
//
// Usage inside renderAt(time):
//   const report = measureSubjects(camera, subjects, { width: 384, height: 216, margin: 6 });
//   frameLog.push({ time, report });
// Then at the end of a render: const faults = findFaults(frameLog, { minHeightPixels: 24 });
// `subjects` is a list of { name, object, occluders? } where occluders are meshes (smoke, steam,
// beams) whose screen boxes count against the subject's visible share.
import * as THREE from 'three';

const corner = new THREE.Vector3();
const box = new THREE.Box3();

export function screenBox(camera, object, width, height) {
  box.setFromObject(object, true);
  if (box.isEmpty()) {
    return null;
  }
  let left = Infinity;
  let right = -Infinity;
  let top = Infinity;
  let bottom = -Infinity;
  for (let index = 0; index < 8; index += 1) {
    corner.set(
      index & 1 ? box.max.x : box.min.x,
      index & 2 ? box.max.y : box.min.y,
      index & 4 ? box.max.z : box.min.z,
    );
    corner.project(camera);
    const pixelX = (corner.x * 0.5 + 0.5) * width;
    const pixelY = (1 - (corner.y * 0.5 + 0.5)) * height;
    left = Math.min(left, pixelX);
    right = Math.max(right, pixelX);
    top = Math.min(top, pixelY);
    bottom = Math.max(bottom, pixelY);
  }
  return { left, right, top, bottom };
}

function overlapArea(first, second) {
  const overlapWidth = Math.max(0, Math.min(first.right, second.right) - Math.max(first.left, second.left));
  const overlapHeight = Math.max(0, Math.min(first.bottom, second.bottom) - Math.max(first.top, second.top));
  return overlapWidth * overlapHeight;
}

function boxArea(rectangle) {
  return Math.max(0, rectangle.right - rectangle.left) * Math.max(0, rectangle.bottom - rectangle.top);
}

// Visible share is approximate: occluder boxes are rectangles and may overlap each other, so the
// share is a floor. Only count occluders that are actually opaque this frame (dissolve below 0.5).
export function measureSubjects(camera, subjects, { width, height, margin = 4 }) {
  camera.updateMatrixWorld();
  return subjects.map(({ name, object, occluders = [] }) => {
    if (!object.visible) {
      return { name, hidden: true };
    }
    const rectangle = screenBox(camera, object, width, height);
    if (!rectangle) {
      return { name, hidden: true };
    }
    const outside =
      rectangle.left < margin ||
      rectangle.top < margin ||
      rectangle.right > width - margin ||
      rectangle.bottom > height - margin;
    let coveredArea = 0;
    for (const occluder of occluders) {
      if (!occluder.visible) {
        continue;
      }
      const occluderBox = screenBox(camera, occluder, width, height);
      if (occluderBox) {
        coveredArea += overlapArea(rectangle, occluderBox);
      }
    }
    const area = boxArea(rectangle);
    const visibleShare = area > 0 ? Math.max(0, 1 - coveredArea / area) : 0;
    return {
      name,
      rectangle,
      heightPixels: rectangle.bottom - rectangle.top,
      outside,
      visibleShare,
    };
  });
}

// Faults that last longer than `graceSeconds` in a row. A subject meant to leave the frame
// (an exit, a recall) is listed in `allowed` as { name, from, to }.
export function findFaults(frameLog, { minHeightPixels = 24, minVisibleShare = 0.5, graceSeconds = 0.3, allowed = [] } = {}) {
  const faults = [];
  const openRuns = new Map();
  const isAllowed = (name, time) => allowed.some((entry) => entry.name === name && time >= entry.from && time <= entry.to);
  const closeRun = (key, endTime) => {
    const run = openRuns.get(key);
    if (run && endTime - run.start > graceSeconds) {
      faults.push({ ...run, end: endTime });
    }
    openRuns.delete(key);
  };
  for (const { time, report } of frameLog) {
    for (const subject of report) {
      if (subject.hidden || isAllowed(subject.name, time)) {
        continue;
      }
      const problems = {
        outside: subject.outside,
        tiny: subject.heightPixels < minHeightPixels,
        covered: subject.visibleShare < minVisibleShare,
      };
      for (const [kind, present] of Object.entries(problems)) {
        const key = `${subject.name}:${kind}`;
        if (present && !openRuns.has(key)) {
          openRuns.set(key, { name: subject.name, kind, start: time });
        } else if (!present) {
          closeRun(key, time);
        }
      }
    }
  }
  const lastTime = frameLog.length ? frameLog[frameLog.length - 1].time : 0;
  for (const key of [...openRuns.keys()]) {
    closeRun(key, lastTime);
  }
  return faults;
}

const contactRay = new THREE.Raycaster();
const contactOrigin = new THREE.Vector3();
const contactDown = new THREE.Vector3(0, -1, 0);

function surfaceHeightBelow(surface, worldX, worldY, worldZ) {
  if (typeof surface === 'number') {
    return surface;
  }
  if (typeof surface === 'function') {
    return surface(worldX, worldZ);
  }
  contactRay.set(contactOrigin.set(worldX, worldY + 1000, worldZ), contactDown);
  contactRay.far = 3000;
  const hits = contactRay.intersectObject(surface, true);
  return hits.length ? hits[0].point.y : null;
}

// pairs: [{ name, object, surface, side = 'above', vertexFilter }]. options: { minimumGap = 0.0002, penetrationTolerance = 0, maxFaultsPerObject = 3 }.
export function measureContacts(pairs, { minimumGap = 0.0002, penetrationTolerance = 0, maxFaultsPerObject = 3 } = {}) {
  const probe = new THREE.Vector3();
  return pairs.map(({ name, object, surface, side = 'above', vertexFilter }) => {
    // updateMatrixWorld (not only updateWorldMatrix) also refreshes a skinned mesh's bind matrix inverse.
    object.updateWorldMatrix(true, false);
    object.updateMatrixWorld(true);
    if (surface && surface.updateWorldMatrix) {
      surface.updateWorldMatrix(true, true);
    }
    const faults = [];
    let lowestGap = Infinity;
    let vertexCount = 0;
    object.traverse((child) => {
      if (!child.isMesh || child.userData.contactIgnore || !child.visible) {
        return;
      }
      const positions = child.geometry.attributes.position;
      for (let index = 0; index < positions.count; index += 1) {
        if (vertexFilter && !vertexFilter(child, index)) {
          continue;
        }
        if (child.isSkinnedMesh) {
          child.getVertexPosition(index, probe);
        } else {
          probe.fromBufferAttribute(positions, index);
        }
        probe.applyMatrix4(child.matrixWorld);
        const surfaceY = surfaceHeightBelow(surface, probe.x, probe.y, probe.z);
        if (surfaceY === null) {
          continue;
        }
        vertexCount += 1;
        const gap = side === 'below' ? surfaceY - probe.y : probe.y - surfaceY;
        lowestGap = Math.min(lowestGap, gap);
        const kind = gap < -penetrationTolerance ? 'penetration' : gap < minimumGap ? 'z-fight' : null;
        if (kind && faults.length < maxFaultsPerObject) {
          faults.push({ kind, gap, worldPosition: probe.toArray() });
        }
      }
    });
    return { name, ok: faults.length === 0, lowestGap, vertexCount, faults };
  });
}

// Grip guard (registerGrip / measureGrips): a hand that holds, pulls or turns something must TOUCH it. A hand animated to be
// "near" a prop reads as floating, so every hand-on-object moment registers a grip and the render fails when they separate.
//   1. Put a named socket (an Object3D) on the prop, in the prop's own space (a panel's edge, a lever's tip). It moves with the prop.
//   2. Put a contact Object3D on the hand bone (the palm or finger crook that should touch the socket).
//   3. Once, at build time: registerGrip({ name: 'panel-edge', hand: handBone, contact, socket, from: 126.5, to: 127.1 }).
//      from/to are the seconds in which the hand is fully on the prop, not the approach or the release.
//   4. Each frame, after two-bone IK has put contact on socket: const results = measureGrips(time). Fail the render when any
//      result has ok false (distance in metres, GRIP_LIMIT = 1 cm). Each result is { name, distance, active, ok }.
// The prop's motion stays time-driven and the arm follows it. When the arm cannot reach, the body turns, leans and steps; look at
// that move in the shot, since a lunge across a low camera blacks out the frame. A push near the hinge needs less reach than the edge.
const registeredGrips = [];
export const GRIP_LIMIT = 0.01;

export function registerGrip({ name, hand, contact, socket, from, to }) {
  const existing = registeredGrips.findIndex((grip) => grip.name === name);
  if (existing >= 0) {
    registeredGrips.splice(existing, 1);
  }
  registeredGrips.push({ name, hand, contact, socket, from, to });
}

const gripContactPoint = new THREE.Vector3();
const gripSocketPoint = new THREE.Vector3();

export function measureGrips(time, { limit = GRIP_LIMIT } = {}) {
  return registeredGrips.map((grip) => {
    if (time < grip.from || time > grip.to) {
      return { name: grip.name, distance: null, active: false, ok: true };
    }
    grip.contact.updateWorldMatrix(true, false);
    grip.socket.updateWorldMatrix(true, false);
    grip.contact.getWorldPosition(gripContactPoint);
    grip.socket.getWorldPosition(gripSocketPoint);
    const distance = gripContactPoint.distanceTo(gripSocketPoint);
    return { name: grip.name, distance, active: true, ok: distance <= limit };
  });
}
