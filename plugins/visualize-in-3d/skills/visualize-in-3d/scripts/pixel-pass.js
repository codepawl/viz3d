// Pixel pass for three.js: a real 3D scene drawn at a low internal resolution and upscaled with nearest-neighbour
// sampling, with outlines from depth and normal edges, optional palette quantising, a dither-dissolve material
// helper and a pixel-snapped orthographic camera. Used by the "pixel diorama" look (references/looks.md).
//
// Copy this file into an app (src/pixel-pass.js); it only imports "three" (tested with 0.186).
//
//   const pass = new PixelPass(renderer, { pixelScale: 5, outlineColor: 0x1b1722 });
//   pass.setSize(window.innerWidth, window.innerHeight);           // canvas pixels, pixel ratio 1
//   const residual = snapOrthographicCamera(camera, { focus, azimuthDegrees: 45, elevationDegrees: 30,
//       distance: 120, viewHeight: 40, lowResWidth: pass.lowResWidth, lowResHeight: pass.lowResHeight });
//   pass.render(scene, camera, residual);                            // every frame instead of renderer.render

import * as THREE from 'three';

const MAXIMUM_PALETTE_COLORS = 32;

const BAYER_FUNCTION_GLSL = /* glsl */ `
float bayer4(vec2 pixelCoordinate) {
  vec2 cell = mod(floor(pixelCoordinate), 4.0);
  float index = cell.x + cell.y * 4.0;
  // 4x4 Bayer matrix, values 0..15, laid out row by row.
  float values[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);
  return (values[int(index)] + 0.5) / 16.0;
}
`;

const FULLSCREEN_VERTEX_SHADER = /* glsl */ `
void main() {
  gl_Position = vec4(position.xy, 0.0, 1.0);
}
`;

const COMPOSITE_FRAGMENT_SHADER = /* glsl */ `
precision highp float;
uniform sampler2D colorTexture;
uniform sampler2D depthTexture;
uniform sampler2D normalTexture;
uniform vec2 lowResSize;        // size of the render target in texels (includes the 1 px margin)
uniform vec2 residual;          // sub-pixel camera offset in low-res pixels
uniform float pixelScale;       // canvas pixels per low-res pixel
uniform float cameraNear;
uniform float cameraFar;
uniform vec3 outlineColor;
uniform float outlineTint;      // 0 = flat outline colour, 1 = outline takes the darkened colour of the near object
uniform float depthEdgeThreshold;   // world units
uniform float normalEdgeThreshold;  // 0..2, difference of unit normals
uniform float creaseDarkness;       // 0 = no inner lines
uniform int paletteSize;
uniform vec3 palette[${MAXIMUM_PALETTE_COLORS}];
uniform float paletteDither;

${BAYER_FUNCTION_GLSL}

float worldDepth(vec2 texel) {
  float raw = texture2D(depthTexture, (texel + 0.5) / lowResSize).x;
  return cameraNear + raw * (cameraFar - cameraNear);
}

vec3 normalAt(vec2 texel) {
  return texture2D(normalTexture, (texel + 0.5) / lowResSize).xyz * 2.0 - 1.0;
}

vec3 colorAt(vec2 texel) {
  return texture2D(colorTexture, (texel + 0.5) / lowResSize).rgb;
}

vec3 quantise(vec3 color, vec2 lowCoordinate) {
  if (paletteSize == 0) return color;
  float bias = (bayer4(lowCoordinate) - 0.5) * paletteDither;
  vec3 biased = color + bias;
  float bestDistance = 1e9;
  vec3 best = palette[0];
  for (int index = 0; index < ${MAXIMUM_PALETTE_COLORS}; index++) {
    if (index >= paletteSize) break;
    vec3 difference = biased - palette[index];
    float distanceSquared = dot(difference, difference);
    if (distanceSquared < bestDistance) {
      bestDistance = distanceSquared;
      best = palette[index];
    }
  }
  return best;
}

void main() {
  // Canvas pixel -> low-res texel. The +1 skips the margin, the residual slides the image by the camera's
  // sub-pixel offset so the camera moves smoothly while the pixels themselves never shimmer.
  vec2 lowCoordinate = gl_FragCoord.xy / pixelScale + residual + 1.0;
  vec2 texel = floor(lowCoordinate);

  vec3 color = colorAt(texel);
  float centerDepth = worldDepth(texel);
  vec3 centerNormal = normalAt(texel);

  vec2 offsets[4] = vec2[4](vec2(1.0, 0.0), vec2(-1.0, 0.0), vec2(0.0, 1.0), vec2(0.0, -1.0));
  float nearestNeighbourDepth = centerDepth;
  vec3 nearestNeighbourColor = color;
  float creaseAmount = 0.0;
  for (int index = 0; index < 4; index++) {
    vec2 neighbour = texel + offsets[index];
    float neighbourDepth = worldDepth(neighbour);
    if (neighbourDepth < nearestNeighbourDepth) {
      nearestNeighbourDepth = neighbourDepth;
      nearestNeighbourColor = colorAt(neighbour);
    }
    if (abs(neighbourDepth - centerDepth) < depthEdgeThreshold) {
      float normalDifference = length(normalAt(neighbour) - centerNormal);
      creaseAmount = max(creaseAmount, step(normalEdgeThreshold, normalDifference));
    }
  }

  // Outline: this pixel lies behind a clearly nearer neighbour, so the line is drawn just outside the silhouette.
  float isOutline = step(depthEdgeThreshold, centerDepth - nearestNeighbourDepth);
  vec3 lineColor = mix(outlineColor, nearestNeighbourColor * 0.35, outlineTint);
  color = mix(color, color * (1.0 - creaseDarkness), creaseAmount);
  color = quantise(color, lowCoordinate);
  color = mix(color, lineColor, isOutline);

  gl_FragColor = vec4(color, 1.0);
  #include <colorspace_fragment>
}
`;

