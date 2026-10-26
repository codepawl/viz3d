# Action film mode

Use this mode for a short film where characters, creatures, vehicles or machines act. Examples: a fight, a chase,
a race, a match, a rescue, a launch, a crash, an animal hunting. It works in any look from `looks.md`. The rules
below came from a duel between two original creatures in the pixel diorama look and hold for any cast and action.

Reading map: Action sheet, Pass 1 (cast, rig, stage), Pass 2 (beats, effects, camera), Faults seen, Sound. Pass 2
ends with the loop in `self-review.md`.

## Action sheet

Write `notes/actions.md` before any code. It is the action version of the topic file.

- For each actor, list the 4 to 6 actions the audience knows it by. Name each action and say what it looks like:
  what comes out of where, its colour and shape, the pose and the sound. Take them from the real source:
  - footage and rules for real sports, animals and vehicles
  - incident reports for real events
  - the source material, when the user asks for a known character.
- Viewers want the real moves at full strength. Generic punches, puffs and balls of colour read as fake.
- Give each beat an action and an answer. Each beat changes who has the upper hand.

## Pass 1: cast, rig, stage

- Models: follow the order in `asset-sources.md`. A ready model with its own animation clips beats a hand-built
  one for a character people know.
- List every clip with its duration in `notes/models.md`. Render a grid of poses per clip and choose clips by
  looking, not by name. A model with a skeleton and no clips is posed bone by bone on a keyframe table. A vehicle
  or machine gets its moving parts as separate nodes.
- Set every clip from the film clock with `AnimationMixer.setTime`, never by a delta. Then any frame renders the
  same in any order.
- Change a model's colours in the shader or a copy of its material made once. Never tint a shared material at
  runtime (see Faults seen).
- Stage: relief and props that fit the place, and real light from a key light with shadows plus a fill. Every
  surface has the same detail level as the actors. In the pixel look that means the same pixel scale.
- Pass 1 report: stills from the film's camera angles, the clip grid, each actor at film scale. Each actor is at
  least 40 pixels tall (low-res pixels in the pixel look) in the main framing.

## Pass 2: beats, effects, camera

A shape that worked for a duel:

1. Entrance with each actor's signature intro.
2. An opening attack and a dodge.
3. A defence that answers it.
4. A counter, then an aerial or fast strike, then the special move.
5. A climax where both forces meet and push back and forth.
6. The outcome in clear view, then the camera pushing in on the winner.

A chase, a race or a launch keeps the same idea: a setup, rising exchanges, one peak, and an ending you can see.

Choreography:

- Each side shows off before anyone attacks. In a duel both actors get a display beat (a roar, a stomp, a
  flourish), then a short pause, then the first attack.
- A display aims forward and up at about 45 degrees, braced. A straight-up 90 degree blast looks odd. Aim it away
  from the opponent so it reads as a display.
- Opponents face each other. Each frame, every actor eases its body toward the other's current position. The
  exceptions are a move that aims elsewhere and an exit.
- Every landed physical hit moves the target: knockback, a stagger or a fall, then a heavy recovery. A target that
  stands still under a hit looks fake.
- Reactions never repeat. Give a long move on one target a sequence: brace, defend, push back, break free. Never
  play one shake loop again.
- The world reacts to every contact. A rock breaks under a landing and a pillar chips when hit. A skid pushes
  pebbles aside, and water splashes. List every contact with its time before the review; a heavy body landing on a
  rock that does nothing is the commonest miss.
- Only the target reacts to a hit. A flash or tint on the attacker is a bug.
- Every special move gets its own cast. It has a wind-up pose and a charge that builds. Then the effect grows
  from its source to the target. An effect that pops into place at full size reads as cheap.

Effects must look heavy and dangerous:

- Beams, jets, flames and exhaust have an opaque core with a white-hot centre and saturated outer layers. Fire
  goes white, yellow, orange, red. Water goes white, cyan, deep blue. Make them thick at the film's scale with a
  soft or dithered edge. Sparse speckle and chains of balls read weak.
- Anticipation: a charge glow or wind-up for 0.2 to 0.4 s. Then the source recoils.
- Every hit or impact gets all of these:
  - 2 to 4 frames of hit-stop and a screen shake scaled to the hit
  - a one-frame flash that never whites out an actor
  - a ring of debris or spray, and a scorch, wet or skid mark that stays
  - the effect's warm or cool light pulsing on the ground and the target
- Smoke, dust and steam stay thin and move outward and up. They never cover an actor for more than 0.3 s.

Camera: one continuous move, with a slight push-in on each big hit and on the climax. Both sides of an exchange
stay in frame. The winner or the result fills at least a third of the frame height at the end.

## Faults seen

`self-review.md` checks these on every render.

- Effects too thin and sparse. Water and fire looked limp.
- An action hidden in dust or steam (a charge inside a dust cloud, steam over both actors for 2 s).
- An actor turning one flat colour during a hit, from a hit tint written into a shared material.
- An actor cut by the frame edge during knockback.
- The knockout and the exit hidden, and the winner small and far away at the end.
- A messy pose from a clip played out of context, such as an attack clip started half-way for a dive.
- Flat, smooth, badly lit ground at a different detail level from the actors.
- The whole frame smeared into ghost copies on every big hit. The screen shake changed between the motion-blur
  subframes of one output frame. Evaluate shake and flash once per output frame.
- Crack and scorch decals piled up as black ink. Keep about 3 at once, tint them a darker shade of the floor and
  fade old ones out.
- Dust puffs over the winner during the victory.
- The victory pan starting late, with the winner still in a corner.

## Sound

Hero cues need professional-sounding SFX, never plain or under-processed ones:

- Build each hero cue from 3 or more layers: a transient, a real CC0 recording, a code-made sub.
  Add a tail of debris, spray or crackle. Process each layer with EQ and saturation. Add a reverb send
  and compression on the cue bus, and pan each cue by its place on screen.
- Sustained beams loop with crossfades. They have a start, a sustain and a release, and their pitch follows the
  effect's growth.
- Build creature voices from layered, pitch-shifted animal recordings. Never use official cries or game audio.
- Keep hit-stop frames near silent, so the impact lands on the first frame after.
- Show previews without sound. Build the sound only after the user approves the cut.
