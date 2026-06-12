# Chapter Function Card

A chapter function card defines why the next chapter exists before drafting. Use it for `continue_story` and `draft_chapter` when the chapter goal is underspecified.

## Purpose

- Prevent filler chapters.
- State the chapter goal and main conflict.
- List required reveals, character changes, relationship changes, and foreshadowing.
- Preserve hard constraints and forbidden plot moves.

## Schema

```yaml
chapter: ""
branch: ""
chapter_goal: ""
main_conflict: ""
scene_beats: []
new_information: []
character_change: []
relationship_change: []
worldbuilding_to_reveal: []
foreshadowing_to_add: []
foreshadowing_to_payoff: []
ending_hook: ""
style_target: ""
hard_constraints: []
forbidden: []
source: []
status: "inferred"
confidence: "medium"
```

## Rules

- Do not automatically decide major plot events.
- If the user only provides `chapter_goal`, leave other fields empty or `待填写`.
- Default `status` is `inferred` unless the user explicitly specifies the chapter function.
- Build or update the context pack before using the card for drafting.
- Keep the card branch-local under `branches/<branch>/chapter_function_cards/`.

## Script

```bash
python scripts/create_chapter_function_card.py --project ./projects/my-novel --branch main --chapter 12 --goal "主角进入剑冢，发现父亲线索"
```

