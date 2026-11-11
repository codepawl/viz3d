// Page side of the renderer: builds a scene, draws its splats with 67js at a low internal size, then turns the frame
// into pixel art (palette, ordered dither, glow halos) and scales it up with nearest-neighbour sampling.
import { Renderer67 } from '/node_modules/@codepawlhq/67js/build/67.module.js';
import { attachGaussianSplats, createGaussianSplats } from '/node_modules/@codepawlhq/67js/build/gaussian-splats.js';
import { packSplatData, hashNoise, valueNoise } from './voxel-splats.js';
import { SCENE_BUILDERS } from './scenes.js';

const BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5].map(value => (value + 0.5) / 16);

const state = { scene: null, sceneKey: '', renderer: null, rendererSize: 0, canvas: null };

function getRenderer(size) {
  if (state.renderer && state.rendererSize === size) return state.renderer;
  if (state.renderer) state.renderer.dispose();
  state.canvas?.remove();
  const canvas = document.createElement('canvas');
  canvas.style.width = `${size}px`;
  canvas.style.height = `${size}px`;
  document.body.appendChild(canvas);
  state.canvas = canvas;
  state.renderer = new Renderer67(canvas, [], { ground: false, transparent: true, pixelRatio: 1, samples: 1, memoryBudgetMiB: 512 });
  state.rendererSize = size;
  return state.renderer;
}

window.setupScene = function setupScene(sceneName, spacing) {
  const key = `${sceneName}:${spacing}`;
  if (state.sceneKey === key) return state.scene.splatCount;
  const started = performance.now();
  const scene = SCENE_BUILDERS[sceneName](spacing);
  const toColor = value => [1, 3, 5].map(start => parseInt(value.slice(start, start + 2), 16) / 255);
  if (scene.paletteExtra) scene.palette = [...scene.palette, ...scene.paletteExtra.map(toColor)];
  let minimumY = Infinity;
  let maximumY = -Infinity;
  for (const list of scene.staticLists) {
    for (let index = 0; index < list.count; index++) {
      const y = list.positions[index * 3 + 1];
      minimumY = Math.min(minimumY, y);
      maximumY = Math.max(maximumY, y);
    }
  }
  scene.heightRange = [minimumY, maximumY];
  scene.splatCount = scene.staticLists.reduce((sum, list) => sum + list.count, 0);
  scene.buildMilliseconds = performance.now() - started;
  state.scene = scene;
  state.sceneKey = key;
  return scene.splatCount;
};

// Mist made of big faint splats drifting around the island, and a few wandering wisp lights.
function atmosphereSplats(scene, time, fade) {
  const mist = scene.mist;
  if (!mist || fade <= 0) return { lists: [], glows: [] };
  const mistCount = 320;
  const positions = new Float32Array(mistCount * 3);
  const colors = new Float32Array(mistCount * 4);
  const scales = new Float32Array(mistCount);
  for (let index = 0; index < mistCount; index++) {
    const radiusRandom = hashNoise(index, 1.3, 7.1);
    const radius = 0.75 + radiusRandom * 1.3;
    const speed = (0.03 + hashNoise(index, 2.2, 3.3) * 0.06) * (hashNoise(index, 9, 9) > 0.5 ? 1 : -1);
    const angle = hashNoise(index, 4.4, 1.1) * Math.PI * 2 + time * speed;
    const height = mist.low + hashNoise(index, 5.5, 2.2) * (mist.high - mist.low) + Math.sin(time * 0.3 + index) * 0.04;
    positions.set([Math.cos(angle) * radius, height, Math.sin(angle) * radius], index * 3);
    const breathe = 0.6 + 0.4 * Math.sin(time * 0.4 + index * 1.7);
    colors.set([...mist.color, mist.alpha * breathe * fade * (0.5 + hashNoise(index, 6, 6))], index * 4);
    scales[index] = 0.08 + hashNoise(index, 7.7, 8.8) * 0.16;
  }
  const wispCount = 7;
  const trailLength = mist.trails ? 10 : 1;
  const wispPositions = new Float32Array(wispCount * trailLength * 3);
  const wispColors = new Float32Array(wispCount * trailLength * 4);
  const wispScales = new Float32Array(wispCount * trailLength);
  const glows = [];
  const wispAt = (phase, sampleTime) => [
    Math.sin(sampleTime * 0.13 + phase) * 1.1 + Math.sin(sampleTime * 0.31 + phase * 2) * 0.25,
    mist.wispHeight + Math.sin(sampleTime * 0.5 + phase) * 0.18,
    Math.cos(sampleTime * 0.11 + phase * 1.3) * 1.1 + Math.cos(sampleTime * 0.27 + phase) * 0.25,
  ];
  for (let wisp = 0; wisp < wispCount; wisp++) {
    const phase = hashNoise(wisp, 3.1, 4.7) * 100;
    const flicker = (0.55 + 0.45 * Math.sin(time * 1.7 + phase * 3)) * fade;
    for (let step = 0; step < trailLength; step++) {
      const slot = wisp * trailLength + step;
      wispPositions.set(wispAt(phase, time - step * 0.12), slot * 3);
      const tail = 1 - step / trailLength;
      wispColors.set([...mist.wispColor, flicker * (step === 0 ? 1 : 0.45 * tail)], slot * 4);
      wispScales[slot] = step === 0 ? 0.016 : 0.012 * tail + 0.004;
    }
    glows.push({ position: wispAt(phase, time), color: mist.wispColor, radius: 0.13, strength: 0.22 * flicker });
  }
  const wispTotal = wispCount * trailLength;
  return {
    lists: [{ count: mistCount, positions, colors, scales }, { count: wispTotal, positions: wispPositions, colors: wispColors, scales: wispScales }],
    glows,
  };
}

