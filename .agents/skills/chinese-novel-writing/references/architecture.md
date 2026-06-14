# Architecture

This skill is a Codex workflow package, not a novel-writing application. It provides instructions, references, templates, and deterministic helper scripts so Codex can maintain a Chinese novel project without treating each request as an isolated prompt.

## Core Idea

A novel project is a file-based knowledge base:

- `raw_text/` stores imported source text and split chapters.
- `extracted/` stores chunk cards, chapter cards, and volume summaries created by Codex/model work.
- `canon/` stores original or confirmed base facts.
- `branches/main/` stores the default continuation line.
- `branches/<branch>/` stores alternate plotlines created by rewrite requests.
- `indexes/` stores lightweight lookup files.
- `context_packs/` stores task-specific context snapshots.
- `pending_updates/` stores candidate bible updates after drafting or outlining.
- `branches/<branch>/draft_prompts/` and `branches/<branch>/reviews/` store v0.5 writing and review workflow artifacts.
- `branches/<branch>/rewrite/` stores v0.6 plot rewrite and divergence-analysis artifacts.

## Project Directory

The standard project template is under `templates/novel_project/`. Its structural skeleton still uses the v0.4 schema, while v0.5 writing-quality artifacts use their own v0.5 markers. Scripts copy this whole directory when initializing a new novel project. This is intentionally kept instead of the older `assets/templates/` single-file layout because the project is directory-shaped and easier to validate as a complete empty skeleton. The template is intentionally empty of real story content.

Important directories:

- `canon/`: base facts and original plot map. Alternate branches must not overwrite it.
- `branches/main/`: main continuation line.
- `branches/<name>/`: isolated rewrite branch with its own timeline, outline, foreshadowing, continuity log, chapter summaries, rewrite artifacts, draft prompts, drafts, and reviews.
- `pending_updates/`: candidate updates generated after writing. These patches are reviewed before merging into bible files.
- `context_packs/`: compact input bundles for current tasks.

## Canon, Bible, Indexes, and Patches

`canon/` is the confirmed or source-tracked foundation. It may contain inferred and uncertain facts, but those must be labeled. Indexes are navigation aids, not the source of truth. Patches are proposals; they do not update canon or branches automatically.

## Long-Form Boundary

Large novels are stored in files and processed by layers: raw text, chapters, chunks, cards, chapter summaries, volume summaries, indexes, and task context packs. The workflow forbids loading a whole long work into one model context.

## Branch Isolation

`rewrite_plot` creates an alternate branch. That branch can reinterpret future development, but it cannot write its character states, timeline, or foreshadowing back into `canon/` or `branches/main/` unless the user explicitly asks for a reviewed merge.
