# Import Pipeline

The import pipeline stores source text, splits it, and creates layered summaries. It is designed for long-form fiction where the full source cannot be placed into one prompt.

## Flow

```text
raw_text/full_text.txt
  -> raw_text/chapters/chapter_0001.txt
  -> chunks/chapter_0001_chunk_0001.txt
  -> imports/extraction_progress.yaml
  -> imports/batches/batch_0001_chunk_cards.md
  -> extracted/chunk_cards/chapter_0001_chunk_0001.yaml
  -> extracted/chapter_cards/chapter_0001.yaml
  -> extracted/volume_summaries/volume_0001.md
  -> canon/* and indexes/*
```

## Hard Limit

Never load a 2-million-character or 2-million-word novel into a single context. Store it on disk, split it into chapters and chunks, and summarize progressively.

## Chapter Recognition

The chapter splitter uses common Chinese headings such as:

- `第1章`, `第一章`, `第001章`
- `卷一`, `第一卷`
- `序章`, `楔子`, `番外`

The split is conservative. It preserves original text and reports suspicious empty, duplicate, or very long chapters.

## Chunking

Run chunk splitting after chapter splitting:

```bash
python scripts/novel_project.py split-import --project-root ./projects/my-novel --source ./novel.txt --chunk-size 6000 --overlap 500 --batch-size 5 --force --clean
```

`split_chunks.py` writes `imports/chunk_manifest.yaml`. Each chunk records `chunk_id`, `chapter_id`, `source_file`, `output_file`, `start_char`, `end_char`, `char_count`, `overlap_prev`, and `overlap_next`.

Use `--clean` only with `--force`. It removes old generated `*_chunk_*.txt` files from the chunk output directory before regenerating chunks. It does not remove raw source text or extracted cards.

## Extraction Progress

Initialize progress after chunking:

```bash
python scripts/novel_project.py init-progress --project-root ./projects/my-novel --force
```

This creates `imports/extraction_progress.yaml` with `project`, `settings`, `chunks`, `chapters`, and `batches` sections. The progress file is the checkpoint for resuming a long import. Chunk states are `pending`, `queued`, `processing`, `done`, `failed`, and `skipped`.

Create a small batch without reading chunk text:

```bash
python scripts/novel_project.py create-batch --project-root ./projects/my-novel --stage chunk_cards --batch-size 5 --force
```

The batch files are written under `imports/batches/`. Codex should read only the chunk files listed in that batch, generate `extracted/chunk_cards/<chunk_id>.yaml`, and then update progress:

```bash
python scripts/novel_project.py mark-done --project-root ./projects/my-novel --batch-id batch_0001 --status done
```

Use `--retry-failed` with `create_extraction_batch.py` only when intentionally retrying failed chunks.

Long chapters should be split further before Codex analysis. A chunk card should include:

- chunk id
- source chapter
- source line or character range when available
- summary
- mentioned characters, places, items, organizations, terms
- possible facts with `source`, `status`, and `confidence`

## v0.4 Import Closure

Use `import-status` at any point to summarize chunk, batch, chapter-card, volume-summary, bible-patch, and conflict status:

```bash
python scripts/novel_project.py import-status --project-root ./projects/my-novel
```

After chunk cards are done, close the import in deterministic prompt batches:

```bash
python scripts/novel_project.py create-chapter-card-batch --project-root ./projects/my-novel --batch-size 5 --force
python scripts/novel_project.py create-volume-summary-batch --project-root ./projects/my-novel --volume 1 --force
python scripts/novel_project.py create-bible-patch-batch --project-root ./projects/my-novel --source all --force
```

These scripts create prompts and metadata only. They do not perform AI extraction, do not read `raw_text/full_text.txt`, and do not directly edit `canon/`. Story-bible updates are staged as pending patch skeletons under `pending_updates/`.

## Source Tracking

Facts extracted from text must keep source references such as `chapter_001`, `chapter_001_chunk_002`, or a user-provided statement. Do not label interpretation as confirmed unless the source directly supports it.

## Import Report

The import process should leave:

- `imports/import_manifest.yaml`: split results and warnings.
- `imports/import_report.md`: Codex-written summary of completed import work.
- `imports/conflicts_found.md`: possible conflicts discovered during extraction.

## Indexes

After chunk cards and chapter cards exist, rebuild lightweight navigation indexes:

```bash
python scripts/novel_project.py build-indexes --project-root ./projects/my-novel --source all --force
```

Indexes help context retrieval, but they are not source of truth. Canon files, extracted cards, and explicit user statements remain the source-backed facts.

## What Scripts Do Not Do

Scripts do not infer characters, style, motives, themes, or world rules. Codex/model analysis performs that work in batches using chunk cards and source text excerpts.

Use `extraction_prompts.md` when generating chunk cards, chapter cards, volume summaries, story bible patches, plot nodes, and indexes.
