# chinese-novel-writing

`chinese-novel-writing` 是一个中文小说项目工作流 skill，用于从零创作、导入续写、资料库维护、context pack 构建、剧情分支改写和一致性检查。v0.4 保留当前实际路径：

```text
.agents/skills/chinese-novel-writing/
```

`DEVELOPMENT_REQUIREMENTS.md` 是原始需求基准；当前实现不重建 `chinese-novel-studio`，也不移动到 `assets/templates/`。项目模板源是：

```text
.agents/skills/chinese-novel-writing/templates/novel_project/
```

## v0.4 Additions

v0.4 keeps the existing v0.3.1 happy path and adds import-closure and quality workflow commands:

- `import-status`: writes `imports/import_status.md` with chunk, batch, card, summary, patch, conflict, and next-action status.
- `create-chapter-card-batch`: creates `batch_XXXX_chapter_cards.md/.yaml` from chapters whose chunks are done or ready.
- `create-volume-summary-batch`: creates `batch_XXXX_volume_summaries.md/.yaml` from reviewed chapter cards.
- `create-bible-patch-batch`: creates `batch_XXXX_story_bible_patches.md/.yaml` plus `pending_updates/import_bible_patch_XXXX.yaml` skeletons; it never edits canon directly.
- `build-context-pack --auto-select`: fills selectors from indexes using the current chapter function card, recent summaries, and matching chapter cards as hints.
- `create-quality-report`: writes `branches/<branch>/reviews/chapter_XXX_quality_report.md`.

Manual selectors still win over auto-selected selectors. Empty auto-selection is allowed and records `missing_sections` instead of failing.

## v0.4.1 Bugfix Notes

v0.4.1 is a small bugfix release. It keeps `schema_version: "0.4"` and does not add a new schema version.

- `mark-done` is now stage-aware. It preserves existing `chunk_cards` behavior, updates chapter progress for `chapter_cards`, and only updates batch metadata for `volume_summaries` and `story_bible_patches`.
- `create-quality-report` resolves `--draft`, `--context-pack`, and `--output` relative to `--project-root` when those paths are not absolute.
- `validate` may print `Suggestions`. Suggestions are workflow guidance, not failure. Hard validation failure is determined by `Errors`; `Errors: none` is the structural acceptance signal.

Project-relative quality report paths:

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py create-quality-report --project-root ./tmp/demo_novel --branch main --chapter 1 --draft branches/main/drafts/chapter_001.md --context-pack context_packs/latest_context_pack.md --force
```

Minimal v0.4 verification after the old happy path:

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py import-status --project-root ./tmp/demo_novel
python .agents/skills/chinese-novel-writing/scripts/novel_project.py create-chapter-card-batch --project-root ./tmp/demo_novel --batch-size 2 --force
python .agents/skills/chinese-novel-writing/scripts/novel_project.py build-context-pack --project-root ./tmp/demo_novel --branch main --task continue_story --chapter 1 --auto-select --force
python .agents/skills/chinese-novel-writing/scripts/novel_project.py create-quality-report --project-root ./tmp/demo_novel --branch main --chapter 1 --template-only --force
python .agents/skills/chinese-novel-writing/scripts/novel_project.py validate --project-root ./tmp/demo_novel
```

## 它不是什么

- 不是完整写作 App，也不提供 Web UI。
- 不接数据库、向量库、外部 API 或外部 LLM 服务。
- 不内置成人内容安全检查器。
- 不承诺“完美处理 200 万字小说”；它提供长文本分层导入和任务级 context pack 架构。
- 不会在写作后直接覆盖 `canon/`、`timeline.yaml`、`foreshadowing.yaml` 等核心资料库。

## v0.4 推荐工作流

1. `init` 创建项目。
2. `split-import` 切章节、切 chunk、初始化 progress、创建第一批 batch。
3. 让 Codex 只读取 batch 内 chunk，生成 chunk cards。
4. `mark-done` 标记 batch 或 chunk 状态。
5. `build-indexes` 构建导航索引。indexes 不是事实来源。
6. `create-function-card` 写章节功能卡。
7. `build-context-pack` 生成写作/续写/改写/审稿前的任务输入包。
8. 写正文或大纲后 `create-patch` 生成 pending update。
9. `apply-patch` 默认 dry-run；确认后才可 `--confirm`。
10. `validate` 自检项目结构。

## 快速开始

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py init --project-root ./tmp/demo_novel --name demo --force
```

## 导入已有小说

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py split-import --project-root ./tmp/demo_novel --source .agents/skills/chinese-novel-writing/samples/minimal_chinese_story.txt --chunk-size 1000 --overlap 100 --batch-size 2 --force --clean
```

`split-import` 会按顺序执行：

1. `split_chapters.py`
2. `split_chunks.py`
3. `init_extraction_progress.py`
4. `create_extraction_batch.py`

`--clean` 必须搭配 `--force`。它只清理旧 `*_chunk_*.txt`，不会删除原文或已抽取卡片。

Batch 导入时给 Codex 的指令：

