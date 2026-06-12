# chinese-novel-writing

`chinese-novel-writing` 是一个 Codex Agent Skill，用于中文小说项目化创作、导入、续写、资料库维护、剧情分支改写和一致性检查。

它不是完整写作 App，也不是 Web UI、数据库服务、向量库或外部 LLM/API 客户端。v0.3 提供的是 Skill 指令、reference 工作流、空项目模板和标准库 Python 辅助脚本。

## 公开仓库提醒

- 不要把真实小说原文、长篇草稿、读者隐私或未公开设定提交到公开仓库。
- 如果要同步真实项目，请使用 private repo。
- `raw_text/`、`chunks/`、`drafts/`、`reviews/`、`context_packs/` 默认不建议公开。
- `.gitignore` 已覆盖常见小说项目目录，但提交前仍应检查 `git status`。

## v0.3 标准流程

1. 创建小说项目。
2. 导入 txt 并切章节。
3. 切 chunk，可用 `--clean` 清理旧 chunk。
4. 初始化 `imports/extraction_progress.yaml`。
5. 创建小批量抽取 batch。
6. 让 Codex 只读取 batch 内 chunk，生成 chunk cards。
7. 标记 batch/chunk 完成或失败。
8. 生成 chapter cards、volume summaries、story bible patch。
9. 构建 indexes。indexes 只是导航，不是事实来源。
10. 写章节功能卡。
11. 生成 context pack。续写、改写、审稿前必须先有 context pack。
12. 续写正文。
13. 生成写后 patch。
14. 先 dry-run apply patch，再在确认后应用有限安全更新。
15. validate 项目。

## 创建项目

```bash
python .agents/skills/chinese-novel-writing/scripts/init_project.py --name my-novel --output ./projects/my-novel
```

## 导入并切章节

```bash
python .agents/skills/chinese-novel-writing/scripts/split_chapters.py --input ./novel.txt --output ./projects/my-novel/raw_text/chapters
```

## 切 Chunk

```bash
python .agents/skills/chinese-novel-writing/scripts/split_chunks.py --project ./projects/my-novel --chunk-size 6000 --overlap 500 --force --clean
```

`--clean` 只会删除输出目录里的旧 `*_chunk_*.txt`，并且必须配合 `--force` 使用。它不会删除原文或已抽取卡片。

## 初始化抽取进度

```bash
python .agents/skills/chinese-novel-writing/scripts/init_extraction_progress.py --project ./projects/my-novel --force
```

该命令根据 `imports/chunk_manifest.yaml` 创建 `imports/extraction_progress.yaml`，用于长篇导入的断点续跑。

## 创建抽取 Batch

```bash
python .agents/skills/chinese-novel-writing/scripts/create_extraction_batch.py --project ./projects/my-novel --stage chunk_cards --batch-size 5 --force
```

batch 文件会写入：

```text
imports/batches/batch_0001_chunk_cards.md
imports/batches/batch_0001_chunk_cards.yaml
```

### Batch 导入 Prompt

```text
请使用 chinese-novel-writing skill，处理 imports/batches/<batch_id>_chunk_cards.md 中列出的 chunk。
只读取该 batch 文件列出的 chunk 原文，不要读取 raw_text/full_text.txt，也不要一次性读取整本小说。
为每个 chunk 生成 extracted/chunk_cards/<chunk_id>.yaml。
每条重要事实必须包含 source、status、confidence。
不要把推测写成 confirmed；不要直接修改 canon 或 main 分支资料库。
完成后用 scripts/mark_extraction_done.py 更新 extraction_progress.yaml。
```

## 标记抽取完成

```bash
python .agents/skills/chinese-novel-writing/scripts/mark_extraction_done.py --project ./projects/my-novel --batch-id batch_0001 --status done
```

失败时：

```bash
python .agents/skills/chinese-novel-writing/scripts/mark_extraction_done.py --project ./projects/my-novel --batch-id batch_0001 --status failed --error "reason"
```

## 构建 Indexes

```bash
python .agents/skills/chinese-novel-writing/scripts/build_indexes.py --project ./projects/my-novel --source all --force
```

Indexes 用于帮助 context pack 检索人物、地点、物品、组织、事件、伏笔、术语、章节和 chunk。它们不是 source of truth；事实仍以 canon、extracted cards 和用户确认内容为准。

## 写章节功能卡

```bash
python .agents/skills/chinese-novel-writing/scripts/create_chapter_function_card.py --project ./projects/my-novel --branch main --chapter 12 --goal "主角进入剑冢，发现父亲线索" --force
```

输出位置：

```text
branches/main/chapter_function_cards/chapter_012_function_card.yaml
```

## 生成 Context Pack

