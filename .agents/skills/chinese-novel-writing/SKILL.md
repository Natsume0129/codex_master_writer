---
name: chinese-novel-writing
description: "Use this skill for Chinese novel writing projects and long-form fiction workflows, including project creation, story import, continuation, outline building, style profiling, story bible maintenance, retrieval index generation, context pack audit, branch-isolated plot rewriting, alternate plot planning, divergence analysis, and quality review."
---

# Chinese Novel Writing

Use this skill when the user wants to build or maintain a Chinese novel project, including original creation, importing an existing story, continuation, story bible maintenance, outline work, style profiling, consistency review, or alternate-plot rewriting through isolated branches.

Do not use this skill for unrelated short-text polishing, non-fiction writing, casual chat, or when the user explicitly asks not to use it.

## Core Modes

- `create_project`: start a novel from an idea, genre, protagonist, setting, or blank project.
- `continue_story`: continue an imported or existing novel from the current branch and context pack.
- `rewrite_plot`: preserve canon facts while creating an isolated alternate branch from a divergence point.

## User Entrypoints

Support these intents: `create_project`, `import_story`, `continue_story`, `rewrite_plot`, `build_outline`, `draft_chapter`, `revise_text`, `review_story`, and `view_bible`.

Map each request to the nearest workflow in `references/workflows.md`. If the request is ambiguous, infer a conservative workflow from the current project files and ask only when the branch, source text, or requested output cannot be safely determined.

## Internal Pipelines

- `import_pipeline`: save raw text, split chapters/chunks, create source-tracked cards, then build bible/index placeholders.
- `extraction_progress_manager`: track chunk/chapter/batch extraction state in `imports/extraction_progress.yaml`.
- `index_builder`: rebuild lightweight navigation indexes from extracted cards and canon files; indexes are not source of truth.
- `retrieval_index_pipeline`: build/query v0.7 retrieval candidates from structured artifacts only, then audit context packs for traceability and budget.
- `context_pack_builder`: assemble only task-relevant facts, summaries, and constraints.
- `style_voice_pipeline`: create v0.8 style profile, character voice sheet, scene outline, style audit, and revision plan artifacts without writing prose.
- `drafting_pipeline`: generate a draft prompt from the chapter function card, context pack, and optional v0.8 style/voice/scene artifacts; write only after model review, then run quality checks.
- `continuation_pipeline`: continue only after branch and recent context are known.
- `plot_rewrite_pipeline`: create or use an alternate branch, then generate v0.6 plot-node, divergence-analysis, rewrite-plan, and branch-diff artifacts before changing causal development.
- `post_write_update_pipeline`: generate pending patch files instead of directly editing bible files.
- `patch_apply_pipeline`: create a patch review report, dry-run pending patches first, then apply only limited safe updates after explicit confirmation.
- `quality_gate`: generate or fill quality reports from draft plus context pack, checking consistency, branch boundaries, style drift, pacing, and major plot-control risks.

## P0 Hard Rules

1. Never load an entire long novel into one model context. A very long work may be stored in project files, but tasks must use chapter/chunk summaries, indexes, and context packs.
2. Build a context pack before every drafting, continuation, rewrite, or review task. Do not default to reading the whole database or raw full text.
3. Every important fact must carry `source`, `status`, and `confidence`. Keep inferred or uncertain facts labeled as such; user overrides have the highest priority.
4. Plot rewriting must use an isolated branch under `branches/<branch>/`. Never write alternate-plot states back into `canon/` or `branches/main/`.
5. Post-write updates must generate `pending_updates/*.yaml` patches. Do not directly overwrite core bible files such as characters, timeline, world bible, or foreshadowing.
6. Do not create or rely on a built-in adult content safety checker. This skill focuses on project workflow, continuity, writing support, and branch isolation.
7. Do not automatically decide major plot changes: core character death, betrayal, confirmed romance, early secret reveals, final antagonist identity, world-rule reversal, main-goal changes, original-mainline rewrites, or branch merges.
8. Do not overwrite user source text. Preserve raw imports and keep generated changes separate unless the user explicitly approves a write target.
9. Retrieval indexes are candidate navigation aids only. They must not replace canon, extracted cards, branch artifacts, or pending patches.
10. Style profiles and character voice sheets are writing controls, not source-of-truth fact stores. They must not override canon, branch facts, chapter function cards, or context packs.

## Reference Loading

Load only the reference needed for the current task:

- Architecture or directory questions: `references/architecture.md`.
- User workflow selection: `references/workflows.md`.
- Long text import: `references/import_pipeline.md`.
- Batch extraction prompts and card schemas: `references/extraction_prompts.md`.
- Drafting, continuation, review, or rewrite context: `references/context_pack.md`.
- Retrieval index, query reports, context audits, or acceptance checks: `references/retrieval_index.md`.
- Chapter goal planning before drafting: `references/chapter_function_card.md`.
- Style profile, character voice, scene outline, style audit, or revision loop: `references/style_voice_system.md`.
- Alternate plot or branch work: `references/branch_system.md`.
- Plot rewrite divergence analysis: `references/plot_rewrite_intelligence.md`.
- Post-write database updates: `references/patch_update.md`.
- Consistency review: `references/quality_gate.md`.
- Data fields and templates: `references/schemas.md`.
- Response size and automation choices: `references/output_modes.md`.
- User-facing commands: `references/codex_usage.md`.

## Script Usage

