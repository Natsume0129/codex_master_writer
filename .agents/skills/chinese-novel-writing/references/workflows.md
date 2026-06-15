# Workflows

Each workflow starts by identifying the active project root, current branch, requested output mode, and whether a context pack is required. Drafting, continuation, rewriting, and review always require a context pack.

## create_project

Input: idea, genre, protagonist, setting, or a request to create a novel project.

Steps:

1. Initialize the project with `scripts/novel_project.py init`.
2. Fill or propose `project_config.yaml`, `user_preferences.md`, and high-level project overview fields.
3. Build initial canon placeholders: protagonist candidates, world assumptions, terms, and hard constraints.
4. Create main outline, first volume outline, early chapter plan, and first chapter function card.
5. Mark generated assumptions as `inferred` unless the user confirms them.

Output: concise project overview, initial next actions, and files created.

## import_story

Input: existing text file, pasted text, or a request to import previous chapters.

Steps:

1. Save raw source text without destructive cleanup.
2. Run `scripts/novel_project.py split-import` when a text file is available; it chains chapter splitting, chunk splitting, progress initialization, and first batch creation.
3. Process only the chunks listed in the generated batch file. Do not read `raw_text/full_text.txt`.
4. Run `scripts/novel_project.py mark-done` after chunk cards are created, or mark failures with an error note.
5. Run `scripts/novel_project.py create-batch` for the next batch when needed.
6. Check closure with `scripts/novel_project.py import-status`.
7. Build chapter cards with `scripts/novel_project.py create-chapter-card-batch` after all chunks for a chapter are done.
8. Build volume summaries with `scripts/novel_project.py create-volume-summary-batch` after chapter cards are reviewed.
9. Create story-bible patch candidates with `scripts/novel_project.py create-bible-patch-batch`; do not edit canon directly.
10. Use `scripts/novel_project.py mark-done` for later-stage batch metadata after reviewing generated chapter cards, volume summaries, or story-bible patch candidates.
11. Run `scripts/novel_project.py build-indexes` after extracted cards or canon files change.
12. Mark extracted facts as `confirmed` only when directly supported by source text. Use `inferred` or `uncertain` for model interpretation.

Output: import report, missing sections, and suggested next extraction batch.

Validation may include workflow suggestions such as the next batch to process. Treat suggestions as guidance, not failure.

## continue_story

Input: "continue", "write next chapter", or a target chapter request.

Steps:

1. Confirm active branch from `project_config.yaml` or user request.
2. If chapter goal is missing, create a chapter function card before writing with `scripts/novel_project.py create-function-card`.
3. If retrieval index is missing or stale, run `scripts/novel_project.py build-retrieval-index`.
4. Optionally run `scripts/novel_project.py query-retrieval-index` to create candidate selectors.
5. Build context pack with `scripts/novel_project.py build-context-pack`; use `--auto-select` when selectors are missing or stale, or `--use-retrieval-index` when the v0.7 retrieval trace should be included.
6. Audit the pack with `scripts/novel_project.py audit-context-pack` or use `build-context-pack --write-audit`.
7. Generate a deterministic writing prompt with `scripts/novel_project.py create-draft-prompt`; pass `--target-length` or `--style-strictness` when the user gives writing-control preferences.
8. Draft according to the generated prompt, style guide, current outline, recent summaries, and constraints.
9. Run quality gate and create a durable report plus review prompt with `scripts/novel_project.py create-quality-report --with-prompt` when a review file is needed.
10. Generate post-write patch with `scripts/novel_project.py create-patch` and fill candidate updates.
11. Create a patch review report with `scripts/novel_project.py review-patch`.
12. Dry-run `scripts/novel_project.py apply-patch` if the user wants to apply safe post-write updates.

Output: draft according to output mode, short quality summary, and patch summary.

## rewrite_plot

Input: a "what if", divergence, or request to change original development while preserving characters/world.

Steps:

