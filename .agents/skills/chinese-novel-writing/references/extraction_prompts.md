# Extraction Prompts

Use these prompts when importing a long Chinese novel in batches. Do not process the whole novel at once. Read only the chunk files for the current batch and write structured outputs with source/status/confidence.

## Batch Import Prompt

```text
请使用 chinese-novel-writing skill，处理 imports/batches/<batch_id>_chunk_cards.md 中列出的 chunk。
只读取该 batch 文件列出的 chunk 原文，不要读取 raw_text/full_text.txt，也不要一次性读取整本小说。
为每个 chunk 生成 extracted/chunk_cards/<chunk_id>.yaml。
每条重要事实必须包含 source、status、confidence。
不要把推测写成 confirmed；不要直接修改 canon 或 main 分支资料库。
完成后用 scripts/novel_project.py mark-done 更新 extraction_progress.yaml。
```

## Status Rules

- `confirmed`: the source text explicitly supports the fact.
- `inferred`: multiple passages imply the fact, but no passage directly confirms it.
- `uncertain`: evidence is insufficient, ambiguous, contradictory, or context-dependent.
- `user_override`: the user explicitly specifies the fact; highest priority.
- `deprecated`: the fact is retired, superseded, or contradicted by accepted later canon.

Do not treat character lies, legends, dreams, hallucinations, rumors, misleading clues, or in-world documents as confirmed facts unless the narrative directly confirms them.

## Chunk Card Prompt

Prompt:

```text
Use chinese-novel-writing. Read only the specified chunk file. Generate one chunk_card YAML.
Preserve source references. Every extracted fact must include category, value, status, source, confidence, and notes.
Do not infer beyond the chunk unless the user provides additional context.
```

Schema:

```yaml
chunk_id: ""
chapter_id: ""
source_file: ""
source_span: ""
summary: ""
events: []
characters: []
relationships: []
worldbuilding: []
locations: []
organizations: []
items: []
terms: []
timeline_events: []
foreshadowing_candidates: []
open_questions: []
style_notes: []
facts:
  - category: ""
    value: ""
    status: "confirmed | inferred | uncertain | user_override | deprecated"
    source: []
    confidence: "high | medium | low"
    notes: ""
```

## Chapter Card Merge Prompt

Prompt:

```text
Use chinese-novel-writing. Merge the chunk_cards for one chapter into a chapter_card.
Do not reread unrelated chapters. Combine duplicate facts by merging source lists.
Keep uncertain facts uncertain. Mark chapter-level interpretations as inferred unless directly supported.
```

For v0.4, prefer creating these prompts with:

```bash
python scripts/novel_project.py create-chapter-card-batch --project-root ./projects/my-novel --batch-size 5 --force
```

The generated batch lists source chunk cards. Read only those listed chunk cards; do not read full raw text or unrelated raw chapters.

Schema:

```yaml
schema_version: "0.4"
chapter_id: ""
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

## Volume Summary Merge Prompt

Prompt:

```text
Use chinese-novel-writing. Merge the chapter_cards for one volume into a volume_summary.
Summarize plot progress and arcs; do not add unsourced canon. Preserve unresolved questions.
```

For v0.4, prefer creating the prompt with:

```bash
python scripts/novel_project.py create-volume-summary-batch --project-root ./projects/my-novel --volume 1 --force
```

Schema:

```yaml
schema_version: "0.4"
volume_id: ""
chapters: []
summary: ""
main_plot_progress: ""
character_arcs: []
relationship_arcs: []
worldbuilding_progress: []
antagonist_progress: []
foreshadowing_open: []
foreshadowing_paid_off: []
open_questions: []
timeline_range: ""
style_notes: []
```

## Story Bible Merge Prompt

Prompt:

```text
Use chinese-novel-writing. Merge accepted chapter_cards and volume_summaries into story bible patch candidates.
Do not edit canon files directly. Produce pending_updates entries first.
Do not promote uncertain to confirmed automatically. Merge duplicate facts by source.
Send conflicts to continuity_log or pending_updates potential_conflicts.
```

For v0.4, prefer creating the prompt and patch skeleton with:

```bash
python scripts/novel_project.py create-bible-patch-batch --project-root ./projects/my-novel --source all --force
```

The script writes `batch_XXXX_story_bible_patches.md/.yaml` and `pending_updates/import_bible_patch_XXXX.yaml`. Fill the patch candidate after reviewing only the listed source files.

Rules:

1. Do not automatically promote `uncertain` to `confirmed`.
2. Do not treat character lies, legends, dreams, hallucinations, or misleading clues as confirmed.
3. When the same fact appears multiple times, merge `source` and avoid duplicate records.
4. Put conflicts into `continuity_log` or `pending_updates`.
5. Keep unresolved content as `inferred` or `uncertain`.

## Index Update Prompt

Prompt:

```text
Use chinese-novel-writing. Update indexes from accepted cards and summaries.
Indexes are navigation aids, not the source of truth. Each index entry should point to source files and entity ids.
Do not put full prose into indexes.
```

Index entry shape:

```yaml
- id: ""
  name: ""
  aliases: []
  sources: []
  last_seen: ""
  notes: ""
```

## Plot Node Extraction

When building `canon/original_plot_map.md`, extract plot nodes from chapter cards:

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

Use plot nodes later for divergence analysis: preserved, invalidated, inverted, or replacement.

## Divergence Analysis Prompt

Prompt:

```text
Use chinese-novel-writing. Given a divergence point and original plot_nodes, classify each affected node.
Do not write branch results into canon or main. Produce branch-local divergence_analysis.
Flag any major plot decision that requires user confirmation.
```

Schema:

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