// A stepped gradient map for MeshToonMaterial: "tones" flat bands from dark to light, no smoothing.
export function createToonGradient(tones = 3, darkest = 0.45) {
  const data = new Uint8Array(tones * 4);
  for (let tone = 0; tone < tones; tone++) {
    const level = tones === 1 ? 1 : darkest + (1 - darkest) * (tone / (tones - 1));
    const byte = Math.round(level * 255);
    data.set([byte, byte, byte, 255], tone * 4);
  }
  const texture = new THREE.DataTexture(data, tones, 1, THREE.RGBAFormat);
  texture.minFilter = THREE.NearestFilter;
  texture.magFilter = THREE.NearestFilter;
  texture.generateMipmaps = false;
  texture.needsUpdate = true;
  return texture;
}

const gradientCache = new Map();

// Flat toon material with 3 to 4 tones. Casts and receives real shadows through the scene's directional light.
export function createToonMaterial(color, options = {}) {
  const tones = options.tones ?? 3;
  const darkest = options.darkest ?? 0.5;
  const cacheKey = `${tones}:${darkest}`;
  if (!gradientCache.has(cacheKey)) gradientCache.set(cacheKey, createToonGradient(tones, darkest));
  return new THREE.MeshToonMaterial({ color, gradientMap: gradientCache.get(cacheKey), ...options.materialOptions });
}

// Adds an ordered-dither dissolve to any material. The returned object holds `amount` (0 = solid, 1 = gone);
// materials that share one controller dissolve together. The Bayer pattern is read in low-res pixels because
// the scene is drawn at the low resolution, so the dither cells are real pixels.
export function addDitherDissolve(material, controller = { amount: 0 }) {
  const previousHook = material.onBeforeCompile;
  material.onBeforeCompile = (shader, renderer) => {
    if (previousHook) previousHook(shader, renderer);
    shader.uniforms.ditherAmount = controller.uniform ?? (controller.uniform = { value: controller.amount });
    shader.fragmentShader = shader.fragmentShader
      .replace('void main() {', `uniform float ditherAmount;\n${BAYER_FUNCTION_GLSL}\nvoid main() {`)
      .replace('#include <clipping_planes_fragment>', `#include <clipping_planes_fragment>\n  if (bayer4(gl_FragCoord.xy) < ditherAmount) discard;`);
  };
  material.customProgramCacheKey = () => 'dither-dissolve';
  material.needsUpdate = true;
  controller.uniform = controller.uniform ?? { value: controller.amount };
  controller.set = (amount) => {
    controller.amount = amount;
    controller.uniform.value = amount;
  };
  return controller;
}

