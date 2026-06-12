# Codex Usage

Use this skill when the user asks for Chinese novel project creation, long-form import, continuation, rewrite, outline, review, or story bible work.

## Primary CLI

Prefer the unified CLI:

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py <subcommand> ...
```

Use lower-level scripts only when a task needs fine-grained control or direct compatibility with an existing workflow.

Supported v0.3.1 subcommands:

- `init`
- `split-import`
- `init-progress`
- `create-batch`
- `mark-done`
- `build-indexes`
- `new-branch`
- `create-function-card`
- `build-context-pack`
- `create-patch`
- `apply-patch`
- `validate`

## Create A Project

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py init --project-root ./projects/my-novel --name my-novel
```

Generated assumptions should be marked `inferred` until the user confirms them.

## Import A Novel

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py split-import --project-root ./projects/my-novel --source ./novel.txt --chunk-size 6000 --overlap 500 --batch-size 5 --force --clean
```

`split-import` performs deterministic file work only: chapter splitting, chunk splitting, progress initialization, and first batch creation. It does not ask the model to analyze the full text.

When processing a batch:

- Read only the chunk files listed in `imports/batches/<batch_id>_chunk_cards.md`.
- Do not read `raw_text/full_text.txt`.
- Do not load the whole novel into context.
- Create `extracted/chunk_cards/<chunk_id>.yaml`.
- Every important fact must carry `source`, `status`, and `confidence`.
- Do not write inferred content as `confirmed`.
- Do not directly modify canon; generate patch candidates.

After chunk cards are created:

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py mark-done --project-root ./projects/my-novel --batch-id batch_0001 --status done
```

Rebuild indexes after extracted cards or canon files change:

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py build-indexes --project-root ./projects/my-novel --source all --force
```

Indexes are navigation aids, not source of truth.

## Continue Or Draft

Create or update a chapter function card when the chapter goal is known:

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py create-function-card --project-root ./projects/my-novel --branch main --chapter 12 --goal "主角进入剑冢，发现父亲线索" --force
```

Build a context pack before drafting, continuation, rewrite, or review:

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py build-context-pack --project-root ./projects/my-novel --branch main --task continue_story --chapter 12 --include-recent 3 --force
```

The context pack must stay task-specific. It must not include full raw text or unrelated full canon files.

## Rewrite Plot

Create an isolated branch for what-if or divergence requests:

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py new-branch --project-root ./projects/my-novel --name villain-ally --title "反派成为盟友线" --divergence "主角和原反派在开篇成为朋友" --inherit skeleton
```

Keep branch state local. Do not write branch timeline, character state, or foreshadowing back into `canon/` or `branches/main/`.

## Post-Write Patch

Create a pending patch after drafting or major outline changes:

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py create-patch --project-root ./projects/my-novel --branch main --chapter 12
```

Dry-run before applying:

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py apply-patch --project-root ./projects/my-novel --patch ./projects/my-novel/pending_updates/chapter_012_patch.yaml
```

Only apply after review:

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py apply-patch --project-root ./projects/my-novel --patch ./projects/my-novel/pending_updates/chapter_012_patch.yaml --confirm
```

Do not automatically confirm major plot changes. If `requires_user_confirmation` is non-empty, use `--confirm-major` only after explicit user approval.

## Validate

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py validate --project-root ./projects/my-novel
```

Validation errors should stop the workflow. Warnings, including missing `schema_version` in older projects, should be reviewed but do not necessarily block work.
