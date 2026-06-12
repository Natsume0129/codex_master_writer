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

## Continue a Story

```bash
python .agents/skills/chinese-novel-writing/scripts/build_context_pack.py --project ./projects/my-novel --branch main --task continue_story --chapter 12
```

Codex fills missing context from summaries and relevant bible entries, writes the draft, runs the quality gate, then creates a patch.

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

## Validate a Project

```bash
python .agents/skills/chinese-novel-writing/scripts/validate_project.py --project ./projects/my-novel
```

Use validation output to find missing directories, missing files, or obviously malformed YAML.

## Later Calls

For future tasks, tell Codex the project root and the desired branch. Codex should load only the relevant reference document and current context pack, then act through the workflow.
