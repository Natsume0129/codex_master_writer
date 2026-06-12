# Context Pack

A context pack is the only approved input bundle for continuation, drafting, rewriting, and review. It contains task-relevant context, not the whole project.

## v0.2 Builder Inputs

`build_context_pack.py` accepts selectors so Codex can include relevant entities without dumping whole bible files:

```bash
python scripts/build_context_pack.py --project ./projects/my-novel --branch main --task continue_story --chapter 12 --characters 林照夜 沈青辞 --locations 剑冢 --items 破剑 --foreshadowing-ids foreshadowing_007 --include-recent 3 --previous-ending-chars 1500 --format markdown --force
```

If selectors are absent or indexes do not contain matching entries, the builder records `missing_sections` instead of inserting large unrelated snippets.

## Default Structure

```yaml
context_pack:
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

## Review Context

Use the draft or outline being reviewed, branch-local timeline, relevant bible facts, recent summaries, foreshadowing status, and hard constraints.

## Exclusions

- Do not include deprecated facts unless the user asks for history.
- Do not include full `raw_text/full_text.txt`.
- Do not include other branch timelines or branch-only character states unless comparing branches is the task.
- Do not include all bible files by default; summarize relevant entries.
- Do not default to the first 4000 characters of `characters.yaml`, `items.yaml`, or other bible files as relevant context.
