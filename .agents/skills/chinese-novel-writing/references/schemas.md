# Schemas

These schemas define the expected shape of project files. YAML examples are templates, not complete story data.

## v0.5 Contract

- The active skill path is `.agents/skills/chinese-novel-writing/`.
- New project templates live under `templates/novel_project/`; this is intentional and replaces the older single-file `assets/templates/` idea.
- Existing structural project files from v0.4 remain valid.
- New v0.5 writing-control artifacts use `schema_version: "0.5"`: chapter function cards, draft prompts, quality review prompts, and patch review reports.
- v0.5.1 does not introduce `schema_version: "0.5.1"`.
- New v0.6 rewrite artifacts use `schema_version: "0.6"`: plot node maps, divergence analyses, replacement routes, rewrite plan prompts, and branch diff reports.
- New v0.4 import and patch skeleton formats still use `schema_version: "0.4"` unless that specific format is migrated.
- `output_mode` is the canonical output field. `preferred_output_mode` is an older requirements name and is not the current implementation field.
- Important facts use `source`, `status`, and `confidence`. Do not reintroduce `fact_status`.
- Indexes are navigation aids, not source of truth.
- `pending_updates/` is a review queue, not an automatic merge area.
- Import closure is staged through chapter-card batches, volume-summary batches, and story-bible patch batches. Scripts generate prompts and patch skeletons; they do not perform AI analysis.
- Context packs may use `--auto-select`, but manual selectors have priority and empty auto-selection remains valid.
- Draft prompts and quality review prompts are instructions for Codex/model; scripts do not write prose or perform AI review.

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
schema_version: "0.4"
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

For older projects where relationship entries do not yet include `status`, keep `source` and `confidence`, and treat relationship certainty conservatively. v0.4 validation may warn but should not fail an otherwise valid empty project for this field.

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
schema_version: "0.4"
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
schema_version: "0.4"
chapter_id: "chapter_001"
title: ""
source_chunk_cards: []
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

## Context Pack

See `context_pack.md` for the full structure.

## Extraction Progress

```yaml
schema_version: "0.4"
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
schema_version: "0.4"
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

## v0.4 Import Status

Default path: `imports/import_status.md`.

YAML shape when using `--format yaml`:

```yaml
schema_version: "0.4"
generated_at: ""
warnings: []
chunk_count: 0
chunk_statuses:
  pending: 0
  queued: 0
  processing: 0
  done: 0
  failed: 0
  skipped: 0
batch_statuses: {}
batch_files: []
chunk_cards_done: 0
missing_chunk_cards: []
ready_chapters: []
chapter_cards_done: []
missing_chapter_cards: []
volume_summaries: []
bible_patches: []
failed_chunks: []
next_actions: []
```

## v0.4 Later-Stage Batch Metadata

Chapter-card batch:

```yaml
schema_version: "0.4"
batch_id: "batch_0002"
stage: "chapter_cards"
status: "queued"
chapter_ids:
  - "chapter_001"
created_at: ""
outputs_expected:
  - "extracted/chapter_cards/*.yaml"