```text
请使用 chinese-novel-writing skill，处理 imports/batches/<batch_id>_chunk_cards.md 中列出的 chunk。
只读取该 batch 文件列出的 chunk 原文，不要读取 raw_text/full_text.txt，也不要一次性读取整本小说。
为每个 chunk 生成 extracted/chunk_cards/<chunk_id>.yaml。
每条重要事实必须包含 source、status、confidence。
不要把推测写成 confirmed；不要直接修改 canon 或 main 分支资料库。
完成后用 novel_project.py mark-done 更新 extraction_progress.yaml。
```

## 续写前准备

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py create-function-card --project-root ./tmp/demo_novel --branch main --chapter 1 --goal "测试章节功能卡" --force
python .agents/skills/chinese-novel-writing/scripts/novel_project.py build-context-pack --project-root ./tmp/demo_novel --branch main --task continue_story --chapter 1 --include-recent 3 --force
```

写作、续写、剧情改写、审稿前都必须先构建 context pack。context pack 只包含当前任务相关内容，不读取 `raw_text/full_text.txt`，也不默认塞入全量 canon。

## 剧情改写分支

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py new-branch --project-root ./tmp/demo_novel --name what_if_villain_ally --title "反派成为盟友线" --divergence "主角一开始和反派成为朋友" --inherit skeleton --force
```

`rewrite_plot`、`what-if`、`假如`、`保留设定但改写` 等请求必须进入 `branches/<branch>/`。branch 的人物状态、timeline、foreshadowing 不写回 `canon/` 或 `branches/main/`，除非用户明确确认并通过 patch。

## 写后 Patch

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py create-patch --project-root ./tmp/demo_novel --branch main --chapter 1 --force
python .agents/skills/chinese-novel-writing/scripts/novel_project.py apply-patch --project-root ./tmp/demo_novel --patch ./tmp/demo_novel/pending_updates/chapter_001_patch.yaml
```

`apply-patch` 默认 dry-run，不写文件。确认写入时使用：

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py apply-patch --project-root ./tmp/demo_novel --patch ./tmp/demo_novel/pending_updates/chapter_001_patch.yaml --confirm
```

如果 `requires_user_confirmation` 非空，必须在用户明确同意后加 `--confirm-major`。人物、关系、世界观、地点、组织、物品、术语等复杂更新在 v0.4 仍是 review-only。

## Validate

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py validate --project-root ./tmp/demo_novel
```

warnings 不代表失败。`schema_version` 缺失会 warning，不会让旧项目直接失败。

`validate` output has three levels:

- `Errors`: structural failures. `Errors: none` is the hard pass condition.
- `Warnings`: review these, but they do not always block work.
- `Suggestions`: next-step workflow guidance; suggestions can exist in a valid project.

## 手动验证 Happy Path

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py --help
python .agents/skills/chinese-novel-writing/scripts/novel_project.py init --project-root ./tmp/demo_novel --name demo --force
python .agents/skills/chinese-novel-writing/scripts/novel_project.py split-import --project-root ./tmp/demo_novel --source .agents/skills/chinese-novel-writing/samples/minimal_chinese_story.txt --chunk-size 1000 --overlap 100 --batch-size 2 --force --clean
python .agents/skills/chinese-novel-writing/scripts/novel_project.py create-function-card --project-root ./tmp/demo_novel --branch main --chapter 1 --goal "测试章节功能卡" --force
python .agents/skills/chinese-novel-writing/scripts/novel_project.py build-context-pack --project-root ./tmp/demo_novel --branch main --task continue_story --chapter 1 --include-recent 3 --force
python .agents/skills/chinese-novel-writing/scripts/novel_project.py create-patch --project-root ./tmp/demo_novel --branch main --chapter 1 --force
python .agents/skills/chinese-novel-writing/scripts/novel_project.py apply-patch --project-root ./tmp/demo_novel --patch ./tmp/demo_novel/pending_updates/chapter_001_patch.yaml
python .agents/skills/chinese-novel-writing/scripts/novel_project.py validate --project-root ./tmp/demo_novel
```

`samples/minimal_chinese_story.txt` 是极短 synthetic sample，只用于验证脚本能跑，不用于评估写作质量。

## 高级脚本

底层脚本仍可直接调用，用于细粒度控制：

- `init_project.py`
- `split_chapters.py`
- `split_chunks.py`
- `init_extraction_progress.py`
- `create_extraction_batch.py`
- `import_status.py`
- `create_chapter_card_batch.py`
- `create_volume_summary_batch.py`
- `create_bible_patch_batch.py`
- `mark_extraction_done.py`
- `build_indexes.py`
- `create_branch.py`
- `create_chapter_function_card.py`
- `build_context_pack.py`
- `create_quality_report.py`
- `create_patch.py`
- `apply_patch.py`
- `validate_project.py`

## Schema 取舍

- v0.4 使用 `schema_version: "0.4"` 标记新模板和新生成文件。
- `output_mode` 是 canonical 字段；旧需求里的 `preferred_output_mode` 不是当前实现主字段。
- 重要事实继续使用 `source` / `status` / `confidence`。
- `foreshadowing.status` 这类字段表示生命周期状态，不等同于事实证据状态。
- `pending_updates/` 是 review queue，不是自动合并区。

## 公开仓库安全提醒

- 不要把真实小说原文、长篇草稿、读者隐私或未公开设定提交到公开仓库。
- `raw_text/`、`chunks/`、`drafts/`、`reviews/`、`context_packs/` 默认不建议公开。
- 提交前检查 `git status` 和 `.gitignore`。
