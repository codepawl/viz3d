// What a human arm can do, for any mannequin with upperarm_/lowerarm_/hand_ bones (Quaternius, UE-style).
// A hand on a prop used to take its whole rotation from the prop, whatever that did to the wrist: the man held the cartridge with
// the wrist bent 149 degrees and sideways 130. Here a grip says only what the contact fixes (the
// palm's normal on a flat face, the thumb-side axis along an edge) and the hand takes the rest from the forearm, then the result is
// clamped into the comfortable range. tools/film.mjs fails a render when any visible arm passes the anatomical range.
// Angles come from the bone positions and the hand's axes only, so they measure what the viewer sees, not how a bone happens to roll.
import * as THREE from 'three'

// Degrees. Anatomical range: standard goniometry reference values (elbow 0-145; forearm pronation 80, supination 85; wrist flexion
// 80, extension 70, radial 20, ulnar 30). Comfort: functional wrist motion is about 40 each way (Palmer 1985, Ryu 1991), and a held
// grip keeps inside that; a push may extend further, which `GRIP_COMFORT` allows.
export const ARM_LIMITS = { elbowFlexion: 145, pronation: 80, supination: 85, wristFlexion: 80, wristExtension: 70, radial: 20, ulnar: 30 }
export const GRIP_COMFORT = { pronation: 70, supination: 75, wristFlexion: 40, wristExtension: 55, radial: 12, ulnar: 22 }
// With the elbow nearly straight the forearm's rotation cannot be told from the shoulder's, so it is neither clamped nor checked.
const ELBOW_BENT_ENOUGH = { from: 10, to: 30 }

const DEGREES = 180 / Math.PI
const vector = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z)
const smooth = (value) => {
  const clamped = Math.min(1, Math.max(0, value))
  return clamped * clamped * (3 - 2 * clamped)
}

// Hand bone axes, measured from the finger bones of this rig: fingers along local +y, the index side +z on both hands, and the palm
// (where the fingers curl and the thumb sits) local -x on the right hand and +x on the left.
export const palmLocal = (side) => vector(side === 'r' ? -1 : 1, 0, 0)
const FINGERS_LOCAL = vector(0, 1, 0)
const INDEX_LOCAL = vector(0, 0, 1)

// The hand's world rotation for a palm direction and a finger direction (made perpendicular to the palm).
export function handFromPalm(side, palm, fingers) {
  const palmUnit = palm.clone().normalize()
  const fingersUnit = fingers.clone().addScaledVector(palmUnit, -fingers.dot(palmUnit)).normalize()
  const index = palmUnit.clone().cross(fingersUnit)
  if (side === 'r') index.negate()
  const localX = side === 'r' ? palmUnit.clone().negate() : palmUnit
  return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(localX, fingersUnit, index))
}

// The hand's world rotation for an edge it wraps: the index side along `edge`, the fingers (made perpendicular to it) across.
export function handFromEdge(side, edge, fingers) {
  const edgeUnit = edge.clone().normalize()
  const fingersUnit = fingers.clone().addScaledVector(edgeUnit, -fingers.dot(edgeUnit)).normalize()
  const palm = side === 'r' ? edgeUnit.clone().cross(fingersUnit) : fingersUnit.clone().cross(edgeUnit)
  return handFromPalm(side, palm, fingersUnit)
}

// Puts a held prop on the hand, so it goes wherever the arm goes: run it after the arm is posed, every frame. `socket` is a child of
// the prop with userData.grip { palm or edge, fingers } in the prop's axes and `contact` a child of the hand bone at the grip point.
// `weight` below 1 leaves part of the pose to whatever else moves the prop, such as the rails it slides out of.
export function carryProp(prop, socket, side, contact, weight = 1) {
  const { palm, edge, fingers } = socket.userData.grip
  const handInProp = palm ? handFromPalm(side, palm, fingers) : handFromEdge(side, edge, fingers)
  const propWorld = contact.getWorldQuaternion(new THREE.Quaternion()).multiply(handInProp.invert())
  const propWorldPosition = contact.getWorldPosition(vector()).sub(socket.position.clone().applyQuaternion(propWorld))
  const parentWorld = prop.parent.getWorldQuaternion(new THREE.Quaternion())
  prop.quaternion.slerp(parentWorld.invert().multiply(propWorld), weight)
  prop.position.lerp(prop.parent.worldToLocal(propWorldPosition), weight)
  prop.updateWorldMatrix(true, true)
}

