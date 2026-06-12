# Codex Usage

This skill is invoked when the user asks for Chinese novel project creation, import, continuation, rewrite, outline, review, or story bible work.

## Create a Project

```bash
python .agents/skills/chinese-novel-writing/scripts/init_project.py --name my-novel --output ./projects/my-novel
```

Then ask Codex to fill the initial concept, canon, and outline. Generated assumptions should be marked `inferred` until confirmed.

## Import a Novel

```bash
python .agents/skills/chinese-novel-writing/scripts/split_chapters.py --input ./novel.txt --output ./projects/my-novel/raw_text/chapters
```

Codex should then process chapters/chunks in batches and create summaries, cards, bible facts, and indexes. Do not ask Codex to load the entire novel at once.

Split chapters into chunks:

```bash
python .agents/skills/chinese-novel-writing/scripts/split_chunks.py --project ./projects/my-novel --chunk-size 6000 --overlap 500 --force --clean
```

Initialize import progress and create the next batch:

```bash
python .agents/skills/chinese-novel-writing/scripts/init_extraction_progress.py --project ./projects/my-novel --force
python .agents/skills/chinese-novel-writing/scripts/create_extraction_batch.py --project ./projects/my-novel --stage chunk_cards --batch-size 5 --force
```

Then use `references/extraction_prompts.md` to process only the chunks listed in `imports/batches/batch_0001_chunk_cards.md`. After creating the chunk cards, update progress:

```bash
python .agents/skills/chinese-novel-writing/scripts/mark_extraction_done.py --project ./projects/my-novel --batch-id batch_0001 --status done
```

Rebuild indexes after extracted cards or canon files change:

```bash
python .agents/skills/chinese-novel-writing/scripts/build_indexes.py --project ./projects/my-novel --source all --force
```

## Continue a Story

```bash
python .agents/skills/chinese-novel-writing/scripts/build_context_pack.py --project ./projects/my-novel --branch main --task continue_story --chapter 12
```

Codex fills missing context from summaries and relevant bible entries, writes the draft, runs the quality gate, then creates a patch.

Create a chapter function card before drafting when the goal is known or inferred:

```bash
python .agents/skills/chinese-novel-writing/scripts/create_chapter_function_card.py --project ./projects/my-novel --branch main --chapter 12 --goal "主角进入剑冢，发现父亲线索"
```

## Create an Alternate Plot Branch

```bash
python .agents/skills/chinese-novel-writing/scripts/create_branch.py --project ./projects/my-novel --branch villain-ally --title "反派成为盟友线" --divergence "主角和原反派在开篇成为朋友"
```

Codex should keep the branch isolated and write branch-local outline, timeline, foreshadowing, and causal impact notes.

## Create a Post-Write Patch

```bash
python .agents/skills/chinese-novel-writing/scripts/create_patch.py --project ./projects/my-novel --branch main --chapter 12
```

Review the patch before applying any bible updates.

Dry-run a safe apply plan:

```bash
python .agents/skills/chinese-novel-writing/scripts/apply_patch.py --project ./projects/my-novel --patch ./projects/my-novel/pending_updates/chapter_012_patch.yaml
```

Apply only after review:

```bash
python .agents/skills/chinese-novel-writing/scripts/apply_patch.py --project ./projects/my-novel --patch ./projects/my-novel/pending_updates/chapter_012_patch.yaml --confirm
```

## Validate a Project

```bash
python .agents/skills/chinese-novel-writing/scripts/validate_project.py --project ./projects/my-novel
```

Use validation output to find missing directories, missing files, or obviously malformed YAML.

## Wrapper Commands

`scripts/novel_project.py` exposes the same helpers as subcommands:

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py init --name my-novel --output ./projects/my-novel
python .agents/skills/chinese-novel-writing/scripts/novel_project.py split-chunks --project ./projects/my-novel --force --clean
python .agents/skills/chinese-novel-writing/scripts/novel_project.py init-progress --project ./projects/my-novel --force
python .agents/skills/chinese-novel-writing/scripts/novel_project.py create-batch --project ./projects/my-novel --stage chunk_cards --batch-size 5 --force
python .agents/skills/chinese-novel-writing/scripts/novel_project.py build-indexes --project ./projects/my-novel --source all --force
python .agents/skills/chinese-novel-writing/scripts/novel_project.py apply-patch --project ./projects/my-novel --patch ./projects/my-novel/pending_updates/chapter_012_patch.yaml
```

## Later Calls

For future tasks, tell Codex the project root and the desired branch. Codex should load only the relevant reference document and current context pack, then act through the workflow.
