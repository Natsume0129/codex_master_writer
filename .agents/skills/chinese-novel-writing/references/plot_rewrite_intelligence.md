# Plot Rewrite Intelligence

v0.6 upgrades `rewrite_plot` from branch isolation to an executable divergence-analysis workflow. It still does not write prose, call external services, infer story meaning in scripts, or auto-confirm major plot changes.

## Workflow

1. Confirm project root and active branch.
2. Ensure `rewrite_plot` uses an isolated branch, never `canon/` or `branches/main/` for alternate outcomes.
3. Build a `rewrite_plot` context pack.
4. Do not read `raw_text/full_text.txt`.
5. Use only needed summaries, story bible entries, timeline excerpts, `branch_config.yaml`, `divergence_point.yaml`, `canon/original_plot_map.md`, and existing rewrite artifacts.
6. Identify the divergence point.
7. Classify impact radius.
8. Build a plot node map.
9. Mark plot nodes as preserved, invalidated, inverted, replacement_needed, optional, or requires_user_decision.
10. Generate 2-3 replacement routes.
11. Mark major changes under `requires_user_decision`.
12. Keep rewrite artifacts branch-local under `branches/<branch>/rewrite/`.
13. Generate a branch diff report for user review.
14. Run validate for missing rewrite artifacts and branch pollution risks.

## Impact Radius

`level_1_local`

- Local event divergence.
- Affects one scene or one to two chapters.
- Example: the protagonist does not lose a specific contest.

`level_2_relationship`

- Character relationship, faction, or emotional-line divergence.
- Affects trust, secrets, cooperation, hostility, or relationship stage.
- Example: the protagonist and antagonist become allies early.

`level_3_main_plot`

- Mainline structure divergence.
- Affects main goal, antagonist structure, climax design, or volume structure.
- Example: the original final enemy dies early.

`level_4_world_rule`

- World rule, history, or power-system divergence.
- Rewrites setting logic, historical causality, or power premises.
- Example: the source of the cultivation system changes.

## Plot Node Classes

- `preserved`: still works after divergence.
- `invalidated`: no longer works because a required condition changed.
- `inverted`: function, alignment, or meaning reverses.
- `replacement_needed`: the old node cannot stand and needs a new causal substitute.
- `optional`: can be kept or removed without breaking the route.
- `requires_user_decision`: touches a major plot control point.

## Major Plot Control

Do not automatically:

- kill important characters
- make important characters betray
- reveal core secrets
- reconcile long-term enemies
- confirm major romance or CP direction
- identify the final antagonist
- reverse core world rules
- overwrite user source text

Major changes can appear only as branch-local candidates or explicit `requires_user_decision` entries.

## Branch Pollution Firewall

- Write only branch-local rewrite artifacts.
- Do not edit `canon/`.
- Do not edit `branches/main/`.
- Do not merge branches.
- Do not apply patches automatically.
- A branch diff report is a report, not a merge action.

## v0.6 Artifacts

Default directory:

```text
branches/<branch>/rewrite/
```

Files:

- `plot_node_map.yaml`: source-backed node inventory and node survival fields.
- `divergence_analysis.yaml`: structured divergence, impact radius, preserved/invalidated/inverted/replacement lists, risks, and required decisions.
- `replacement_routes.yaml`: candidate route skeletons for model/user review.
- `rewrite_plan_prompt.md`: prompt for Codex/model to fill rewrite artifacts.
- `branch_diff_report.md`: human-readable diff report for route review.

`causal_impact_log.md` remains the ongoing narrative reasoning log. The `rewrite/` files are structured planning artifacts and review surfaces.

## Commands

```bash
python scripts/novel_project.py new-branch --project-root ./projects/my-novel --name what_if_villain_ally --divergence "主角提前和反派结盟" --inherit skeleton --force
python scripts/novel_project.py build-context-pack --project-root ./projects/my-novel --branch what_if_villain_ally --task rewrite_plot --chapter 12 --user-request "如果主角提前和反派结盟，后续剧情如何重构？" --force
python scripts/novel_project.py create-plot-node-map --project-root ./projects/my-novel --branch what_if_villain_ally --force
python scripts/novel_project.py create-divergence-analysis --project-root ./projects/my-novel --branch what_if_villain_ally --impact-radius level_2_relationship --force
python scripts/novel_project.py create-rewrite-plan --project-root ./projects/my-novel --branch what_if_villain_ally --force
python scripts/novel_project.py create-branch-diff-report --project-root ./projects/my-novel --branch what_if_villain_ally --force
```