const easeOutBack = amount => 1 + 2.2 * Math.pow(amount - 1, 3) + 1.2 * Math.pow(amount - 1, 2);

// Moves, fades and grows static splats for the build-up and break-apart moments, and darkens ground under movers.
function animateStatic(scene, time, { assemble = 1, dissolve = 0 }) {
  const shadows = scene.contactShadows(time);
  const [minimumY, maximumY] = scene.heightRange;
  const range = maximumY - minimumY;
  return scene.staticLists.map((list, listIndex) => {
    if (assemble >= 1 && dissolve <= 0 && shadows.length === 0) return list;
    const positions = new Float32Array(list.positions);
    const colors = new Float32Array(list.colors);
    const scales = new Float32Array(list.scales);
    for (let index = 0; index < list.count; index++) {
      const x = positions[index * 3];
      const y = positions[index * 3 + 1];
      const z = positions[index * 3 + 2];
      for (const shadow of shadows) {
        const distance = Math.hypot(x - shadow.x, z - shadow.z);
        if (distance < shadow.radius && y > -0.08 && y < 0.06) {
          const darken = 1 - shadow.strength * Math.pow(1 - distance / shadow.radius, 0.7);
          colors[index * 4] *= darken;
          colors[index * 4 + 1] *= darken;
          colors[index * 4 + 2] *= darken * 1.04;
        }
      }
      const random = hashNoise(index * 0.37 + listIndex * 13.1, x * 3.1, z * 2.7);
      const randomSecond = hashNoise(index * 0.11, listIndex + 4.2, y * 5.3);
      if (assemble < 1) {
        const delay = ((y - minimumY) / range) * 0.55 + random * 0.2;
        const progress = Math.min(Math.max((assemble - delay) / 0.25, 0), 1);
        const settle = easeOutBack(progress);
        const scatterAngle = randomSecond * Math.PI * 2;
        const lift = (1 - settle) * (1.6 + random * 1.2);
        positions[index * 3] = x + Math.cos(scatterAngle) * (1 - settle) * 0.9;
        positions[index * 3 + 1] = y + lift;
        positions[index * 3 + 2] = z + Math.sin(scatterAngle) * (1 - settle) * 0.9;
        colors[index * 4 + 3] *= progress > 0 ? Math.min(progress * 3, 1) : 0;
        scales[index] *= 1 + (1 - progress) * 0.5;
      }
      if (dissolve > 0) {
        const delay = random * 0.45 + ((maximumY - y) / range) * 0.25;
        const progress = Math.min(Math.max((dissolve - delay) / 0.35, 0), 1);
        const push = progress * progress;
        const outward = Math.hypot(x, z) || 1;
        positions[index * 3] = x + (x / outward) * push * 1.3 + Math.cos(randomSecond * 6.28) * push * 0.5;
        positions[index * 3 + 1] = y + push * (1.2 + random * 1.5);
        positions[index * 3 + 2] = z + (z / outward) * push * 1.3 + Math.sin(randomSecond * 6.28) * push * 0.5;
        colors[index * 4 + 3] *= 1 - progress;
        scales[index] *= 1 + progress * 2.5;
      }
    }
    return { count: list.count, positions, colors, scales };
  });
}