// Shoulder, elbow and wrist of one arm, and the forearm's rotation: 0 is a handshake (palm toward the body's middle), positive turns
// the palm toward the upper arm's far side (pronation, palm down with the elbow at a right angle).
function armGeometry(bones, side) {
  const shoulder = bones['upperarm_' + side].getWorldPosition(vector())
  const elbow = bones['lowerarm_' + side].getWorldPosition(vector())
  const wrist = bones['hand_' + side].getWorldPosition(vector())
  return { upper: elbow.clone().sub(shoulder).normalize(), forearm: wrist.clone().sub(elbow).normalize() }
}

function forearmRotation(side, upper, forearm, palm) {
  const hinge = upper.clone().cross(forearm).normalize()
  const towardMiddle = side === 'r' ? hinge.negate() : hinge
  const palmFlat = palm.clone().addScaledVector(forearm, -palm.dot(forearm)).normalize()
  const upperFlat = upper.clone().addScaledVector(forearm, -upper.dot(forearm)).normalize()
  return Math.atan2(palmFlat.dot(upperFlat), palmFlat.dot(towardMiddle))
}

function wristAngles(forearm, palm, fingers, index) {
  const along = forearm.dot(fingers)
  return { flexion: Math.atan2(-forearm.dot(palm), along), radial: Math.atan2(-forearm.dot(index), along) }
}

export function armAngles(bones, side) {
  bones['hand_' + side].updateWorldMatrix(true, false)
  const { upper, forearm } = armGeometry(bones, side)
  const rotation = bones['hand_' + side].getWorldQuaternion(new THREE.Quaternion())
  const palm = palmLocal(side).applyQuaternion(rotation)
  const fingers = FINGERS_LOCAL.clone().applyQuaternion(rotation)
  const index = INDEX_LOCAL.clone().applyQuaternion(rotation)
  const wrist = wristAngles(forearm, palm, fingers, index)
  const elbowFlexion = Math.acos(Math.min(1, Math.max(-1, upper.dot(forearm)))) * DEGREES
  return {
    elbowFlexion,
    rotation: elbowFlexion > ELBOW_BENT_ENOUGH.to ? forearmRotation(side, upper, forearm, palm) * DEGREES : null,
    flexion: wrist.flexion * DEGREES,
    radial: wrist.radial * DEGREES,
  }
}

// Puts an angle inside its range without a jump. Clamping to the nearer end flips the joint from one end to the other when the wanted
// angle passes through the unreachable side: a 17 cm one-frame hand pop. Here the angle walks back through the range
// while the wanted angle crosses the unreachable arc, so the result is continuous all the way round.
function foldIntoRange(angle, low, high) {
  if (angle >= low && angle <= high) return angle
  const fullTurn = 2 * Math.PI
  const pastHigh = ((angle - high) % fullTurn + fullTurn) % fullTurn
  return high - ((high - low) * pastHigh) / (fullTurn - (high - low))
}

// A hand rotation near `hand` whose wrist and forearm stay inside `limits`, for this upper arm and forearm.
export function limitHand(hand, side, upper, forearm, limits = GRIP_COMFORT) {
  const limited = hand.clone()
  const palm = palmLocal(side).applyQuaternion(limited)
  const elbowFlexion = Math.acos(Math.min(1, Math.max(-1, upper.dot(forearm)))) * DEGREES
  const rollWeight = smooth((elbowFlexion - ELBOW_BENT_ENOUGH.from) / (ELBOW_BENT_ENOUGH.to - ELBOW_BENT_ENOUGH.from))
  if (rollWeight > 0) {
    const rotation = forearmRotation(side, upper, forearm, palm)
    const allowed = foldIntoRange(rotation, -limits.supination / DEGREES, limits.pronation / DEGREES)
    // A turn about the forearm raises the rotation on the left arm and lowers it on the right: the two palms mirror each other.
    const sign = side === 'r' ? 1 : -1
    limited.premultiply(new THREE.Quaternion().setFromAxisAngle(forearm, sign * (rotation - allowed) * rollWeight))
  }
  const palmNow = palmLocal(side).applyQuaternion(limited)
  const fingersNow = FINGERS_LOCAL.clone().applyQuaternion(limited)
  const indexNow = INDEX_LOCAL.clone().applyQuaternion(limited)
  const wrist = wristAngles(forearm, palmNow, fingersNow, indexNow)
  const flexion = foldIntoRange(wrist.flexion, -limits.wristExtension / DEGREES, limits.wristFlexion / DEGREES)
  const radial = foldIntoRange(wrist.radial, -limits.ulnar / DEGREES, limits.radial / DEGREES)
  // Where the forearm should lie in the hand's own axes, then the smallest turn that puts it there.
  const forearmWanted = fingersNow.clone().addScaledVector(palmNow, -Math.tan(flexion)).addScaledVector(indexNow, -Math.tan(radial)).normalize()
  return limited.premultiply(new THREE.Quaternion().setFromUnitVectors(forearmWanted, forearm))
}

