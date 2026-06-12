# chinese-novel-writing

`chinese-novel-writing` 是一个 Codex Agent Skill，用于中文小说项目化创作、导入、续写、资料库维护、剧情重构和一致性检查。

它不是完整写作 App，也不是 Web UI、数据库服务或外部 LLM 接口。v0.2 提供的是：Skill 指令、reference 工作流、空项目模板、批量导入提示词和标准库 Python 辅助脚本。真实写作由 Codex 根据 `SKILL.md` 与 `references/` 执行。

## 公开仓库提醒

- 不要把真实小说原文提交到公开仓库。
- 如果需要同步真实项目，请使用 private repo。
- `raw_text/`、`chunks/`、`drafts/`、`reviews/`、`context_packs/` 默认不建议公开。
- `.gitignore` 已默认忽略常见用户小说项目与原文目录，但提交前仍应检查 `git status`。

## 适用场景

- 从零创建中文小说项目。
- 导入已有中文小说并切分章节和 chunk。
- 分批生成 chunk card、chapter card、volume summary、story bible patch 和 indexes。
- 续写已有小说。
- 整理人物、关系、世界观、物品、名词、时间线、伏笔和文风。
- 基于已有设定创建剧情改写分支。
- 生成 context pack、章节功能卡、写后 patch 和一致性检查报告。

## 不适用场景

- 与小说项目无关的短文本润色。
- 非小说写作任务。
- 完整 App、后端、数据库、向量库或联网服务开发。
- 一次性把整部长篇小说塞进 prompt。
- 内置成人内容安全检查器或内容审查模块。

## v0.2 标准流程

1. 创建项目。
2. 导入 txt 并切章节。
3. 切 chunk。
4. 让 Codex 分批生成 chunk cards。
5. 合并 chapter cards 和 volume summaries。
6. 生成 context pack。
7. 写章节功能卡。
8. 续写正文。
9. 生成写后 patch。
10. validate 项目。

## 创建小说项目

```bash
python .agents/skills/chinese-novel-writing/scripts/init_project.py --name my-novel --output ./projects/my-novel
```

## 导入 txt 并切章节

```bash
python .agents/skills/chinese-novel-writing/scripts/split_chapters.py --input ./novel.txt --output ./projects/my-novel/raw_text/chapters
```

## 切 Chunk

```bash
python .agents/skills/chinese-novel-writing/scripts/split_chunks.py --project ./projects/my-novel --chunk-size 6000 --overlap 500
```

也支持显式输入输出：

```bash
python .agents/skills/chinese-novel-writing/scripts/split_chunks.py --chapter-dir ./projects/my-novel/raw_text/chapters --output ./projects/my-novel/chunks --manifest ./projects/my-novel/imports/chunk_manifest.yaml --chunk-size 6000 --overlap 500
```

## 导入后给 Codex 的 Prompt

```text
请使用 chinese-novel-writing skill，对 ./projects/my-novel/imports/chunk_manifest.yaml 中的 chunk 进行分批导入。
每批处理 5-10 个 chunk：
1. 读取 chunk 原文；
2. 生成 extracted/chunk_cards/*.yaml；
3. 合并对应 chapter_card；
4. 更新 pending_updates；
5. 每条事实必须有 source/status/confidence；
6. 不要一次性读取全文；
7. 不要把推测写成 confirmed。
```

## 生成 Context Pack

```bash
python .agents/skills/chinese-novel-writing/scripts/build_context_pack.py --project ./projects/my-novel --branch main --task continue_story --chapter 12 --characters 林照夜 沈青辞 --locations 剑冢 --items 破剑 --foreshadowing-ids foreshadowing_007 --include-recent 3 --previous-ending-chars 1500 --output ./projects/my-novel/context_packs/chapter_012_context.md --force
```

如果没有选择器或 indexes 不完整，脚本会把缺失项列入 `missing_sections`，而不是默认塞入整个资料库片段。

## 写章节功能卡

```bash
python .agents/skills/chinese-novel-writing/scripts/create_chapter_function_card.py --project ./projects/my-novel --branch main --chapter 12 --goal "主角进入剑冢，发现父亲线索"
```

章节功能卡写入：

```text
branches/main/chapter_function_cards/chapter_012_function_card.yaml
```

## 续写小说