// Places an orthographic camera on the low-res pixel grid and returns the sub-pixel residual (in low-res pixels)
// for PixelPass.render. The camera looks at `focus` from the given compass azimuth and elevation. Snapping the
// camera to whole low-res pixels along its own right and up axes keeps every texel of the world on a texel of
// the image while the focus moves continuously, which removes shimmer; the residual is applied when upscaling.
export function snapOrthographicCamera(camera, settings) {
  const { focus, azimuthDegrees, elevationDegrees, distance, viewHeight, lowResWidth, lowResHeight } = settings;
  const azimuth = THREE.MathUtils.degToRad(azimuthDegrees);
  const elevation = THREE.MathUtils.degToRad(elevationDegrees);
  const toCamera = new THREE.Vector3(
    Math.sin(azimuth) * Math.cos(elevation),
    Math.sin(elevation),
    Math.cos(azimuth) * Math.cos(elevation),
  );
  const worldUp = new THREE.Vector3(0, 1, 0);
  const right = new THREE.Vector3().crossVectors(worldUp, toCamera).normalize();
  const up = new THREE.Vector3().crossVectors(toCamera, right).normalize();

  const unitsPerPixel = viewHeight / lowResHeight;
  const rightCoordinate = focus.dot(right);
  const upCoordinate = focus.dot(up);
  const snappedRight = Math.round(rightCoordinate / unitsPerPixel) * unitsPerPixel;
  const snappedUp = Math.round(upCoordinate / unitsPerPixel) * unitsPerPixel;
  const snappedFocus = focus
    .clone()
    .addScaledVector(right, snappedRight - rightCoordinate)
    .addScaledVector(up, snappedUp - upCoordinate);

  // The render target has a one pixel margin on every side, so the frustum covers two extra pixels.
  const halfHeight = ((lowResHeight + 2) * unitsPerPixel) / 2;
  const halfWidth = ((lowResWidth + 2) * unitsPerPixel) / 2;
  camera.left = -halfWidth;
  camera.right = halfWidth;
  camera.top = halfHeight;
  camera.bottom = -halfHeight;
  camera.near = 0.5;
  camera.far = distance * 2.2;
  camera.position.copy(snappedFocus).addScaledVector(toCamera, distance);
  camera.up.set(0, 1, 0);
  camera.lookAt(snappedFocus);
  camera.updateProjectionMatrix();
  camera.updateMatrixWorld(true);

  return new THREE.Vector2(
    (rightCoordinate - snappedRight) / unitsPerPixel,
    (upCoordinate - snappedUp) / unitsPerPixel,
  );
}

export class PixelPass {
  constructor(renderer, options = {}) {
    this.renderer = renderer;
    this.pixelScale = options.pixelScale ?? 5;
    this.backgroundColor = new THREE.Color(options.backgroundColor ?? 0xf4f1e8);
    this.lowResWidth = 1;
    this.lowResHeight = 1;

    this.colorTarget = null;
    this.normalTarget = null;
    this.normalMaterial = new THREE.MeshNormalMaterial();

    this.compositeMaterial = new THREE.ShaderMaterial({
      vertexShader: FULLSCREEN_VERTEX_SHADER,
      fragmentShader: COMPOSITE_FRAGMENT_SHADER,
      depthTest: false,
      depthWrite: false,
      uniforms: {
        colorTexture: { value: null },
        depthTexture: { value: null },
        normalTexture: { value: null },
        lowResSize: { value: new THREE.Vector2(1, 1) },
        residual: { value: new THREE.Vector2() },
        pixelScale: { value: this.pixelScale },
        cameraNear: { value: 0.5 },
        cameraFar: { value: 100 },
        outlineColor: { value: new THREE.Color(options.outlineColor ?? 0x1b1722) },
        outlineTint: { value: options.outlineTint ?? 0.35 },
        depthEdgeThreshold: { value: options.depthEdgeThreshold ?? 0.55 },
        normalEdgeThreshold: { value: options.normalEdgeThreshold ?? 0.9 },
        creaseDarkness: { value: options.creaseDarkness ?? 0.22 },
        paletteSize: { value: 0 },
        palette: { value: Array.from({ length: MAXIMUM_PALETTE_COLORS }, () => new THREE.Color()) },
        paletteDither: { value: options.paletteDither ?? 0.0 },
      },
    });
    this.quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.compositeMaterial);
    this.quad.frustumCulled = false;
    this.quadScene = new THREE.Scene();
    this.quadScene.add(this.quad);
    this.quadCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