function cameraFor(scene, time, { angleOffset = 0, zoom = 1, orbitSpeed = 0.12, heightOffset = 0, targetOffset = [0, 0, 0] }) {
  const { target, distance, height, startAngle } = scene.camera;
  const angle = startAngle + time * orbitSpeed + angleOffset;
  const finalTarget = [target[0] + targetOffset[0], target[1] + targetOffset[1], target[2] + targetOffset[2]];
  return {
    eye: [finalTarget[0] + Math.sin(angle) * distance * zoom, finalTarget[1] + (height + heightOffset) * zoom, finalTarget[2] + Math.cos(angle) * distance * zoom],
    target: finalTarget,
  };
}

function project(renderer, point, size) {
  const view = renderer.view;
  const projection = renderer.projection;
  const viewSpace = [0, 1, 2, 3].map(row => view[row] * point[0] + view[4 + row] * point[1] + view[8 + row] * point[2] + view[12 + row]);
  const clip = [0, 1, 2, 3].map(row => projection[row] * viewSpace[0] + projection[4 + row] * viewSpace[1] + projection[8 + row] * viewSpace[2] + projection[12 + row] * viewSpace[3]);
  if (clip[3] <= 0) return null;
  return {
    x: (clip[0] / clip[3] * 0.5 + 0.5) * size,
    y: (1 - (clip[1] / clip[3] * 0.5 + 0.5)) * size,
    pixelsPerUnit: projection[5] * size * 0.5 / clip[3],
  };
}

function boxBlur(source, size, radius) {
  const horizontal = new Float32Array(source.length);
  const result = new Float32Array(source.length);
  const passes = [[source, horizontal, 1, 0], [horizontal, result, 0, 1]];
  for (const [from, to, stepX, stepY] of passes) {
    for (let row = 0; row < size; row++) {
      for (let column = 0; column < size; column++) {
        const sum = [0, 0, 0];
        let count = 0;
        for (let offset = -radius; offset <= radius; offset++) {
          const sampleX = column + offset * stepX;
          const sampleY = row + offset * stepY;
          if (sampleX < 0 || sampleY < 0 || sampleX >= size || sampleY >= size) continue;
          const index = (sampleY * size + sampleX) * 3;
          sum[0] += from[index];
          sum[1] += from[index + 1];
          sum[2] += from[index + 2];
          count++;
        }
        const target = (row * size + column) * 3;
        to[target] = sum[0] / count;
        to[target + 1] = sum[1] / count;
        to[target + 2] = sum[2] / count;
      }
    }
  }
  return result;
}

// Soft bloom on the bright parts, lifted blacks towards the fog colour, a low mist band and a vignette.
function applyDreamyHaze(buffer, size, haze) {
  if (!haze) return;
  const bright = new Float32Array(buffer.length);
  for (let index = 0; index < buffer.length; index++) bright[index] = Math.max(buffer[index] - haze.bloomThreshold, 0);
  const radius = Math.max(2, Math.round(size / 36));
  const bloom = boxBlur(boxBlur(bright, size, radius), size, radius);
  const softened = boxBlur(buffer, size, 1);
  for (let row = 0; row < size; row++) {
    for (let column = 0; column < size; column++) {
      const index = (row * size + column) * 3;
      const vertical = row / size;
      const mistBand = Math.max(0, Math.min(1, (vertical - haze.mistTop) / 0.35)) * haze.mistStrength;
      const edge = Math.hypot(column / size - 0.5, row / size - 0.5);
      const vignette = 1 - Math.max(edge - 0.32, 0) * haze.vignette;
      for (let channel = 0; channel < 3; channel++) {
        let value = buffer[index + channel] * (1 - haze.soften) + softened[index + channel] * haze.soften;
        value += bloom[index + channel] * haze.bloom;
        value = value * (1 - haze.lift) + haze.color[channel] * haze.lift;
        value = value * (1 - mistBand) + haze.color[channel] * 1.4 * mistBand;
        buffer[index + channel] = value * vignette;
      }
    }
  }
}

function expandPalette(palette, steps) {
  if (steps <= 1) return palette;
  const expanded = [...palette];
  for (let first = 0; first < palette.length; first++) {
    for (let second = first + 1; second < palette.length; second++) {
      const distance = Math.hypot(...palette[first].map((value, channel) => value - palette[second][channel]));
      if (distance > 0.32) continue;
      for (let step = 1; step < steps; step++) {
        const amount = step / steps;
        expanded.push(palette[first].map((value, channel) => value + (palette[second][channel] - value) * amount));
      }
    }
  }
  return expanded;
}

