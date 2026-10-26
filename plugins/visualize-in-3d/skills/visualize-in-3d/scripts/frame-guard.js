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
