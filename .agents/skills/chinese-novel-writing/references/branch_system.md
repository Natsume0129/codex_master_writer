# Branch System

The branch system prevents alternate-plot rewriting from polluting canon or the default continuation line.

## Areas

- `canon/`: source-backed base facts and original plot map. It is not a drafting area.
- `branches/main/`: default continuation line.
- `branches/<branch>/`: alternate plotline created for a divergence.

## Rewrite Rule

Any request like "what if", "假如", "保留设定但改写", "让某角色没死", "让反派成为朋友", or "改变世界规则" must create or use an isolated branch.

Before generating a rewritten outline:

1. Identify `divergence_point`.
2. Estimate `impact_radius`.
3. Map original `plot_nodes`.
4. Classify nodes as preserved, invalidated, inverted, or replacement.
5. Generate the new branch outline from the mapping.

## Required Alternate Branch Files

Each alternate branch should have:

- `branch_config.yaml`
- `divergence_point.yaml`
- `causal_impact_log.md`
- `outline.md`
- `timeline.yaml`
- `foreshadowing.yaml`
- `continuity_log.md`
- `chapter_summaries/`
- `chapter_function_cards/`
- `drafts/`
- `reviews/`

Use `--inherit skeleton` by default. It creates empty branch-local files and does not copy main's concrete timeline, outline, or foreshadowing. Use `--inherit current-state --base-chapter N` only when the divergence starts after an existing chapter and copied state must be pruned.

## Divergence Point

Record:

- original fact
- changed fact
- story time
- impact radius
- affected characters, factions, and plot nodes
- must-preserve facts
- can-change areas
- base branch
- base chapter
- inherit mode
- whether pruning is required
- invalidated main events
- preserved plot nodes
- replacement-needed nodes

## Pollution Controls

- Branch character states do not write back to `canon/`.
- Branch timeline events do not write back to `branches/main/`.
- Branch foreshadowing does not write into another branch.
- `canon/` records original/base facts and source-tracked corrections only.
- Merging branch ideas back to main requires an explicit user-approved patch.

## Causal Impact Log

Use `causal_impact_log.md` to track cause-effect changes after divergence:

- changed premise
- immediate consequences
- relationship impacts
- faction impacts
- outline nodes preserved, removed, inverted, or replaced
- unresolved risks

## Divergence Analysis

Use the schema in `schemas.md` to record `divergence_analysis` with invalidated, preserved, inverted, and replacement plot nodes. Do not write branch-local outcomes back into canon.
