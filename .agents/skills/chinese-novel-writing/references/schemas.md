# Schemas

These schemas define the expected shape of project files. YAML examples are templates, not complete story data.

## project_config.yaml

```yaml
project_name: ""
language: "zh-CN"
primary_mode: "original"
current_branch: "main"
current_chapter: null
chapter_length_target: null
output_mode: "draft_with_notes"
automation_level: "medium"
auto_update_bible: true
auto_generate_context_pack: true
auto_generate_scene_outline: true
auto_review_after_draft: true
auto_rewrite_after_review: false
confirm_major_plot_changes: true
created_at: ""
updated_at: ""
```

## Fact Value

Every important setting should support:

```yaml
value: ""
status: "confirmed | inferred | uncertain | user_override | deprecated"
source: []
confidence: "high | medium | low"
last_seen: ""
notes: ""
```

## Character

```yaml
characters:
  character_id:
    name: ""
    aliases: []
    role: "protagonist | antagonist | supporting | minor | unknown"
    status:
      value: "alive | dead | missing | unknown"
      fact_status: "confirmed | inferred | uncertain | user_override | deprecated"
      source: []
      confidence: "high | medium | low"
    identity:
      value: ""
      fact_status: "confirmed | inferred | uncertain | user_override | deprecated"
      source: []
      confidence: "high | medium | low"
    goals: []
    fears: []
    secrets: []
    abilities: []
    current_state: ""
    relationships: []
    speech_style: ""
    first_appearance: ""
    last_seen: ""
    notes: ""
```

## Relationship

```yaml
relationships:
  - from: ""
    to: ""
    relation_type: "ally | enemy | family | mentor | romantic | superior | subordinate | unknown"
    public_status: ""
    private_status: ""
    knowledge_asymmetry: ""
    stage: ""
    source: []
    confidence: "high | medium | low"
    branch: "canon | main | branch_name"
```

## Item, Location, Organization, Term

```yaml
items:
  - id: ""
    name: ""
    owner: ""
    state:
      value: ""
      status: "confirmed | inferred | uncertain | user_override | deprecated"
      source: []
      confidence: "high | medium | low"
    notes: ""
```

Use the same source/status/confidence pattern for `locations`, `organizations`, and `terms`.

## Timeline Event

```yaml
timeline:
  - id: "event_001"
    story_time: ""
    narrative_order: 1
    chapter: ""
    event: ""
    characters: []
    location: ""
    causes: []
    effects: []
    branch: "main"
    source: []
    confidence: "high | medium | low"
```

## Foreshadowing

```yaml
foreshadowing:
  - id: "foreshadowing_001"
    content: ""
    first_appeared: ""
    reinforced: []
    status: "open | reinforced | paid_off | abandoned | uncertain"
    likely_payoff_range: ""
    related_entities: []
    possible_payoffs: []
    actual_payoff: ""
    source: []
    confidence: "high | medium | low"
```

## Branch Config

```yaml
branch_name: "main"
branch_type: "main | alternate"
title: ""
base_branch: ""
divergence_point: ""
created_at: ""
status: "active"
notes: ""
```

## Chapter Card

```yaml
chapter_id: "chapter_001"
title: ""
source_file: ""
summary: ""
chapter_function: ""
key_events: []
characters_present: []
locations: []
items: []
foreshadowing: []
open_questions: []
source: []
confidence: "high | medium | low"
```

## Context Pack

See `context_pack.md` for the full structure.

## Patch

See `patch_update.md` for the full post-write patch schema.