```

Volume-summary batch:

```yaml
schema_version: "0.4"
batch_id: "batch_0003"
stage: "volume_summaries"
status: "queued"
volume: "volume_0001"
chapter_ids: []
missing_chapter_cards: []
created_at: ""
output: "extracted/volume_summaries/volume_0001.md"
```

Story-bible patch batch:

```yaml
schema_version: "0.4"
batch_id: "batch_0004"
stage: "story_bible_patches"
status: "queued"
source: "all"
patch_skeleton: "pending_updates/import_bible_patch_batch_0004.yaml"
source_files: []
created_at: ""
```

Patch skeletons created by this batch stay under `pending_updates/` and must be reviewed before `apply-patch --confirm`.

## v0.4 Quality Report

Default path:

```text
branches/<branch>/reviews/chapter_XXX_quality_report.md
```

Required sections:

- `schema_version: 0.4`
- summary
- serious issues
- medium issues
- light issues
- suggested fixes
- patch candidates
- evidence
- next actions

The report is an evidence-backed review artifact. It is not an automatic rewrite and does not apply patches.

## v0.5 Draft Prompt

Default path:

```text
branches/<branch>/draft_prompts/chapter_XXX_draft_prompt.md
```

Required metadata:

- `schema_version: 0.5`
- `generated_at`
- `branch`
- `chapter`
- `chapter_label`
- `output_mode`
- `target_length`
- `style_strictness`
- `context_pack`
- `context_pack_status`
- `chapter_function_card`
- `chapter_function_card_status`
- `suggested_draft_output`

The prompt instructs Codex/model to read the context pack and function card, avoid `raw_text/full_text.txt`, write only when requested, and stage post-write updates through pending patches.

## v0.5 Quality Review Prompt

Default path:

```text
branches/<branch>/reviews/chapter_XXX_quality_review_prompt.md
```

Required metadata:

- `schema_version: 0.5`
- `generated_at`
- `branch`
- `chapter`
- `chapter_label`
- `draft`
- `draft_status`
- `context_pack`
- `context_pack_status`
- `report_output`
- `severity_scope`

The prompt is not the review itself. It tells Codex/model how to fill the quality report using evidence from the draft and context pack.

## v0.5 Patch Review Report

Default path:

```text
pending_updates/<patch_stem>_review.md
```

Required sections:

- `schema_version: 0.5`
- patch metadata
- summary counts
- safe updates
- review-only updates
- requires user confirmation
- potential conflicts
- dry-run and apply guidance

Safe update fields are currently `updates.timeline`, `updates.foreshadowing_added`, `updates.open_questions_added`, and `updates.continuity_issues`. Other update fields are review-only unless a future helper explicitly supports them.

## v0.6 Plot Node Map

```yaml
schema_version: "0.6"
project: ""
branch: ""
base_branch: "main"
source_scope: []
generated_at: ""
missing_sections: []
plot_nodes:
  - id: ""
    source_branch: ""
    chapter: ""
    scene: ""
    event: ""
    summary: ""
    causes: []
    effects: []
    required_conditions: []
    affected_characters: []
    affected_relationships: []
    affected_factions: []
    affected_items: []
    affected_locations: []
    affected_world_rules: []
    foreshadowing_links: []
    status: "confirmed | inferred | uncertain"
    source: []
    confidence: "high | medium | low"
    can_survive_divergence: "yes | no | uncertain"
    replacement_needed_if_changed: true
```

## v0.6 Divergence Analysis

```yaml
schema_version: "0.6"
project: ""
branch: ""
base_branch: "main"
divergence_id: ""
divergence_title: ""
base_chapter: ""
original_fact: ""
changed_fact: ""
divergence_time: ""
impact_radius: "level_1_local | level_2_relationship | level_3_main_plot | level_4_world_rule | uncertain"
impact_reason: ""
preserved_facts: []
can_change: []
invalidated_plot_nodes: []
preserved_plot_nodes: []
inverted_plot_nodes: []
replacement_plot_nodes: []
relationship_impacts: []
faction_impacts: []
timeline_impacts: []
foreshadowing_impacts: []
world_rule_impacts: []
new_conflicts: []
unresolved_risks: []
requires_user_decision: []
source: []
status: "confirmed | inferred | uncertain | user_override"
confidence: "high | medium | low"
missing_sections: []
```

## v0.6 Replacement Routes

```yaml
schema_version: "0.6"
project: ""
branch: ""
divergence_id: ""
routes:
  - route_id: ""
    title: ""
    premise: ""
    preserved_nodes: []
    replaced_nodes: []
    inverted_nodes: []
    new_major_conflicts: []
    relationship_direction: []
    antagonist_plan_changes: []
    timeline_changes: []
    foreshadowing_to_add: []
    risks: []
    requires_user_decision: []
    recommendation: "primary | alternative | risky | rejected"
    reason: ""
status: "draft"
confidence: "medium"
```

## v0.6 Branch Diff Report

Markdown report with YAML frontmatter:

```yaml
---
schema_version: "0.6"
project: ""
branch: ""
base_branch: "main"
divergence_id: ""
impact_radius: ""
report_type: "branch_diff_report"
status: "draft"
---
```

Required sections: summary, divergence point, impact radius, preserved plot nodes, invalidated plot nodes, inverted plot nodes, replacement needed, candidate replacement routes, timeline risks, relationship risks, foreshadowing risks, world rule risks, required user decisions, branch pollution checklist, and next recommended action.

## v0.6 Rewrite Plan Prompt

Markdown prompt with metadata. It instructs Codex/model to read the context pack, plot node map, divergence analysis, and replacement routes; avoid `raw_text/full_text.txt`; keep outputs branch-local; and produce artifact updates rather than prose.

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
