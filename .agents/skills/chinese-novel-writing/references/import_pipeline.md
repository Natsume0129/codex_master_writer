# Import Pipeline

The import pipeline stores source text, splits it, and creates layered summaries. It is designed for long-form fiction where the full source cannot be placed into one prompt.

## Flow

```text
raw_text/full_text.txt
  -> raw_text/chapters/chapter_0001.txt
  -> chunks/chapter_0001_chunk_0001.txt
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
python scripts/split_chunks.py --project ./projects/my-novel --chunk-size 6000 --overlap 500
```

`split_chunks.py` writes `imports/chunk_manifest.yaml`. Each chunk records `chunk_id`, `chapter_id`, `source_file`, `output_file`, `start_char`, `end_char`, `char_count`, `overlap_prev`, and `overlap_next`.

Long chapters should be split further before Codex analysis. A chunk card should include:

- chunk id
- source chapter
- source line or character range when available
- summary
- mentioned characters, places, items, organizations, terms
- possible facts with `source`, `status`, and `confidence`

## Source Tracking

Facts extracted from text must keep source references such as `chapter_001`, `chapter_001_chunk_002`, or a user-provided statement. Do not label interpretation as confirmed unless the source directly supports it.

## Import Report

The import process should leave:

- `imports/import_manifest.yaml`: split results and warnings.
- `imports/import_report.md`: Codex-written summary of completed import work.
- `imports/conflicts_found.md`: possible conflicts discovered during extraction.

## What Scripts Do Not Do

Scripts do not infer characters, style, motives, themes, or world rules. Codex/model analysis performs that work in batches using chunk cards and source text excerpts.

Use `extraction_prompts.md` when generating chunk cards, chapter cards, volume summaries, story bible patches, plot nodes, and indexes.