Use `scripts/novel_project.py` as the preferred v0.8 unified CLI for deterministic file work. Use lower-level scripts only when fine-grained control is needed.

- `scripts/novel_project.py` exposes `init`, `split-import`, `init-progress`, `create-batch`, `import-status`, `create-chapter-card-batch`, `create-volume-summary-batch`, `create-bible-patch-batch`, `mark-done`, `build-indexes`, `build-retrieval-index`, `query-retrieval-index`, `new-branch`, `create-function-card`, `build-context-pack`, `audit-context-pack`, `acceptance-check`, `create-style-profile`, `create-voice-sheet`, `create-scene-outline`, `create-draft-prompt`, `create-style-audit`, `create-revision-plan`, `create-plot-node-map`, `create-divergence-analysis`, `create-rewrite-plan`, `create-branch-diff-report`, `create-quality-report`, `create-patch`, `review-patch`, `create-patch-review`, `apply-patch`, and `validate`.
- `scripts/init_project.py` creates a project from templates.
- `scripts/split_chapters.py` splits imported text and writes an import manifest.
- `scripts/split_chunks.py` splits chapter files into overlapping chunks and writes a chunk manifest.
- `scripts/init_extraction_progress.py` initializes `imports/extraction_progress.yaml`.
- `scripts/create_extraction_batch.py` creates the next small extraction batch prompt and metadata file.
- `scripts/import_status.py` reports import closure status and next deterministic actions.
- `scripts/create_chapter_card_batch.py` creates chapter-card prompt batches from completed chunk cards.
- `scripts/create_volume_summary_batch.py` creates volume-summary prompt batches from chapter cards.
- `scripts/create_bible_patch_batch.py` creates story-bible patch prompt batches and pending patch skeletons without editing canon.
- `scripts/mark_extraction_done.py` marks chunks or batches as queued, processing, done, failed, or skipped.
- `scripts/build_indexes.py` rebuilds lightweight navigation indexes without external services.
- `scripts/build_retrieval_index.py` builds `indexes/retrieval_index.jsonl` and a summary report from structured artifacts only.
- `scripts/query_retrieval_index.py` creates deterministic retrieval candidate reports without embeddings or semantic search.
- `scripts/audit_context_pack.py` audits context packs for budget, traceability, raw-text risk, branch boundaries, and Retrieval Trace.
- `scripts/run_acceptance_checks.py` runs local deterministic compatibility checks and writes an acceptance report.
- `scripts/create_branch.py` creates isolated alternate-plot branches.
- `scripts/create_plot_node_map.py` creates a v0.6 branch-local plot-node map skeleton.
- `scripts/create_divergence_analysis.py` creates a v0.6 branch-local divergence-analysis skeleton.
- `scripts/create_rewrite_plan.py` creates a v0.6 rewrite-plan prompt and replacement-route skeleton.
- `scripts/create_branch_diff_report.py` creates a v0.6 branch diff report for user review.
- `scripts/create_chapter_function_card.py` creates branch-local v0.5 chapter function cards.
- `scripts/create_style_profile.py` creates a v0.8 style profile skeleton and optional prompt.
- `scripts/create_voice_sheet.py` creates a v0.8 character voice sheet skeleton and optional prompt.
- `scripts/create_scene_outline.py` creates a v0.8 scene outline skeleton and optional prompt.
- `scripts/build_context_pack.py` creates a context-pack skeleton without reading full raw text; `--auto-select` can fill selectors from indexes and chapter/recent hints, `--use-retrieval-index` can add a v0.7 Retrieval Trace, and v0.8 flags can include bounded style/voice/scene artifacts.
- `scripts/create_draft_prompt.py` creates a drafting prompt from the context pack, chapter function card, and optional v0.8 style/voice/scene/revision artifacts without writing prose; `--target-length`, `--style-strictness`, and `--anti-ai-flavor-level` are prompt controls only.
- `scripts/create_quality_report.py` creates a review template and can create a review prompt under `branches/<branch>/reviews/`.
- `scripts/create_style_audit.py` creates a v0.8 style audit report skeleton and optional prompt.
- `scripts/create_revision_plan.py` creates a v0.8 revision plan and embedded revision prompt.
- `scripts/create_patch.py` creates pending post-write update patches.
- `scripts/create_patch_review.py` creates human-readable patch review reports before patch apply. Prefer `review-patch`; `create-patch-review` remains compatible.
- `scripts/apply_patch.py` dry-runs and then applies limited safe patch updates after confirmation.
- `scripts/validate_project.py` checks project structure.

Scripts do not perform AI extraction, drafting, style imitation, quality review, or plot reasoning. Those remain Codex/model tasks guided by the references.

## Output Strategy

- If the user asks for only正文, use `draft_only`.
- If the user asks for analysis, use `analysis_only` or `full`.
- If the user asks for the complete workflow, provide draft, concise post-write notes, quality summary, patch summary, and next-step suggestions.
- Otherwise default to `draft_with_notes` and avoid oversized reports.

## Forbidden Behaviors

- Do not turn this skill into a web app, database service, external API client, or networked tool.
- Do not place real long-form novel samples inside the skill package.
- Do not hard-code one genre, author style, or named work.
- Do not merge branch facts into canon/main without explicit user confirmation.
- Do not promote `inferred` or `uncertain` facts to `confirmed` without evidence.
- Do not directly edit core bible files after drafting; generate a patch first.