    if (options.palette) this.setPalette(options.palette);
  }

  // Hex colours (sRGB). Pass null to switch quantising off. At most 32 colours.
  setPalette(hexColors, ditherStrength = this.compositeMaterial.uniforms.paletteDither.value) {
    const uniforms = this.compositeMaterial.uniforms;
    if (!hexColors || hexColors.length === 0) {
      uniforms.paletteSize.value = 0;
      return;
    }
    const count = Math.min(hexColors.length, MAXIMUM_PALETTE_COLORS);
    for (let index = 0; index < count; index++) uniforms.palette.value[index].set(hexColors[index]);
    uniforms.paletteSize.value = count;
    uniforms.paletteDither.value = ditherStrength;
  }

  setBackground(color) {
    this.backgroundColor.set(color);
  }

  // Canvas size in pixels. Keep the renderer's pixel ratio at 1 so the pixel scale is exact.
  setSize(canvasWidth, canvasHeight) {
    this.renderer.setPixelRatio(1);
    this.renderer.setSize(canvasWidth, canvasHeight, false);
    this.lowResWidth = Math.ceil(canvasWidth / this.pixelScale);
    this.lowResHeight = Math.ceil(canvasHeight / this.pixelScale);
    this.colorTarget?.dispose();
    this.normalTarget?.dispose();
    const width = this.lowResWidth + 2;
    const height = this.lowResHeight + 2;
    this.colorTarget = new THREE.WebGLRenderTarget(width, height, {
      type: THREE.HalfFloatType,
      minFilter: THREE.NearestFilter,
      magFilter: THREE.NearestFilter,
      depthBuffer: true,
      samples: 0,
    });
    this.colorTarget.depthTexture = new THREE.DepthTexture(width, height);
    this.colorTarget.depthTexture.minFilter = THREE.NearestFilter;
    this.colorTarget.depthTexture.magFilter = THREE.NearestFilter;
    this.normalTarget = new THREE.WebGLRenderTarget(width, height, {
      type: THREE.UnsignedByteType,
      minFilter: THREE.NearestFilter,
      magFilter: THREE.NearestFilter,
      depthBuffer: true,
    });
    this.compositeMaterial.uniforms.lowResSize.value.set(width, height);
    this.compositeMaterial.uniforms.pixelScale.value = this.pixelScale;
  }

  // Draws the scene to the canvas. `residual` comes from snapOrthographicCamera.
  render(scene, camera, residual = new THREE.Vector2()) {
    const renderer = this.renderer;
    const previousBackground = scene.background;
    const previousAutoUpdate = renderer.shadowMap.autoUpdate;

    scene.background = this.backgroundColor;
    renderer.setRenderTarget(this.colorTarget);
    renderer.clear();
    renderer.render(scene, camera);

    // Normal pass for crease lines. Objects flagged userData.skipNormalPass (dissolving smoke) are hidden in it.
    const hidden = [];
    scene.traverse((object) => {
      if (object.visible && object.userData.skipNormalPass) {
        object.visible = false;
        hidden.push(object);
      }
    });
    scene.background = new THREE.Color(0x8080ff);
    scene.overrideMaterial = this.normalMaterial;
    renderer.shadowMap.autoUpdate = false;
    renderer.setRenderTarget(this.normalTarget);
    renderer.clear();
    renderer.render(scene, camera);
    renderer.shadowMap.autoUpdate = previousAutoUpdate;
    scene.overrideMaterial = null;
    scene.background = previousBackground;
    for (const object of hidden) object.visible = true;

    const uniforms = this.compositeMaterial.uniforms;
    uniforms.colorTexture.value = this.colorTarget.texture;
    uniforms.depthTexture.value = this.colorTarget.depthTexture;
    uniforms.normalTexture.value = this.normalTarget.texture;
    uniforms.residual.value.copy(residual);
    uniforms.cameraNear.value = camera.near;
    uniforms.cameraFar.value = camera.far;
    renderer.setRenderTarget(null);
    renderer.render(this.quadScene, this.quadCamera);
  }
}
