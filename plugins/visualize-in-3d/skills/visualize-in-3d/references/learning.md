# Learn from every mistake and every correction

The skill gets better only if each lesson is written down where the next run will read it. Reading map: What
becomes a lesson, Where lessons live, How to write one, Use them, When rules disagree.

## What becomes a lesson

- **A user correction or taste note.** "Too bright", "the boat slides", "I hate the dark theme", a picked option
  and its reason. Record it the same turn, before the next build step, without asking first.
- **A fault you caught yourself.** A review round fixed it, a check failed, or a tool cost time. Record the cause, not only the symptom.
- **A user request about how to work.** "Always send a preview first", "use real models". It is a rule from now on.

A one-off choice for this piece only ("make this boat red") stays in the plan file, not in the lessons.

## Where lessons live

1. **`{{WORK_DIR}}/viz3d-lessons.md`** for every lesson. It belongs to the user, survives plugin updates and is
   read at the start of every run.
2. **The skill's own lists**, but only in the user's own copy of the skill. A plugin update overwrites a plugin
   cache. In an own copy, add a fault to its list in `self-review.md` ("Growing the lists"). Add a look rule to
   `looks.md`.
3. **Upstream.** Some lessons help every user of the skill. Tell the user and offer to open an issue with the case
   on the skill's repository.

## How to write one

One entry per lesson, newest at the end:

```text
## 2026-11-06 Prototype ground
Rule: the ground is never one flat colour; dress it to the style card's density.
Why: user said "trông như khối xám trơn" on the canal lock prototype.
Check: in the side-by-side, no empty single-colour area larger than a quarter of the frame.
```

The rule is a command. The why quotes the user's own words or names the failed check. The check is something a
later round can measure or see, so the lesson is tested and not only remembered.

## Use them

- Read `{{WORK_DIR}}/viz3d-lessons.md` before writing the plan file and copy the rules that apply into it.
- Fix the current piece by the new rule before reporting. A lesson recorded but not applied is not done.
- When a lesson keeps coming back, turn its check into a script or a frame-guard measurement.

## When rules disagree

The newer user word wins over an older rule, and a user rule wins over this skill's defaults. Mark the older entry
"replaced on <date> by <title>" instead of deleting it, so the history stays readable.