1. Create or select an isolated branch with `scripts/novel_project.py new-branch`, defaulting to `--inherit skeleton`.
2. If retrieval index is missing or stale, run `scripts/novel_project.py build-retrieval-index --include-branches`.
3. Optionally run `scripts/novel_project.py query-retrieval-index` for the divergence terms.
4. Build a rewrite context pack with `scripts/novel_project.py build-context-pack --task rewrite_plot --use-retrieval-index`.
5. Audit the pack with `scripts/novel_project.py audit-context-pack` or `--write-audit`.
6. Create a branch-local plot node map with `scripts/novel_project.py create-plot-node-map`.
7. Create divergence analysis with `scripts/novel_project.py create-divergence-analysis`.
8. Create a rewrite plan prompt and replacement-route skeleton with `scripts/novel_project.py create-rewrite-plan`.
9. Let Codex/model fill or revise rewrite artifacts from the generated prompt. The prompt does not generate prose.
10. Create a branch diff report with `scripts/novel_project.py create-branch-diff-report` for user review.
11. Run `scripts/novel_project.py validate` and resolve missing artifact suggestions.
12. Ask the user to confirm required decisions or choose a replacement route before outline or draft work.

Rules:

- Do not read `raw_text/full_text.txt`.
- Do not edit `canon/` or `branches/main/`.
- Do not auto-apply patches or merge branches.
- Put major plot changes under `requires_user_decision`.

Output: branch created, divergence summary, route recommendation, outline impact, and pending decisions.

## build_outline

Input: request for high-level outline, volume outline, chapter outline, or scene beats.

Steps:

1. Build or inspect context pack.
2. Choose outline level: premise, mainline, volume, chapter, scene, or chapter function card.
3. Track plot lines: main conflict, character growth, relationships, antagonist, foreshadowing, world reveal, emotion, and resources.
4. Add source/status/confidence for facts introduced as bible candidates.
5. Generate a patch for major outline changes.

Output: requested outline level and concise update notes.

## draft_chapter

Input: chapter number, chapter goal, outline, or "write this chapter".

Steps:

1. Require branch, chapter function card or chapter goal, recent summaries or previous ending, relevant facts, foreshadowing, style guide, and hard constraints.
2. Build the context pack and create a draft prompt, including target length or style strictness when provided.
3. Draft only within the active branch.
4. Do not introduce major irreversible plot events without confirmation.
5. Run quality gate with a review prompt when the report should persist.
6. Create post-write patch and patch review report.

Output: chapter draft plus notes according to output mode.

## revise_text

Input: text to polish, expand, shorten, change style, strengthen conflict, strengthen character voice, or reduce AI-like phrasing.

Steps:

1. Classify requested change: language, scene, or plot.
2. Preserve plot unless the user requests plot-level revision.
3. Keep original text separate unless a target file update is explicitly approved.
4. If revision affects continuity, create patch candidates.
5. Apply patches only through review and dry-run first; do not overwrite canon directly.

Output: revised text and brief change note.

## review_story

Input: request to审稿, check consistency, or inspect a draft/outline.

Steps:

1. Query retrieval index when candidate context is unclear.
2. Build context pack with the relevant branch; use `--auto-select` if the user did not provide selectors, or `--use-retrieval-index` for a v0.7 candidate trace.
3. Audit the pack before review when traceability or budget matters.
4. Check character consistency, world rules, timeline, item state, information asymmetry, foreshadowing, style drift, pacing, and branch pollution.
5. Classify findings by severity.
6. Write `branches/<branch>/reviews/chapter_XXX_quality_report.md` and a review prompt with `create-quality-report --with-prompt` when the review should persist.
7. Suggest fixes without silently rewriting major plot.

Output: severe, medium, light issues, and suggested fixes.

## view_bible

Input: request to view characters, world bible, items, terms, timeline, foreshadowing, branches, context pack, or pending updates.

Steps:

1. Read only requested files or summaries.
2. Prefer concise tables or grouped summaries.
3. Keep deprecated facts out of normal context unless the user requests history.

Output: requested bible view and any missing/uncertain markers.
