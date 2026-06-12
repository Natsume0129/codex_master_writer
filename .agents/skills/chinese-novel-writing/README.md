# chinese-novel-writing

`chinese-novel-writing` 是一个 Codex Agent Skill，用于中文小说项目化创作、续写、导入、资料库维护、剧情重构和一致性检查。

它不是完整写作 App，也不是 Web UI、数据库服务或外部 LLM 接口。v0.1 提供的是：Skill 指令、reference 工作流、空项目模板和标准库 Python 辅助脚本。真实写作由 Codex 根据 `SKILL.md` 与 `references/` 执行。

## 适用场景

- 从零创建中文小说项目。
- 导入已有中文小说并切分章节。
- 续写已有小说。
- 整理人物、关系、世界观、物品、名词、时间线、伏笔和文风。
- 基于已有设定创建剧情改写分支。
- 生成 context pack、写后 patch 和一致性检查报告。

## 不适用场景

- 与小说项目无关的短文本润色。
- 非小说写作任务。
- 完整 App、后端、数据库、向量库或联网服务开发。
- 一次性把整部长篇小说塞进 prompt。
- 内置成人内容安全检查器或内容审查模块。

## 目录

```text
.agents/skills/chinese-novel-writing/
  SKILL.md
  README.md
  references/
  scripts/
  templates/novel_project/
```

## 创建小说项目

```bash
python .agents/skills/chinese-novel-writing/scripts/init_project.py --name my-novel --output ./projects/my-novel
```

这会复制 `templates/novel_project/`，写入 `project_config.yaml` 的项目名，并创建必要目录。

## 导入已有小说

```bash
python .agents/skills/chinese-novel-writing/scripts/split_chapters.py --input ./novel.txt --output ./projects/my-novel/raw_text/chapters
```

脚本会保留原文，按常见中文章节标题粗切章节，并生成 `imports/import_manifest.yaml`。后续人物提取、文风分析、章节卡和资料库维护由 Codex 按批处理完成，不要一次性读取全文。

## 续写小说

续写前先生成 context pack：

```bash
python .agents/skills/chinese-novel-writing/scripts/build_context_pack.py --project ./projects/my-novel --branch main --task continue_story --chapter 12
```

然后让 Codex 按 `references/workflows.md` 和 `references/context_pack.md` 执行续写。默认输出为正文加简短写后说明。

## 创建剧情改写分支

```bash
python .agents/skills/chinese-novel-writing/scripts/create_branch.py --project ./projects/my-novel --branch villain-ally --title "反派成为盟友线" --divergence "主角和原反派在开篇成为朋友"
```

改写剧情必须写入独立分支，不得污染 `canon/` 或 `branches/main/`。

## 生成写后 Patch

```bash
python .agents/skills/chinese-novel-writing/scripts/create_patch.py --project ./projects/my-novel --branch main --chapter 12
```

patch 写入 `pending_updates/`。它记录新增事实、人物状态变化、关系变化、物品状态、时间线推进、伏笔变化和潜在矛盾。不要默认直接覆盖资料库。

## 查看 Pending Updates

查看 `pending_updates/*.yaml`。重大剧情变化必须进入 `requires_user_confirmation`，由用户确认后才能合并。

## 运行 Validate

```bash
python .agents/skills/chinese-novel-writing/scripts/validate_project.py --project ./projects/my-novel
```

也可以使用兼容包装器：

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py validate --project ./projects/my-novel
```

## 最小手动验证

```bash
python .agents/skills/chinese-novel-writing/scripts/init_project.py --name demo --output ./tmp/demo_novel
python .agents/skills/chinese-novel-writing/scripts/split_chapters.py --input .agents/skills/chinese-novel-writing/samples/minimal_chinese_story.txt --output ./tmp/demo_novel/raw_text/chapters --force
python .agents/skills/chinese-novel-writing/scripts/create_branch.py --project ./tmp/demo_novel --branch what-if --title "测试分支" --divergence "一个关键事件提前发生"
python .agents/skills/chinese-novel-writing/scripts/build_context_pack.py --project ./tmp/demo_novel --branch main --task continue_story --chapter 1 --force
python .agents/skills/chinese-novel-writing/scripts/create_patch.py --project ./tmp/demo_novel --branch main --chapter 1
python .agents/skills/chinese-novel-writing/scripts/validate_project.py --project ./tmp/demo_novel
```

`samples/minimal_chinese_story.txt` 是极短 synthetic sample，只用于验证脚本能跑，不用于评估写作质量。

## v0.1 支持

- Skill 触发说明与 P0 硬规则。
- 10 个 reference 文档。
- 空小说项目模板。
- 初始化项目。
- 中文 txt 章节粗切。
- 剧情改写分支创建。
- context pack 骨架生成。
- 写后 patch 模板生成。
- 项目结构 validate。

## v0.1 暂不支持

- 自动语义检索或向量库。
- 自动人物抽取、文风建模和剧情推理脚本。
- 自动合并 patch。
- 自动 rollback。
- 真实长篇小说测试样本。
- 外部 API 或联网功能。

## 后续路线

1. 增强章节识别和 chunk 切分。
2. 增强 index 生成与来源追踪。
3. 补充质量门报告模板和审稿示例。
4. 增加 patch 合并辅助工具，但仍保留用户确认。
5. 在确认需要后再设计语义检索或向量库，作为 P2 能力。