function postProcess(scene, renderer, time, internalSize, style, outputSize, fadeToBlack, flash = 0) {
  const reader = document.createElement('canvas');
  reader.width = internalSize;
  reader.height = internalSize;
  const readerContext = reader.getContext('2d', { willReadFrequently: true });
  readerContext.drawImage(state.canvas, 0, 0, internalSize, internalSize);
  const image = readerContext.getImageData(0, 0, internalSize, internalSize);
  const pixels = image.data;
  const glows = [...scene.glows(time), ...(scene.extraGlows ?? [])].map(glow => {
    const screen = project(renderer, glow.position, internalSize);
    return screen && { ...glow, screenX: screen.x, screenY: screen.y, radiusPixels: glow.radius * screen.pixelsPerUnit };
  }).filter(Boolean);
  const palette = style.palette === 'none' ? null : expandPalette(scene.palette, style.paletteSteps ?? 1);
  const { inner, outer, stars, moon, clouds } = scene.background;
  const pixelScale = internalSize / 216;
  const outlineColor = scene.palette[0].map(value => value * 0.6);
  const isOutline = new Uint8Array(internalSize * internalSize);
  if (style.outline) {
    const solid = index => pixels[index * 4 + 3] > 150;
    for (let row = 1; row < internalSize - 1; row++) {
      for (let column = 1; column < internalSize - 1; column++) {
        const index = row * internalSize + column;
        if (pixels[index * 4 + 3] > 90) continue;
        if (solid(index - 1) || solid(index + 1) || solid(index - internalSize) || solid(index + internalSize)) isOutline[index] = 1;
      }
    }
  }
  const buffer = new Float32Array(internalSize * internalSize * 3);
  for (let row = 0; row < internalSize; row++) {
    for (let column = 0; column < internalSize; column++) {
      const pixelIndex = row * internalSize + column;
      const offset = pixelIndex * 4;
      const alpha = pixels[offset + 3] / 255;
      const centerDistance = Math.min(Math.hypot(column / internalSize - 0.5, row / internalSize - 0.42) * 1.6, 1);
      const color = [0, 1, 2].map(channel => {
        const background = inner[channel] + (outer[channel] - inner[channel]) * centerDistance;
        return (pixels[offset + channel] / 255) * alpha + background * (1 - alpha);
      });
      if (stars && alpha < 0.2) {
        const starCellX = Math.floor(column / pixelScale);
        const starCellY = Math.floor(row / pixelScale);
        const star = hashNoise(starCellX * 1.3, starCellY * 2.1, 9.7);
        if (star > 0.993) {
          const twinkle = 0.5 + 0.5 * Math.sin(time * 3 + star * 400);
          for (let channel = 0; channel < 3; channel++) color[channel] += 0.4 * twinkle;
        }
      }
      if (moon && alpha < 0.5) {
        const moonDistance = Math.hypot(column / internalSize - moon.x, row / internalSize - moon.y);
        const cover = 1 - alpha * 2;
        if (moonDistance < moon.radius) {
          const crater = valueNoise(column / internalSize * 40, row / internalSize * 40, 1) > 0.62 ? 0.82 : 1;
          for (let channel = 0; channel < 3; channel++) color[channel] = color[channel] * (1 - cover) + moon.color[channel] * crater * cover;
        } else {
          const halo = Math.pow(Math.max(1 - (moonDistance - moon.radius) / (moon.radius * 3.2), 0), 2) * 0.45 * cover;
          for (let channel = 0; channel < 3; channel++) color[channel] += moon.halo[channel] * halo;
        }
      }
      if (clouds && alpha < 0.6) {
        const cloudX = column / internalSize * 3 + time * 0.035;
        const cloudY = row / internalSize * 7;
        const density = valueNoise(cloudX, cloudY, 3) * 0.65 + valueNoise(cloudX * 2.3, cloudY * 2.3, 5) * 0.35;
        const band = Math.max(0, 1 - Math.abs(row / internalSize - 0.24) * 3.2);
        const amount = Math.max(density - 0.5, 0) * 2.2 * band * (1 - alpha);
        for (let channel = 0; channel < 3; channel++) color[channel] = color[channel] * (1 - amount * 0.8) + clouds[channel] * amount * 0.8;
      }
      if (flash > 0) {
        for (let channel = 0; channel < 3; channel++) color[channel] = color[channel] * (1 + flash * 1.4) + flash * [0.16, 0.18, 0.26][channel] * (1 - alpha * 0.5);
      }
      for (const glow of glows) {
        const distance = Math.hypot(column - glow.screenX, row - glow.screenY);
        if (distance < glow.radiusPixels) {
          const falloff = Math.pow(1 - distance / glow.radiusPixels, 2) * glow.strength;
          for (let channel = 0; channel < 3; channel++) color[channel] += glow.color[channel] * falloff;
        }
      }
      if (isOutline[pixelIndex]) for (let channel = 0; channel < 3; channel++) color[channel] = outlineColor[channel];
      buffer.set(color, pixelIndex * 3);
    }
  }
  applyDreamyHaze(buffer, internalSize, scene.haze ?? null);
  for (let row = 0; row < internalSize; row++) {
    for (let column = 0; column < internalSize; column++) {
      const pixelIndex = row * internalSize + column;
      const offset = pixelIndex * 4;
      const color = [buffer[pixelIndex * 3], buffer[pixelIndex * 3 + 1], buffer[pixelIndex * 3 + 2]];
      if (fadeToBlack > 0) for (let channel = 0; channel < 3; channel++) color[channel] *= 1 - fadeToBlack;
      if (palette) {
        const threshold = BAYER[(row % 4) * 4 + (column % 4)] - 0.5;
        const ditheredColor = color.map(value => value + threshold * style.dither);
        let best = palette[0];
        let bestDistance = Infinity;
        for (const entry of palette) {
          const red = ditheredColor[0] - entry[0];
          const green = ditheredColor[1] - entry[1];
          const blue = ditheredColor[2] - entry[2];
          const distance = red * red * 0.3 + green * green * 0.59 + blue * blue * 0.11;
          if (distance < bestDistance) {
            bestDistance = distance;
            best = entry;
          }
        }
        for (let channel = 0; channel < 3; channel++) pixels[offset + channel] = Math.round(best[channel] * 255);
      } else {
        for (let channel = 0; channel < 3; channel++) pixels[offset + channel] = Math.round(Math.min(Math.max(color[channel], 0), 1) * 255);
      }
      pixels[offset + 3] = 255;
    }
  }
  readerContext.putImageData(image, 0, 0);
  const output = document.createElement('canvas');
  output.width = outputSize;
  output.height = outputSize;
  const outputContext = output.getContext('2d');
  outputContext.imageSmoothingEnabled = false;
  outputContext.drawImage(reader, 0, 0, outputSize, outputSize);
  return output.toDataURL('image/png');
}

