# Contributing to viz3d

Thanks for helping. This guide is for people. If you work through a coding agent, point it at
[AGENTS.md](AGENTS.md). That file has the same rules in the order an agent needs them.

## What helps most

- **A fault you saw.** Maybe a film had a hidden hit, or a caption went by too fast. Open an issue with the prompt you used, the agent and model, and one frame that shows the fault. We add it
  to a fault list in `references/self-review.md` or `references/action.md`, so every later run checks for it.
- **A new look.** You need a style that the five looks do not cover. Add a section to `references/looks.md` (see
  below).
- **An example topic.** You built a place or a system that went well. Add it to `examples/` as a topic file.
- **A harness adapter.** Your agent needs its own command file to run `/viz3d`.
- **Fixes to the scripts** in `scripts/`.

For a large change, such as a new mode or a new script, open an issue first. That way we can agree on the shape
before you spend time on it.

## Layout

```text
.claude-plugin/marketplace.json            marketplace entry for Claude Code
plugins/visualize-in-3d/
  .claude-plugin/plugin.json               plugin name and version
  skills/visualize-in-3d/                  the skill
    SKILL.md                               entrypoint, read first by every agent
    references/                            one file per mode or topic, read on demand
    examples/                              topic files for real places and systems
    scripts/                               recording, checks and the mock feed
    agents/openai.yaml                     Codex display name and invocation policy
  skills/viz3d/                            the /viz3d command
harness/gemini/viz3d.toml                  /viz3d for Gemini CLI
harness/opencode/viz3d.md                  /viz3d for OpenCode
```

## How to add things

### A look

1. Add a `## <Look name>` section to `references/looks.md`, before `## Choosing`.
2. Describe the look in the same order as the other sections: palette, light, materials, camera, effects, and what
   breaks it.
3. Add one row for the look under `## Choosing`.
4. Add the look name to the list of looks in `README.md` and in the `description` of `SKILL.md`.

### A mode

1. Add `references/<mode>.md` with the steps for the mode and its own fault list.
2. Add one row to the shape table in `SKILL.md` and a mode word to the table in `skills/viz3d/SKILL.md`.
3. Update the mode list in `README.md` and in `harness/gemini/viz3d.toml` and `harness/opencode/viz3d.md`.

### An example topic

Copy the shape of `examples/airport-ramp.md`: the real parts and their sizes, what moves, the beats, the look and
the camera. Use made-up company and people names. Cite the sources for real sizes and procedures.

### A fault

Add one line to the matching list in `references/self-review.md` (generic faults) or in the mode's reference. Write
what the fault looks like in a frame and how to measure it, not only its name.

## Rules for every change

- **`SKILL.md` stays under 100 lines.** Move detail into a reference file and link to it.
- **Frontmatter of `skills/visualize-in-3d/SKILL.md`** has only `name`, `description` and `license`. Other keys
  make the upload to claude.ai fail. The `viz3d` command can also use `argument-hint` and
  `disable-model-invocation`.
- **No private details.** No user names, home folders, drive letters, company names or internal tools. Write paths
  as `{{WORK_DIR}}` and `{{SKILL_DIR}}`, with forward slashes.
- **Assets and sounds** must have a licence that lets anyone reuse them, such as CC0 or CC BY. Name the source and
  the licence. Sound effects are real recordings or sounds you made and mixed in layers, not one beep per hit.
- **Write plainly.** Use short sentences, active voice and one name for one thing. Do not use em dashes or sales
  words.
- **Every frame is a function of time.** Scripts and briefs never read the wall clock or `Math.random` without a
  seed.

## Check your change

Run these from the repository root before you open a pull request:

```bash
claude plugin validate .
```

```bash
claude plugin validate plugins/visualize-in-3d
```

```bash
for f in plugins/visualize-in-3d/skills/visualize-in-3d/scripts/*.js plugins/visualize-in-3d/skills/visualize-in-3d/scripts/*.mjs; do node --check "$f"; done
```

```bash
bash -n plugins/visualize-in-3d/skills/visualize-in-3d/scripts/contact-sheet.sh
```

```bash
wc -l plugins/visualize-in-3d/skills/*/SKILL.md
```

If you changed what the agent does, run the skill once on a small subject. Attach a contact sheet or a short clip
to the pull request.

## Versions

Raise `version` in `plugins/visualize-in-3d/.claude-plugin/plugin.json` in the same pull request:

- patch (0.3.0 to 0.3.1) for a fix or a new fault,
- minor (0.3.0 to 0.4.0) for a new look, mode, script or harness.

## Pull requests

Keep one topic in each pull request. Say what changed, why, and how you checked it. By contributing, you agree
that your work is released under the MIT licence of this repository.