续写前必须已有 context pack，最好也有章节功能卡。然后让 Codex 按 `references/workflows.md`、`references/context_pack.md`、`references/chapter_function_card.md` 执行续写。默认输出为正文加简短写后说明。

## 创建剧情改写分支

默认 skeleton 模式不会复制 main 的具体 timeline、outline、foreshadowing 内容：

```bash
python .agents/skills/chinese-novel-writing/scripts/create_branch.py --project ./projects/my-novel --branch villain-ally --title "反派成为盟友线" --divergence "主角和原反派在开篇成为朋友" --inherit skeleton
```

如果从某一章之后分歧，可以使用当前状态继承并标记剪枝：

```bash
python .agents/skills/chinese-novel-writing/scripts/create_branch.py --project ./projects/my-novel --branch late-betrayal --title "后期背叛线" --divergence "师父在第十二章后背叛主角" --inherit current-state --base-chapter 12
```

## 剧情改写分支 Prompt

```text
请使用 chinese-novel-writing skill，为当前小说创建剧情改写分支：
分歧点是：____。
请先创建 branch，然后分析 impact_radius、invalidated_plot_nodes、preserved_plot_nodes、replacement_plot_nodes，再给出新剧情路线，不要污染 main 或 canon。
```

## 生成写后 Patch

```bash
python .agents/skills/chinese-novel-writing/scripts/create_patch.py --project ./projects/my-novel --branch main --chapter 12
```

patch 写入 `pending_updates/`。它记录新增事实、人物状态变化、关系变化、物品状态、时间线推进、伏笔变化和潜在矛盾。不要默认直接覆盖资料库。

## 运行 Validate

```bash
python .agents/skills/chinese-novel-writing/scripts/validate_project.py --project ./projects/my-novel
```

也可以使用包装器：

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py validate --project ./projects/my-novel
```

## 最小手动验证

```bash
python .agents/skills/chinese-novel-writing/scripts/init_project.py --name demo --output ./tmp/demo_novel --force
python .agents/skills/chinese-novel-writing/scripts/split_chapters.py --input .agents/skills/chinese-novel-writing/samples/minimal_chinese_story.txt --output ./tmp/demo_novel/raw_text/chapters --force
python .agents/skills/chinese-novel-writing/scripts/split_chunks.py --project ./tmp/demo_novel --chunk-size 1000 --overlap 100 --force
python .agents/skills/chinese-novel-writing/scripts/create_chapter_function_card.py --project ./tmp/demo_novel --branch main --chapter 1 --goal "测试章节功能卡" --force
python .agents/skills/chinese-novel-writing/scripts/create_branch.py --project ./tmp/demo_novel --branch what-if --title "测试分支" --divergence "一个关键事件提前发生" --inherit skeleton --force
python .agents/skills/chinese-novel-writing/scripts/build_context_pack.py --project ./tmp/demo_novel --branch main --task continue_story --chapter 1 --include-recent 3 --force
python .agents/skills/chinese-novel-writing/scripts/create_patch.py --project ./tmp/demo_novel --branch main --chapter 1 --force
python .agents/skills/chinese-novel-writing/scripts/validate_project.py --project ./tmp/demo_novel
```

`samples/minimal_chinese_story.txt` 是极短 synthetic sample，只用于验证脚本能跑，不用于评估写作质量。

## v0.2 支持

- 长章节 chunk 切分与 `chunk_manifest.yaml`。
- 批量抽取提示词：chunk card、chapter card、volume summary、story bible patch、index 更新。
- 统一 `source/status/confidence` 事实字段，不再使用旧的事实状态字段。
- 参数化 context pack 构建。
- plot_node 与 divergence_analysis schema。
- skeleton/current-state 两种分支创建模式。
- 章节功能卡。
- 更严格的 validate。

## v0.2 暂不支持

- 自动语义检索或向量库。
- 自动人物抽取、文风建模和剧情推理脚本。
- 自动合并 patch。
- 自动 rollback。
- 外部 API 或联网功能。

## 后续路线

1. 增加 patch 合并辅助工具，但仍保留用户确认。
2. 增强 indexes 生成与来源追踪。
3. 增加 card 批处理进度记录和断点续跑。
4. 增加更细的章节识别规则。
5. 在确认需要后再设计语义检索或向量库，作为 P2 能力。
