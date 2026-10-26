# Agent guide for this repository

This repository is the viz3d skill: a plugin that turns a subject into a 3D app or film. These rules are for a
coding agent that changes the repository. To use the skill, not to change it, read
`plugins/visualize-in-3d/skills/visualize-in-3d/SKILL.md` instead. People read [CONTRIBUTING.md](CONTRIBUTING.md).
It has the same rules with more reasons.

## Before you edit

1. Read `plugins/visualize-in-3d/skills/visualize-in-3d/SKILL.md` and only the reference files that your change
   touches. Do not load every file in `references/`.
2. Run `git status`. Do not change or revert files that you did not touch.
3. Find where the thing lives:

| Change | Files |
|---|---|
| A look | `references/looks.md` (new section before `## Choosing`, one row in `## Choosing`), `README.md`, `SKILL.md` description |
| A mode | `references/<mode>.md`, shape table in `SKILL.md`, mode table in `skills/viz3d/SKILL.md`, `README.md`, both files in `harness/` |
| A fault | the fault list in `references/self-review.md` or in the mode reference |
| An example | `examples/<topic>.md`, in the shape of `examples/airport-ramp.md` |
| A script | `scripts/`, and the reference that tells the agent when to run it |
| A harness | `harness/<agent>/`, plus the install and command tables in `README.md` |

## Hard rules

- `skills/visualize-in-3d/SKILL.md` has a maximum of 100 lines. Its frontmatter has only `name`, `description` and
  `license`. Move detail into a reference file.
- `skills/viz3d/SKILL.md` keeps `disable-model-invocation: true`, so the command runs only when a person types it.
  `skills/viz3d/agents/openai.yaml` keeps `allow_implicit_invocation: false` for the same reason.
- A mode word must match in all four places: `skills/viz3d/SKILL.md`, `harness/gemini/viz3d.toml`,
  `harness/opencode/viz3d.md` and the `README.md` mode table.
- No private data: no personal names, home folders, drive letters, internal tool names, API keys or tokens. Use
  `{{WORK_DIR}}` and `{{SKILL_DIR}}` with forward slashes.
- Assets and sounds need a reusable licence (CC0, CC BY) with the source named. Sound effects are real or made and
  mixed in layers.
- Scripts never read the wall clock or unseeded randomness. A frame depends only on its time.
- Do not add a dependency to a script without a reason in the pull request. The scripts run on Node 20 and ffmpeg.
- Prose follows plain technical English: short sentences, active voice, no em dashes, no semicolons in prose, no
  sales words.

## Check before you finish

Run these from the repository root and fix every failure:

```bash
claude plugin validate .
claude plugin validate plugins/visualize-in-3d
for f in plugins/visualize-in-3d/skills/visualize-in-3d/scripts/*.js plugins/visualize-in-3d/skills/visualize-in-3d/scripts/*.mjs; do node --check "$f"; done
bash -n plugins/visualize-in-3d/skills/visualize-in-3d/scripts/contact-sheet.sh
wc -l plugins/visualize-in-3d/skills/*/SKILL.md
git diff | grep -niE "C:\\\\|/Users/|/home/|api[_-]?key|token" || echo "scrub clean"
```

If `claude` is not installed, say so in your report and still run the other checks.

## Finish

- Raise `version` in `plugins/visualize-in-3d/.claude-plugin/plugin.json`: patch for a fix or a fault, minor for a
  look, mode, script or harness.
- Keep one topic in each commit. In the report, list the changed files and the checks with their result. Say what
  you could not check.
- Do not push, publish or open a pull request unless the person asked for it.