// The last stop for any posed arm, a stock clip included (the walk clip swings the wrists 26 degrees toward the thumb): turns the
// hand back inside the anatomical range, two degrees short of it. An arm already inside is left exactly as it is.
const LAST_STOP = Object.fromEntries(Object.entries(ARM_LIMITS).map(([joint, limit]) => [joint, limit - 2]))
export function keepArmInRange(bones, side) {
  const hand = bones['hand_' + side]
  hand.updateWorldMatrix(true, false)
  const { upper, forearm } = armGeometry(bones, side)
  const rotation = limitHand(hand.getWorldQuaternion(new THREE.Quaternion()), side, upper, forearm, LAST_STOP)
  const parentRotation = hand.parent.getWorldQuaternion(new THREE.Quaternion())
  hand.quaternion.copy(parentRotation.invert().multiply(rotation))
  hand.updateWorldMatrix(false, true)
}

// Which way the arm's bones roll, read from a relaxed clip pose (the rig has no twist bones). `twoBoneArm` keeps the elbow bending
// about the rig's own hinge, so the skin folds where an elbow folds.
export function captureArmRest(bones, side) {
  const upperBone = bones['upperarm_' + side]
  const lowerBone = bones['lowerarm_' + side]
  const handBone = bones['hand_' + side]
  handBone.updateWorldMatrix(true, false)
  const { upper, forearm } = armGeometry(bones, side)
  const hinge = upper.clone().cross(forearm).normalize()
  return {
    upperHinge: hinge.clone().applyQuaternion(upperBone.getWorldQuaternion(new THREE.Quaternion()).invert()),
    lowerHinge: hinge.clone().applyQuaternion(lowerBone.getWorldQuaternion(new THREE.Quaternion()).invert()),
    handInLower: handBone.quaternion.clone(),
  }
}

// Turns `bone` about `axis` (world) so its local `localDirection` lies as close to `wanted` as a turn about that axis can put it.
function rollBoneTo(bone, axis, localDirection, wanted) {
  const rotation = bone.getWorldQuaternion(new THREE.Quaternion())
  const current = localDirection.clone().applyQuaternion(rotation)
  const currentFlat = current.addScaledVector(axis, -current.dot(axis))
  const wantedFlat = wanted.clone().addScaledVector(axis, -wanted.dot(axis))
  if (currentFlat.lengthSq() < 1e-6 || wantedFlat.lengthSq() < 1e-6) return
  const angle = Math.atan2(currentFlat.clone().cross(wantedFlat).dot(axis), currentFlat.dot(wantedFlat))
  rotateBoneWorld(bone, axis, angle)
}

function rotateBoneWorld(bone, axis, angle) {
  const rotation = bone.getWorldQuaternion(new THREE.Quaternion()).premultiply(new THREE.Quaternion().setFromAxisAngle(axis, angle))
  const parentRotation = bone.parent.getWorldQuaternion(new THREE.Quaternion())
  bone.quaternion.copy(parentRotation.invert().multiply(rotation))
  bone.updateWorldMatrix(false, true)
}

function aimBone(bone, tipBone, target) {
  bone.updateWorldMatrix(true, true)
  const origin = bone.getWorldPosition(vector())
  const current = tipBone.getWorldPosition(vector()).sub(origin).normalize()
  const desired = target.clone().sub(origin).normalize()
  rotateBoneByDelta(bone, new THREE.Quaternion().setFromUnitVectors(current, desired))
}

function rotateBoneByDelta(bone, delta) {
  const rotation = bone.getWorldQuaternion(new THREE.Quaternion()).premultiply(delta)
  const parentRotation = bone.parent.getWorldQuaternion(new THREE.Quaternion())
  bone.quaternion.copy(parentRotation.invert().multiply(rotation))
  bone.updateWorldMatrix(false, true)
}

