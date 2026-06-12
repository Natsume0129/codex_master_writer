# Schemas

These schemas define the expected shape of project files. YAML examples are templates, not complete story data.

## v0.3.1 Contract

- The active skill path is `.agents/skills/chinese-novel-writing/`.
- New project templates live under `templates/novel_project/`; this is intentional and replaces the older single-file `assets/templates/` idea.
- New generated files should include `schema_version: "0.3.1"` when the format supports it.
- `output_mode` is the canonical output field. `preferred_output_mode` is an older requirements name and is not the current implementation field.
- Important facts use `source`, `status`, and `confidence`. Do not reintroduce `fact_status`.
- Indexes are navigation aids, not source of truth.
- `pending_updates/` is a review queue, not an automatic merge area.

## Fact Value

Use this exact fact envelope for important settings. Do not use the old separate fact-status key.

```yaml
value: ""
status: "confirmed | inferred | uncertain | user_override | deprecated"
source: []
confidence: "high | medium | low"
last_seen: ""
notes: ""
```

Status rules:

- `confirmed`: directly supported by source text or explicit user confirmation.
- `inferred`: suggested by multiple clues but not directly confirmed.
- `uncertain`: evidence is weak, ambiguous, contradictory, or incomplete.
- `user_override`: explicitly supplied by the user; highest priority.
- `deprecated`: superseded or intentionally retired; exclude from normal context packs.

Some fields named `status` are lifecycle states rather than evidence states. For example, `foreshadowing.status` uses `open | reinforced | paid_off | abandoned | uncertain`, and extraction progress uses `pending | queued | processing | done | failed | skipped`. Do not treat those as fact evidence status without reading the surrounding schema.

## project_config.yaml

```yaml
schema_version: "0.3.1"
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

## Character

```yaml
characters:
  character_id:
    name: ""
    aliases: []
    role: "protagonist | antagonist | supporting | minor | unknown"
    life_state:
      value: "alive | dead | missing | unknown"
      status: "confirmed | inferred | uncertain | user_override | deprecated"
      source: []
      confidence: "high | medium | low"
      last_seen: ""
      notes: ""
    identity:
      value: ""
      status: "confirmed | inferred | uncertain | user_override | deprecated"
      source: []
      confidence: "high | medium | low"
      last_seen: ""
      notes: ""
    goals: []
    fears: []
    secrets: []
    abilities: []
    current_state:
      value: ""
      status: "confirmed | inferred | uncertain | user_override | deprecated"
      source: []
      confidence: "high | medium | low"
      last_seen: ""
      notes: ""
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
    status: "confirmed | inferred | uncertain | user_override | deprecated"
    confidence: "high | medium | low"
    branch: "canon | main | branch_name"
```

For older projects where relationship entries do not yet include `status`, keep `source` and `confidence`, and treat relationship certainty conservatively. v0.3.1 validation may warn but should not fail an otherwise valid empty project for this field.

## Item, Location, Organization, Term

Use the fact envelope for mutable item state, location description, organization state, and term meaning.

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
      last_seen: ""
      notes: ""
```

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
    status: "confirmed | inferred | uncertain | user_override | deprecated"
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
    last_seen: ""
    notes: ""
```

## Plot Node

```yaml
plot_nodes:
  - id: ""
    chapter: ""
    event: ""
    summary: ""
    causes: []
    effects: []
    required_conditions: []
    affected_characters: []
    affected_relationships: []
    affected_factions: []
    affected_items: []
    affected_world_rules: []
    foreshadowing_links: []
    can_survive_divergence: true
    replacement_needed_if_changed: false
    source: []
    confidence: "medium"
```

## Divergence Analysis

```yaml
divergence_analysis:
  divergence_id: ""
  branch: ""
  original_fact: ""
  changed_fact: ""
  divergence_time: ""
  impact_radius: ""
  preserved_facts: []
  can_change: []
  invalidated_plot_nodes: []
  preserved_plot_nodes: []
  inverted_plot_nodes: []
  replacement_plot_nodes: []
  new_conflicts: []
  relationship_impacts: []
  faction_impacts: []
  timeline_impacts: []
  unresolved_risks: []
  requires_user_decision: []
```

## Branch Config

```yaml
schema_version: "0.3.1"
branch_name: "main"
branch_type: "main | alternate"
title: ""
base_branch: ""
base_chapter: ""
inherit_mode: "skeleton | current-state"
divergence_point: ""
created_at: ""
status: "active"
notes: ""
```

## Chapter Card

```yaml
chapter_id: "chapter_001"
title: ""
source_files: []
summary: ""
chapter_function: ""
major_events: []
characters_present: []
relationship_changes: []
new_worldbuilding: []
locations: []
organizations: []
items: []
terms: []
timeline_events: []
foreshadowing: []
open_questions: []
ending_hook: ""
style_snapshot: ""
facts:
  - category: ""
    value: ""
    status: "confirmed | inferred | uncertain | user_override | deprecated"
    source: []
    confidence: "high | medium | low"
    notes: ""
```

## Chapter Function Card

```yaml
schema_version: "0.3.1"
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

## Context Pack

See `context_pack.md` for the full structure.

## Extraction Progress

```yaml
schema_version: "0.3.1"
project:
  name: ""
  source_manifest: "imports/chunk_manifest.yaml"
  created_at: ""
  updated_at: ""

settings:
  batch_size: 10
  active_stage: "chunk_cards"
  stages: ["chunk_cards", "chapter_cards", "volume_summaries", "story_bible_patches", "indexes"]

chunks:
  chapter_001_chunk_0001:
    chapter_id: "chapter_001"
    source_file: ""
    output_file: ""
    status: "pending | queued | processing | done | failed | skipped"
    batch_id: ""
    chunk_card: ""
    error: ""
    updated_at: ""

chapters:
  chapter_001:
    status: "pending | partial | ready_for_chapter_card | done | failed"
    chunk_ids: []
    chapter_card: ""
    updated_at: ""

batches:
  batch_0001:
    stage: "chunk_cards"
    status: "queued | processing | done | failed"
    chunk_ids: []
    created_at: ""
    completed_at: ""
    notes: ""
```

## Extraction Batch Metadata

```yaml
schema_version: "0.3.1"
batch_id: "batch_0001"
stage: "chunk_cards"
status: "queued"
chunk_ids:
  - "chapter_001_chunk_0001"
created_at: ""
instructions: "Read only listed chunks; facts require source/status/confidence."
outputs_expected:
  - "extracted/chunk_cards/*.yaml"
```

## Navigation Index Entry

Indexes are retrieval aids. They must point back to source files and must not replace canon or extracted cards.

```yaml
characters:
  - id: ""
    name: ""
    aliases: []
    type: "characters"
    sources: []
    chapters: []
    chunks: []
    last_seen: ""
    status: ""
    confidence: ""
    notes: ""
```

## Patch

See `patch_update.md` for the post-write patch schema.

Patch apply helpers may dry-run and apply limited safe fields, but complex bible updates remain review-only unless a human explicitly approves the target edit.