// options: { time, internalSize, outputSize, style: { palette, dither, paletteSteps, splatScale }, camera: {...},
//   assemble, dissolve, fadeToBlack }
window.renderFrame = function renderFrame(options) {
  const scene = state.scene;
  const time = options.time;
  const staticLists = animateStatic(scene, time, options);
  const dynamicLists = scene.dynamic(time);
  if ((options.dissolve ?? 0) > 0) {
    for (const list of dynamicLists) {
      const colors = new Float32Array(list.colors);
      for (let index = 0; index < list.count; index++) colors[index * 4 + 3] *= Math.max(1 - options.dissolve * 2.5, 0);
      list.colors = colors;
    }
  }
  if ((options.assemble ?? 1) < 1) {
    for (const list of dynamicLists) {
      const colors = new Float32Array(list.colors);
      for (let index = 0; index < list.count; index++) colors[index * 4 + 3] *= Math.max((options.assemble - 0.75) * 4, 0);
      list.colors = colors;
    }
  }
  const fade = Math.max(1 - (options.dissolve ?? 0) * 1.5, 0) * Math.min(Math.max(((options.assemble ?? 1) - 0.4) * 2, 0), 1);
  const atmosphere = atmosphereSplats(scene, time, fade);
  const lists = [...staticLists, ...dynamicLists, ...atmosphere.lists];
  scene.extraGlows = atmosphere.glows;
  const splatScale = options.style.splatScale ?? 1;
  const scaledLists = splatScale === 1 ? lists : lists.map(list => ({ ...list, scales: list.scales.map(value => value * splatScale) }));
  const data = packSplatData(scaledLists.filter(list => list.count > 0));
  const renderer = getRenderer(options.internalSize);
  const splats = createGaussianSplats(data, { maximumCount: 3_000_000 });
  const detach = attachGaussianSplats(renderer, splats);
  renderer.render(cameraFor(scene, time, options.camera ?? {}));
  const url = postProcess(scene, renderer, time, options.internalSize, options.style, options.outputSize, options.fadeToBlack ?? 0, options.flash ?? 0);
  detach();
  return { url, splatCount: data.count };
};

window.pageReady = true;
