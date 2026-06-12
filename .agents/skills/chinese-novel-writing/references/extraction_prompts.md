# Extraction Prompts

Use these prompts when importing a long Chinese novel in batches. Do not process the whole novel at once. Read only the chunk files for the current batch and write structured outputs with source/status/confidence.

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

Schema:

```yaml
chapter_id: ""
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

## Volume Summary Merge Prompt

Prompt:

```text
Use chinese-novel-writing. Merge the chapter_cards for one volume into a volume_summary.
Summarize plot progress and arcs; do not add unsourced canon. Preserve unresolved questions.
```

Schema:

```yaml
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