```bash
python .agents/skills/chinese-novel-writing/scripts/build_context_pack.py --project ./projects/my-novel --branch main --task continue_story --chapter 12 --characters 林照夜 沈青辞 --locations 剑冢 --items 破剑 --foreshadowing-ids foreshadowing_007 --include-recent 3 --previous-ending-chars 1500 --output ./projects/my-novel/context_packs/chapter_012_context.md --force
```

v0.3 会自动读取当前分支的章节功能卡，并把 `chapter_goal` 写入 context pack。实体检索会先看 index，再从 canon 抽完整条目块，最后才退回短行匹配。没有找到的内容会进入 `missing_sections`，不会默认塞入整份资料库。

## 创建剧情改写分支

```bash
python .agents/skills/chinese-novel-writing/scripts/create_branch.py --project ./projects/my-novel --branch villain-ally --title "反派成为盟友线" --divergence "主角和原反派在开篇成为朋友" --inherit skeleton
```

分支改写必须隔离在 `branches/<branch>/` 下，不要污染 `canon/` 或 `branches/main/`。

## 生成写后 Patch

```bash
python .agents/skills/chinese-novel-writing/scripts/create_patch.py --project ./projects/my-novel --branch main --chapter 12 --force
```

patch 写入 `pending_updates/`。不要在续写后直接覆盖人物、时间线、世界观、物品、伏笔等核心资料。

## Dry-run / Apply Patch

默认只 dry-run：

```bash
python .agents/skills/chinese-novel-writing/scripts/apply_patch.py --project ./projects/my-novel --patch ./projects/my-novel/pending_updates/chapter_012_patch.yaml
```

确认后应用有限安全字段：

```bash
python .agents/skills/chinese-novel-writing/scripts/apply_patch.py --project ./projects/my-novel --patch ./projects/my-novel/pending_updates/chapter_012_patch.yaml --confirm
```

如果 patch 的 `requires_user_confirmation` 非空，还必须在用户明确同意后加 `--confirm-major`。v0.3 只自动追加 timeline、foreshadowing_added、open_questions_added、continuity_issues；人物、关系、世界观、地点、组织、物品、术语更新需要人工审阅。

## Validate

```bash
python .agents/skills/chinese-novel-writing/scripts/validate_project.py --project ./projects/my-novel
```

也可以使用 wrapper：

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py validate --project ./projects/my-novel
```

## 最小手动验证

```bash
python .agents/skills/chinese-novel-writing/scripts/init_project.py --name demo --output ./tmp/demo_novel --force
python .agents/skills/chinese-novel-writing/scripts/split_chapters.py --input .agents/skills/chinese-novel-writing/samples/minimal_chinese_story.txt --output ./tmp/demo_novel/raw_text/chapters --force
python .agents/skills/chinese-novel-writing/scripts/split_chunks.py --project ./tmp/demo_novel --chunk-size 1000 --overlap 100 --force --clean
python .agents/skills/chinese-novel-writing/scripts/init_extraction_progress.py --project ./tmp/demo_novel --force
python .agents/skills/chinese-novel-writing/scripts/create_extraction_batch.py --project ./tmp/demo_novel --stage chunk_cards --batch-size 2 --force
python .agents/skills/chinese-novel-writing/scripts/create_chapter_function_card.py --project ./tmp/demo_novel --branch main --chapter 1 --goal "测试章节功能卡" --force
python .agents/skills/chinese-novel-writing/scripts/build_context_pack.py --project ./tmp/demo_novel --branch main --task continue_story --chapter 1 --include-recent 3 --force
python .agents/skills/chinese-novel-writing/scripts/create_patch.py --project ./tmp/demo_novel --branch main --chapter 1 --force
python .agents/skills/chinese-novel-writing/scripts/apply_patch.py --project ./tmp/demo_novel --patch ./tmp/demo_novel/pending_updates/chapter_001_patch.yaml
python .agents/skills/chinese-novel-writing/scripts/validate_project.py --project ./tmp/demo_novel
```

`samples/minimal_chinese_story.txt` 是极短 synthetic sample，只用于验证脚本能跑，不用于评估写作质量。

## v0.3 支持

- 可断点续跑的 extraction progress。
- batch 文件生成和状态标记。
- chunk/chapter/entity indexes 构建。
- context pack 自动载入当前分支章节功能卡。
- context pack 的索引优先实体检索和 `retrieval_notes`。
- guarded patch apply：dry-run 默认、备份、changelog、有限自动合并。
- 更完整的 validate。

## 仍不支持

- 自动语义检索、向量库或数据库服务。
- 外部 API、联网读取或远程同步。
- 自动人物抽取、文风建模和剧情推理脚本。
- 复杂资料库 patch 的无人工合并。
- 自动 rollback。
- 内置成人内容安全检查器。
