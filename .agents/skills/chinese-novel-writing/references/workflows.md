# Workflows

Each workflow starts by identifying the active project root, current branch, requested output mode, and whether a context pack is required. Drafting, continuation, rewriting, and review always require a context pack.

## create_project

Input: idea, genre, protagonist, setting, or a request to create a novel project.

Steps:

1. Initialize the project with `scripts/init_project.py`.
2. Fill or propose `project_config.yaml`, `user_preferences.md`, and high-level project overview fields.
3. Build initial canon placeholders: protagonist candidates, world assumptions, terms, and hard constraints.
4. Create main outline, first volume outline, early chapter plan, and first chapter function card.
5. Mark generated assumptions as `inferred` unless the user confirms them.

Output: concise project overview, initial next actions, and files created.

## import_story

Input: existing text file, pasted text, or a request to import previous chapters.

Steps:

1. Save raw source text without destructive cleanup.
2. Run `scripts/split_chapters.py` when a text file is available.
3. Build chunk cards and chapter cards in batches. Do not read the whole source into context.
4. Create chapter summaries, volume summaries, story bible drafts, indexes, and import report.
5. Mark extracted facts as `confirmed` only when directly supported by source text. Use `inferred` or `uncertain` for model interpretation.

Output: import report, missing sections, and suggested next extraction batch.

## continue_story

Input: "continue", "write next chapter", or a target chapter request.

Steps:

1. Confirm active branch from `project_config.yaml` or user request.
2. Build context pack with `scripts/build_context_pack.py`, then let Codex fill relevant missing sections from summaries and bible files.
3. If chapter goal is missing, create a chapter function card before writing.
4. Draft according to style guide, current outline, recent summaries, and constraints.
5. Run quality gate.
6. Generate post-write patch with `scripts/create_patch.py` and fill candidate updates.

Output: draft according to output mode, short quality summary, and patch summary.

## rewrite_plot

Input: a "what if", divergence, or request to change original development while preserving characters/world.

Steps:

1. Read canon and original plot map summaries only as needed.
2. Identify divergence point, impact radius, preserved facts, and allowed changes.
3. Create a new branch with `scripts/create_branch.py`.
4. Produce 2-3 route options when the change is high impact.
5. Recalculate relationships, causal chain, antagonist plan, timeline, foreshadowing, and outline within the new branch.
6. Run branch pollution and plausibility checks.

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

1. Require branch, chapter goal, recent summaries or previous ending, relevant facts, foreshadowing, style guide, and hard constraints.
2. Draft only within the active branch.
3. Do not introduce major irreversible plot events without confirmation.
4. Run quality gate.
5. Create post-write patch.

Output: chapter draft plus notes according to output mode.

## revise_text

Input: text to polish, expand, shorten, change style, strengthen conflict, strengthen character voice, or reduce AI-like phrasing.

Steps:

1. Classify requested change: language, scene, or plot.
2. Preserve plot unless the user requests plot-level revision.
3. Keep original text separate unless a target file update is explicitly approved.
4. If revision affects continuity, create patch candidates.

Output: revised text and brief change note.

## review_story

Input: request to审稿, check consistency, or inspect a draft/outline.

Steps:

1. Build context pack with the relevant branch.
2. Check character consistency, world rules, timeline, item state, information asymmetry, foreshadowing, style drift, pacing, and branch pollution.
3. Classify findings by severity.
4. Suggest fixes without silently rewriting major plot.

Output: severe, medium, light issues, and suggested fixes.

## view_bible

Input: request to view characters, world bible, items, terms, timeline, foreshadowing, branches, context pack, or pending updates.

Steps:

1. Read only requested files or summaries.
2. Prefer concise tables or grouped summaries.
3. Keep deprecated facts out of normal context unless the user requests history.

Output: requested bible view and any missing/uncertain markers.
