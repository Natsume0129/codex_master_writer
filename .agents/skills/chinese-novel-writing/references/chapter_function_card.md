# Chapter Function Card

A chapter function card defines why the next chapter exists before drafting. In v0.5 it is the writing-control surface for chapter purpose, scene rhythm, conflict, reveals, character movement, foreshadowing, hard constraints, and user-confirmation gates.

## Purpose

- Prevent filler chapters.
- State the chapter goal, chapter function, reader promise, and main conflict.
- Plan scene beats with required facts and forbidden changes.
- Track emotional arc, information reveals, character and relationship changes, worldbuilding, foreshadowing, and ending hook.
- Preserve hard constraints and explicitly mark major plot decisions that require user confirmation.

## v0.5 Schema

```yaml
schema_version: "0.5"
chapter: "chapter_001"
branch: "main"
chapter_goal: ""
chapter_function:
  type: "setup | escalation | reveal | reversal | payoff | transition | climax | aftermath | unknown"
  purpose: ""
  reader_promise: ""
main_conflict: ""
scene_beats:
  - beat_id: "beat_001"
    purpose: ""
    location: ""
    characters: []
    conflict: ""
    outcome: ""
    required_facts: []
    forbidden_changes: []
emotional_arc:
  start: ""
  turn: ""
  end: ""
new_information: []
character_change: []
relationship_change: []
worldbuilding_to_reveal: []
foreshadowing_to_add: []
foreshadowing_to_payoff: []
continuity_constraints: []
style_target: ""
ending_hook: ""
hard_constraints: []
forbidden:
  - "不得自动决定重大剧情变化。"
  - "不得覆盖用户原文。"
requires_user_confirmation:
  - change: ""
    reason: ""
source: ["user_input"]
status: "inferred"
confidence: "medium"
created_at: ""
notes: ""
```

Older v0.4 cards with only `chapter_goal`, `main_conflict`, `scene_beats`, reveal fields, `hard_constraints`, and `forbidden` remain readable. New cards should use the v0.5 fields.

## Rules

- Do not automatically decide major plot events.
- If the user only provides `chapter_goal`, leave other fields empty or `unknown`; Codex/model may fill them after reading the context pack.
- Default `status` is `inferred` unless the user explicitly specifies the chapter function.
- Build or update the context pack before using the card for drafting.
- Generate a draft prompt before writing when the task is a normal continuation or draft request.
- Keep the card branch-local under `branches/<branch>/chapter_function_cards/`.

## Script

```bash
python scripts/novel_project.py create-function-card --project-root ./projects/my-novel --branch main --chapter 12 --goal "主角进入剑冢，发现父亲线索" --force
```

The script creates the card skeleton only. It does not infer scene beats, write prose, read long raw text, or confirm major plot changes.
