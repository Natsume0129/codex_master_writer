# Context Pack

A context pack is the only approved input bundle for continuation, drafting, rewriting, and review. It contains task-relevant context, not the whole project.

## v0.4 Builder Inputs

`build_context_pack.py` accepts selectors so Codex can include relevant entities without dumping whole bible files:

```bash
python scripts/novel_project.py build-context-pack --project-root ./projects/my-novel --branch main --task continue_story --chapter 12 --characters 林照夜 沈青辞 --locations 剑冢 --items 破剑 --foreshadowing-ids foreshadowing_007 --include-recent 3 --previous-ending-chars 1500 --format markdown --force
```

If selectors are absent or indexes do not contain matching entries, the builder records `missing_sections` instead of inserting large unrelated snippets.

v0.4 can also auto-select selectors from indexes:

```bash
python scripts/novel_project.py build-context-pack --project-root ./projects/my-novel --branch main --task continue_story --chapter 12 --auto-select --selector-source all --max-selectors 20 --write-selector-report --force
```

Auto-selection uses the current chapter function card, recent summaries, and matching imported chapter card as hint text, then matches those hints against `indexes/*_index.yaml`. It does not use embeddings, external APIs, `raw_text/full_text.txt`, or full-canon scanning. Manual selectors remain first and are never removed by auto-select.

When `--chapter` is provided, the builder automatically looks for:

```text
branches/<branch>/chapter_function_cards/chapter_XXX_function_card.yaml
```

Only the active branch's function card is loaded. The card is included as `current_arc.chapter_function_card`, and `chapter_goal` is also copied to `current_arc.chapter_goal` / `current_arc.current_chapter_goal`.

Entity retrieval is conservative:

1. Check the relevant `indexes/*_index.yaml`.
2. Use matching ids/names/aliases from the index to find full source blocks in `canon/*.yaml`.
3. Fall back to short line matches only when a complete block cannot be found.
4. Record retrieval choices in `retrieval_notes`.

Indexes are navigation aids, not durable truth. If index and canon disagree, prefer source-backed canon entries and mark the conflict for review.

v0.4 context packs include a schema marker. Markdown packs use `Schema version: 0.4`; YAML packs use `context_pack.schema_version`.

## v0.7 Retrieval Trace And Audit

`build-context-pack` keeps its default behavior. It uses the retrieval index only when the caller passes `--use-retrieval-index`.

Typical v0.7 flow:

```bash
python scripts/novel_project.py build-retrieval-index --project-root ./projects/my-novel --include-branches --force
python scripts/novel_project.py query-retrieval-index --project-root ./projects/my-novel --query "chapter 12 ally reveal" --branch main --top-k 10 --force
python scripts/novel_project.py build-context-pack --project-root ./projects/my-novel --branch main --task continue_story --chapter 12 --use-retrieval-index --retrieval-query "chapter 12 ally reveal" --retrieval-top-k 10 --write-audit --force
```

The pack may include a `## Retrieval Trace` section with:

- index file
- query
- selected candidate metadata
- omitted count
- candidate source files
- warnings

The trace is not source truth. It points Codex/model to source files that still need verification. Do not copy full candidate files into the pack; include only short summaries, selectors, and source references.

`--context-budget-chars` is used by audit only. If the budget is exceeded, the audit reports a warning; it does not silently delete user-selected context.

`audit-context-pack` checks budget, raw-text path references, possible raw full-text inclusion by size, branch boundaries, missing source/status/confidence markers, deprecated facts, oversized sections, and missing Retrieval Trace. It does not read `raw_text/full_text.txt` content.

## Default Structure

```yaml
context_pack:
  schema_version: "0.4"
  task:
    type: continue_story
    user_request: ""
    output_mode: draft_with_notes
    branch: main
    chapter: null
  project_snapshot:
    project_config: ""
    style_guide_summary: ""
    genre_strategy_summary: ""
  current_arc:
    current_outline: ""
    current_volume_summary: ""
    current_chapter_goal: ""
    chapter_goal: ""
    chapter_function_card: ""
  recent_context:
    previous_chapter_summaries: []
    previous_chapter_ending_excerpt: ""
  relevant_entities:
    characters: []
    relationships: []
    locations: []
    organizations: []
    items: []
  plot_threads:
    main_plot: ""
    side_plots: []
    antagonist_plan: ""
  foreshadowing_and_questions:
    open_foreshadowing: []
    payoff_candidates: []
    open_questions: []
  timeline_constraints:
    current_story_time: ""
    recent_events: []
    forbidden_time_conflicts: []
  hard_constraints:
    must_not_change: []
    must_not_reveal_yet: []
    branch_boundaries: []
  auto_selection:
    enabled: false
    selector_source: all
    max_selectors: 20
    source_files: []
    notes: []
  retrieval_notes: []
  retrieval_trace:
    enabled: false
    index_file: ""
    query: ""
    selected_candidates: []
    omitted_count: 0
    source_files: []
    warnings: []
  missing_sections: []
```

## Budget Priority

If context is too large, keep items in this order:

1. User request.
2. Active branch and chapter goal.
3. Previous chapter ending excerpt.
4. Last three chapter summaries.
5. Current volume summary.
6. Relevant characters, places, items, and relationships.
7. Relevant foreshadowing and open questions.
8. Timeline and hard constraints.
9. Style guide summary.
10. Older source evidence snippets.

## Continuation Context

Use recent chapter summaries, previous ending, current outline, relevant character states, relevant foreshadowing, style guide, and hard constraints. Do not read raw full text.

## Rewrite Context

Use canon facts, original plot map summary, divergence point, must-preserve facts, impact radius, active alternate branch files, and branch-local timeline. Do not mix in unrelated alternate branches.

For `rewrite_plot`, the context pack should include only task-relevant excerpts from:

- `branches/<branch>/branch_config.yaml`
- `branches/<branch>/divergence_point.yaml`
- selected chapter summaries
- branch-local timeline excerpts
- relevant story bible entries
- style constraints
- `canon/original_plot_map.md`
- `branches/<branch>/rewrite/plot_node_map.yaml` if available
- `branches/<branch>/rewrite/divergence_analysis.yaml` if available
- `branches/<branch>/rewrite/replacement_routes.yaml` if available
- `missing_sections`

Do not read `raw_text/full_text.txt`, do not default to the whole novel, and do not include unrelated branch artifacts.

## Review Context

Use the draft or outline being reviewed, branch-local timeline, relevant bible facts, recent summaries, foreshadowing status, and hard constraints.

## Exclusions

- Do not include deprecated facts unless the user asks for history.
- Do not include full `raw_text/full_text.txt`.
- Do not include other branch timelines or branch-only character states unless comparing branches is the task.
- Do not include other branch chapter function cards.
- Do not include all bible files by default; summarize relevant entries.
- Do not default to the first 4000 characters of `characters.yaml`, `items.yaml`, or other bible files as relevant context.
