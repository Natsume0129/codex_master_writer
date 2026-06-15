# Retrieval Index

v0.7 adds a deterministic retrieval index for long-form projects. The index is a navigation aid, not a fact source.

## Position

Source of truth remains:

- user input
- raw imported source files
- extracted chunk cards
- chapter cards
- volume summaries
- canon bible files
- branch-local artifacts
- pending patches

The retrieval index may reference `source_file`, `source`, `status`, and `confidence`. It must not promote `inferred` facts to `confirmed`, and it must not override canon, extracted cards, branch artifacts, or pending patches.

## Allowed Sources

The builder may index structured artifacts:

- `extracted/chunk_cards/*.yaml`
- `extracted/chapter_cards/*.yaml`
- `extracted/volume_summaries/*.md`
- `canon/*.yaml`
- `canon/*.md`
- `bible/*.yaml`
- `bible/*.md`
- `indexes/*.yaml`
- `indexes/*.md`
- `branches/<branch>/branch_config.yaml`
- `branches/<branch>/divergence_point.yaml`
- `branches/<branch>/rewrite/*.yaml`
- `branches/<branch>/summaries/*.md`
- `branches/<branch>/chapter_summaries/*.md`
- `branches/<branch>/reviews/*.md`
- `pending_updates/*.yaml`

Forbidden content bodies:

- `raw_text/full_text.txt`
- full content of `raw_text/*.txt`
- full content of `imports/source_texts/*.txt`
- large prose excerpts

If raw text presence matters, scripts may check file existence and size only. They must not read raw full-text content.

## Retrieval Rules

Deterministic retrieval may use:

- exact keyword match
- lowercase normalized substring match
- chapter id match
- entity match
- branch match
- source type weighting
- recency or `updated_at` if present
- status and confidence weighting
- user-provided selectors

Do not use embeddings, AI semantic search, external APIs, NLP libraries, or tokenizers.

## Context Pack Audit

Audit context packs for:

- budget overflow
- possible raw full text inclusion by size heuristic
- `raw_text/full_text.txt` path references
- unrelated branch references
- missing `source` / `status` / `confidence`
- missing task, branch, or chapter metadata
- deprecated facts
- missing expected sections
- missing Retrieval Trace
- oversized sections
- treating retrieval index as source of truth

Audit reports are heuristic. They do not judge prose quality and should not block old projects by default.

## Acceptance Harness

`acceptance-check` verifies CLI compatibility and deterministic file creation. It does not validate novel quality, AI output quality, or semantic correctness.

It checks:

- script compilation
- unified CLI help
- demo project initialization
- v0.5 writing-quality flow
- v0.6 rewrite flow
- v0.7 retrieval and audit flow
- validate exit status
- expected files created
- raw full-text marker not copied into context pack
- no rewrite flow pollution of `canon/` or `branches/main/`

The harness uses only synthetic placeholder text and local subprocess calls.