// Two-bone IK with a pole: puts the wrist at `target` (clamped to the arm's reach), the elbow bending toward `pole`, and each bone
// rolled so the elbow folds about the rig's own hinge. Returns how far the wrist falls short.
export function twoBoneArm(bones, side, rest, target, pole) {
  const upperBone = bones['upperarm_' + side]
  const lowerBone = bones['lowerarm_' + side]
  const handBone = bones['hand_' + side]
  upperBone.updateWorldMatrix(true, true)
  const shoulder = upperBone.getWorldPosition(vector())
  const elbow = lowerBone.getWorldPosition(vector())
  const wrist = handBone.getWorldPosition(vector())
  const upperLength = elbow.distanceTo(shoulder)
  const lowerLength = wrist.distanceTo(elbow)
  const toTarget = target.clone().sub(shoulder)
  const wanted = toTarget.length()
  const distance = Math.min(wanted, (upperLength + lowerLength) * 0.9999)
  const axis = toTarget.normalize()
  const along = (upperLength ** 2 - lowerLength ** 2 + distance ** 2) / (2 * distance)
  const height = Math.sqrt(Math.max(0, upperLength ** 2 - along ** 2))
  const perpendicular = pole.clone().addScaledVector(axis, -pole.dot(axis)).normalize()
  const elbowTarget = shoulder.clone().addScaledVector(axis, along).addScaledVector(perpendicular, height)
  const wristTarget = shoulder.clone().addScaledVector(axis, distance)
  const hinge = perpendicular.clone().cross(axis).normalize()
  aimBone(upperBone, lowerBone, elbowTarget)
  rollBoneTo(upperBone, elbowTarget.clone().sub(shoulder).normalize(), rest.upperHinge, hinge)
  aimBone(lowerBone, handBone, wristTarget)
  rollBoneTo(lowerBone, wristTarget.clone().sub(elbowTarget).normalize(), rest.lowerHinge, hinge)
  return wanted - distance
}

// Without a twist bone, all the forearm's rotation would wring the skin at one joint. The lower arm takes this share and the wrist
// keeps the rest, the way the radius turns along the length of a real forearm.
const FOREARM_ROLL_SHARE = 0.6
export function shareForearmRoll(bones, side, rest, handRotation) {
  const lowerBone = bones['lowerarm_' + side]
  const handBone = bones['hand_' + side]
  lowerBone.updateWorldMatrix(true, true)
  const axis = handBone.getWorldPosition(vector()).sub(lowerBone.getWorldPosition(vector())).normalize()
  const lowerRotation = lowerBone.getWorldQuaternion(new THREE.Quaternion())
  const lowerWanted = handRotation.clone().multiply(rest.handInLower.clone().invert())
  const current = rest.lowerHinge.clone().applyQuaternion(lowerRotation)
  const wanted = rest.lowerHinge.clone().applyQuaternion(lowerWanted)
  const currentFlat = current.addScaledVector(axis, -current.dot(axis))
  const wantedFlat = wanted.addScaledVector(axis, -wanted.dot(axis))
  if (currentFlat.lengthSq() < 1e-6 || wantedFlat.lengthSq() < 1e-6) return
  const angle = Math.atan2(currentFlat.clone().cross(wantedFlat).dot(axis), currentFlat.dot(wantedFlat))
  rotateBoneWorld(lowerBone, axis, angle * FOREARM_ROLL_SHARE)
}

// The film's check: every mannequin registers its arms, and tools/film.mjs reads measureWatchedArms() on each frame.
const watchedArms = []
export function watchArms(name, bones, group) {
  watchedArms.push({ name, bones, group })
}

function isShown(object) {
  for (let node = object; node; node = node.parent) {
    if (!node.visible) return false
  }
  return true
}

export function measureWatchedArms() {
  const faults = []
  const largest = {}
  watchedArms.forEach(({ name, bones, group }) => {
    if (!bones.hand_r || !isShown(group)) return
    ;['l', 'r'].forEach((side) => {
      const angles = armAngles(bones, side)
      const excess = {
        elbowFlexion: angles.elbowFlexion - ARM_LIMITS.elbowFlexion,
        pronation: angles.rotation === null ? -1 : angles.rotation - ARM_LIMITS.pronation,
        supination: angles.rotation === null ? -1 : -angles.rotation - ARM_LIMITS.supination,
        wristFlexion: angles.flexion - ARM_LIMITS.wristFlexion,
        wristExtension: -angles.flexion - ARM_LIMITS.wristExtension,
        radial: angles.radial - ARM_LIMITS.radial,
        ulnar: -angles.radial - ARM_LIMITS.ulnar,
      }
      Object.entries(excess).forEach(([joint, over]) => {
        const key = name + ' ' + side + ' ' + joint
        largest[key] = Math.max(largest[key] ?? -Infinity, over)
        if (over > 0) faults.push({ key, over })
      })
    })
  })
  return { faults, largest }
}
