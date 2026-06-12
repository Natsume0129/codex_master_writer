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

## Project Directory

The standard project template is under `templates/novel_project/`. Scripts copy this directory when initializing a new novel project. The template is intentionally empty of real story content.

Important directories:

- `canon/`: base facts and original plot map. Alternate branches must not overwrite it.
- `branches/main/`: main continuation line.
- `branches/<name>/`: isolated rewrite branch with its own timeline, outline, foreshadowing, continuity log, chapter summaries, drafts, and reviews.
- `pending_updates/`: candidate updates generated after writing. These patches are reviewed before merging into bible files.
- `context_packs/`: compact input bundles for current tasks.

## Canon, Bible, Indexes, and Patches

`canon/` is the confirmed or source-tracked foundation. It may contain inferred and uncertain facts, but those must be labeled. Indexes are navigation aids, not the source of truth. Patches are proposals; they do not update canon or branches automatically.

## Long-Form Boundary

Large novels are stored in files and processed by layers: raw text, chapters, chunks, cards, chapter summaries, volume summaries, indexes, and task context packs. The workflow forbids loading a whole long work into one model context.

## Branch Isolation

`rewrite_plot` creates an alternate branch. That branch can reinterpret future development, but it cannot write its character states, timeline, or foreshadowing back into `canon/` or `branches/main/` unless the user explicitly asks for a reviewed merge.
