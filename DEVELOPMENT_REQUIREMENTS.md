# 中文小说创作、续写与剧情重构 Skill 开发需求文档

> 文件用途：把本文件交给 Codex，作为创建 `chinese-novel-studio` skill 的开发需求说明。  
> 当前阶段目标：先制作一个稳定、可维护、可扩展的 Codex Agent Skill，而不是一次性实现完整小说写作应用。  
> 用户会自行测试效果，因此 Codex 不需要准备真实长篇测试小说；但必须提供可运行的项目骨架、工作流说明、数据结构模板、辅助脚本与自检命令。

---

## 0. 给 Codex 的总指令

请在当前 GitHub 仓库中创建一个 Codex Agent Skill，默认路径：

```text
.agents/skills/chinese-novel-studio/
```

该 skill 的定位是：

```text
中文小说创作、续写与剧情重构 skill。
```

它要帮助用户处理三类核心创作情形：

```text
1. 从零开始创作中文小说。
2. 导入并续写已有中文小说。
3. 在复用已有小说人物、世界观、设定的基础上，改变关键剧情前提并重构新的故事发展。
```

本 skill 不只是“生成一段正文”的提示词，而是一个小说项目工作流系统。它必须围绕以下原则设计：

```text
用户少操作，系统多维护。
自动分析，但不随便覆盖。
自动检查，但不默认大改。
长篇小说不能整本进入上下文。
原创、续写、改写共享底层资料库。
改写剧情必须进入独立分支，不能污染主线。
每条重要设定必须有来源、状态和置信度。
每次写作必须先构建 context pack，而不是读取全量资料。
每次写后更新必须生成 patch，不能直接粗暴覆盖资料库。
```

---

## 1. Skill 名称与触发描述

请创建 `SKILL.md`，并使用以下 front matter：

```markdown
---
name: chinese-novel-studio
description: Use this skill for Chinese novel creation, long-form story import, continuation, outline building, style profiling, story bible maintenance, and alternate-plot rewriting. Trigger when the user wants to write, continue, analyze, restructure, or rewrite a Chinese novel project.
---
```

`description` 必须清楚覆盖这些触发词：

```text
Chinese novel
write novel
continue story
import story
story bible
outline
style profiling
alternate plot
rewrite plot
branch
long-form fiction
```

`SKILL.md` 本身不要过长。核心执行规则放在 `SKILL.md`，详细 schema、流程、模板放入 `references/`。这是为了让 skill 可以按需加载，避免初始上下文过大。

---

## 2. 第一版范围

### 2.1 必须支持的用户入口

第一版必须支持 9 个用户入口：

```text
1. create_project      从零创建小说项目
2. import_story        导入已有小说并建立资料库
3. continue_story      根据已有小说继续写
4. rewrite_plot        根据已有设定改写剧情发展
5. build_outline       生成或补全大纲 / 细纲
6. draft_chapter       根据细纲写正文
7. revise_text         润色、改写、增强文本
8. review_story        审稿与一致性检查
9. view_bible          查看或整理小说资料库
```

### 2.2 必须支持的三种创作模式

```text
模式 A：原创模式
- 用户只有一个想法、类型、主角或设定。
- skill 帮用户建立项目档案、世界观、人物、大纲、章节细纲。

模式 B：续写模式
- 用户已有正文，想继续写。
- skill 先导入、分析、整理资料库，再根据 context pack 续写。

模式 C：剧情重构模式
- 用户提供已有小说或已有设定，并指定一个分歧点。
- skill 保留 canon 设定，在独立 branch 中重算人物关系、因果链、主线、大纲和正文。
```

### 2.3 第一版不需要做的事情

不要实现以下内容：

```text
1. 不要内置成人内容安全检查器。
2. 不要制作审查器、过滤器或内容道德判断模块。
3. 不要依赖用户提供真实测试文件。
4. 不要强行接入数据库、向量库或外部服务。
5. 不要把整个 skill 做成复杂应用框架。
6. 不要把所有细节堆进 SKILL.md。
7. 不要把长篇原文放进 skill 包本身。
8. 不要硬编码某一本小说、某一种题材、某个作者风格。
```

注意：不要创建“成人内容安全检查器”作为功能模块。skill 可以支持风格分类、类型策略和写作流程，但不要把成人内容审查作为独立内置功能。

---

## 3. 必须优先保证的 P0 设计目标

第一版必须优先解决以下 5 个问题。

### P0-1：长文本不能进入上下文

硬规则：

```text
绝不能把 200 万字小说整本塞进模型上下文。
```

正确方案：

```text
原文保存到项目文件。
按章节和 chunk 切分。
逐块生成 chunk card。
逐章生成 chapter card。
逐卷生成 volume summary。
全书生成 story bible。
每次任务只加载 context pack。
```

### P0-2：每条设定必须有来源、状态和置信度

任何重要资料都必须记录：

```yaml
value: 设定内容
status: confirmed | inferred | uncertain | user_override | deprecated
source: 来源章节、chunk 或用户输入
confidence: high | medium | low
last_seen: 最后出现位置
notes: 补充说明
```

### P0-3：续写和改写必须使用 context pack

每次写作或改写前，必须先构建 context pack。

context pack 只包含当前任务相关内容，例如：

```text
用户本次要求
当前分支
当前章节目标
上一章结尾原文
最近 3 章摘要
当前卷摘要
相关人物卡
相关地点 / 物品 / 组织
相关伏笔
时间线约束
文风指南
不可违背事项
```

### P0-4：改写剧情必须进入独立 branch

剧情重构不能覆盖 canon，也不能污染 main。

必须支持：

```text
canon/               原作基础设定
branches/main/       默认主线或续写线
branches/<branch>/   每条改写分支
```

每条改写分支必须拥有独立的：

```text
divergence_point.yaml
causal_impact_log.md
outline.md
timeline.yaml
foreshadowing.yaml
continuity_log.md
chapter_summaries/
```

### P0-5：写后更新必须用 patch，不直接覆盖资料库

每次写完正文或大纲后，必须生成候选更新 patch：

```text
pending_updates/chapter_012_patch.yaml
```

patch 内容包括：

```text
新增事实
人物状态变化
人物关系变化
物品归属变化
地点状态变化
组织状态变化
时间线推进
新增伏笔
回收伏笔
潜在矛盾
```

不能直接粗暴覆盖 `characters.yaml`、`world_bible.md`、`timeline.yaml` 等核心文件。

---

## 4. Skill 包目录结构

请创建以下目录结构：

```text
.agents/skills/chinese-novel-studio/
  SKILL.md
  README.md

  references/
    overview.md
    workflows.md
    data_model.md
    context_pack.md
    branch_system.md
    patch_update.md
    quality_gate.md
    output_modes.md
    codex_usage.md

  scripts/
    novel_project.py

  assets/
    templates/
      project_config.yaml
      user_preferences.md
      project_overview.md
      style_guide.md
      genre_strategy.md
      world_bible.md
      characters.yaml
      relationships.yaml
      items.yaml
      terms.yaml
      locations.yaml
      organizations.yaml
      timeline.yaml
      foreshadowing.yaml
      open_questions.md
      hard_constraints.md
      branch_config.yaml
      divergence_point.yaml
      causal_impact_log.md
      chapter_card.yaml
      chunk_card.yaml
      context_pack.md
      post_write_patch.yaml
      quality_report.md
```

### 4.1 `SKILL.md` 职责

`SKILL.md` 需要包含：

```text
1. skill 的适用场景。
2. 三种核心模式：原创、续写、剧情重构。
3. P0 硬规则。
4. 用户意图识别规则。
5. 何时读取 references。
6. 何时运行 scripts。
7. 输出模式规则。
8. 禁止行为。
```

### 4.2 `references/` 职责

`references/` 放详细说明，避免 `SKILL.md` 过长。

每个文件职责：

```text
overview.md
- skill 总体定位、目标、非目标。

workflows.md
- create_project / import_story / continue_story / rewrite_plot / build_outline / draft_chapter / revise_text / review_story / view_bible 的工作流。

data_model.md
- 小说项目资料库 schema。

context_pack.md
- context pack 构建规则、预算规则、优先级。

branch_system.md
- canon/main/branches 的隔离规则。

patch_update.md
- 写后 patch 更新规则。

quality_gate.md
- 一致性检查与质量门规则。

output_modes.md
- draft_only / draft_with_notes / full / analysis_only 等输出模式。

codex_usage.md
- Codex 使用该 skill 的操作说明。
```

### 4.3 `scripts/novel_project.py` 职责

实现一个轻量级 Python CLI，尽量只使用标准库。

必须支持这些子命令：

```text
init
split-import
new-branch
build-context-pack
create-patch
validate
```

示例：

```bash
python scripts/novel_project.py init --project-root ./my_novel
python scripts/novel_project.py split-import --project-root ./my_novel --source ./novel.txt
python scripts/novel_project.py new-branch --project-root ./my_novel --name what_if_villain_ally
python scripts/novel_project.py build-context-pack --project-root ./my_novel --branch main --task continue_story
python scripts/novel_project.py create-patch --project-root ./my_novel --branch main --chapter 12
python scripts/novel_project.py validate --project-root ./my_novel
```

脚本只做确定性工作：

```text
创建项目结构
复制模板
按章节切分文本
生成 import_manifest
生成基础索引占位
创建分支目录
从已有资料组装 context_pack 骨架
生成 patch 模板
检查必要文件是否存在
```

脚本不要尝试完成复杂 AI 分析。人物提取、文风分析、剧情重构等由 skill 指令引导 Codex / 模型完成。

---

## 5. 小说项目目录结构

skill 创建或维护的小说项目应该采用以下结构：

```text
novel_project/
  project_config.yaml
  user_preferences.md
  changelog.md

  raw_text/
    full_text.txt
    chapters/
      chapter_001.txt
      chapter_002.txt

  imports/
    import_manifest.yaml
    import_report.md
    conflicts_found.md

  extracted/
    chunk_cards/
      chapter_001_chunk_001.yaml
    chapter_cards/
      chapter_001.yaml
      chapter_002.yaml
    volume_summaries/
      volume_001.md

  shared/
    style_guide.md
    genre_strategy.md
    terms.yaml
    hard_constraints.md
    open_questions.md

  canon/
    canon_bible.md
    world_bible.md
    characters.yaml
    relationships.yaml
    locations.yaml
    organizations.yaml
    items.yaml
    original_plot_map.md

  branches/
    main/
      branch_config.yaml
      outline.md
      volume_outline.md
      chapter_outlines.md
      timeline.yaml
      foreshadowing.yaml
      continuity_log.md
      chapter_summaries/
      drafts/
      reviews/

    branch_example/
      branch_config.yaml
      divergence_point.yaml
      causal_impact_log.md
      outline.md
      timeline.yaml
      foreshadowing.yaml
      continuity_log.md
      chapter_summaries/
      drafts/
      reviews/

  indexes/
    character_index.yaml
    location_index.yaml
    item_index.yaml
    event_index.yaml
    foreshadowing_index.yaml
    chapter_index.yaml

  context_packs/
    latest_context_pack.md

  pending_updates/
    chapter_001_patch.yaml
```

---

## 6. 核心数据模型要求

### 6.1 `project_config.yaml`

必须包含：

```yaml
project_name: ""
language: "zh-CN"
primary_mode: "original | continuation | rewrite"
current_branch: "main"
current_chapter: null
chapter_length_target: null
preferred_output_mode: "draft_with_notes"
automation_level: "medium"
auto_update_bible: true
auto_generate_scene_outline: true
auto_review_after_draft: true
auto_rewrite_after_review: false
confirm_major_plot_changes: true
created_at: ""
updated_at: ""
```

### 6.2 人物卡 schema

`canon/characters.yaml` 至少支持：

```yaml
characters:
  character_id:
    name: ""
    aliases: []
    role: "protagonist | antagonist | supporting | minor | unknown"
    status:
      value: "alive | dead | missing | unknown"
      fact_status: "confirmed | inferred | uncertain | user_override | deprecated"
      source: []
      confidence: "high | medium | low"
    identity:
      value: ""
      fact_status: "confirmed | inferred | uncertain | user_override | deprecated"
      source: []
      confidence: "high | medium | low"
    goals: []
    fears: []
    secrets: []
    abilities: []
    current_state: ""
    relationships: []
    speech_style: ""
    first_appearance: ""
    last_seen: ""
    notes: ""
```

### 6.3 关系 schema

`canon/relationships.yaml`：

```yaml
relationships:
  - from: ""
    to: ""
    relation_type: "ally | enemy | family | mentor | romantic | superior | subordinate | unknown"
    public_status: ""
    private_status: ""
    knowledge_asymmetry: ""
    stage: ""
    source: []
    confidence: "high | medium | low"
    branch: "canon | main | branch_name"
```

### 6.4 伏笔 schema

`branches/<branch>/foreshadowing.yaml`：

```yaml
foreshadowing:
  - id: "foreshadowing_001"
    content: ""
    first_appeared: ""
    reinforced: []
    status: "open | reinforced | paid_off | abandoned | uncertain"
    likely_payoff_range: ""
    related_entities: []
    possible_payoffs: []
    actual_payoff: ""
    source: []
    confidence: "high | medium | low"
```

### 6.5 时间线 schema

`branches/<branch>/timeline.yaml`：

```yaml
timeline:
  - id: "event_001"
    story_time: ""
    narrative_order: 1
    chapter: ""
    event: ""
    characters: []
    location: ""
    causes: []
    effects: []
    source: []
    confidence: "high | medium | low"
```

### 6.6 分歧点 schema

`branches/<branch>/divergence_point.yaml`：

```yaml
branch_name: ""
divergence_type: "relationship | event | faction | personality | ability | world_rule | timeline | genre"
original_fact: ""
changed_fact: ""
divergence_time: ""
impact_radius: "level_1_local | level_2_relationship | level_3_main_plot | level_4_world_rule"
affected_characters: []
affected_factions: []
affected_plot_nodes: []
must_preserve: []
can_change: []
notes: ""
```

---

## 7. 用户入口工作流

### 7.1 create_project：从零创建小说

触发示例：

```text
我想写一本仙侠网文，主角能听见法宝心声。
从零设计一本都市悬疑小说。
帮我创建一个小说项目。
```

流程：

```text
1. 判断类型、风格、目标读者。
2. 建立 project_config。
3. 建立 project_overview。
4. 生成主角、核心冲突、世界观初稿。
5. 生成主线大纲、第一卷大纲、前 10 章大纲。
6. 生成第一章场景细纲。
7. 初始化 canon 和 branches/main。
8. 输出项目总览，不要输出过长设定堆砌。
```

### 7.2 import_story：导入已有小说

触发示例：

```text
这是我写的前五章，帮我导入。
导入这本小说，整理人物和世界观。
```

流程：

```text
1. 保存原文。
2. 切分章节。
3. 长章节继续切 chunk。
4. 逐 chunk 生成 chunk card。
5. 合并 chapter card。
6. 合并 volume summary。
7. 生成 story bible。
8. 生成人物、关系、物品、地点、组织、名词、时间线、伏笔、文风指南。
9. 生成 import_report。
10. 标记 uncertain / inferred，不要把推测当 confirmed。
```

### 7.3 continue_story：续写已有小说

触发示例：

```text
接着写。
继续写下一章。
根据前文写第十二章。
```

流程：

```text
1. 确认当前 branch。
2. 读取 project_config。
3. 构建 context_pack。
4. 如缺少章节目标，自动生成章节功能卡。
5. 按文风和当前剧情写正文。
6. 自动运行 quality_gate。
7. 生成 post_write_patch。
8. 输出正文和简短写后说明。
```

### 7.4 rewrite_plot：剧情重构

触发示例：

```text
如果主角一开始和反派成为朋友，后面怎么写？
保留人物和世界观，但让师父没有死，而是背叛主角。
根据这本小说改写原有剧情发展。
```

流程：

```text
1. 读取 canon_bible 和 original_plot_map。
2. 识别 divergence_point。
3. 判断 impact_radius。
4. 创建新 branch。
5. 分析连锁影响。
6. 映射原剧情节点：保留 / 删除 / 反转 / 替换。
7. 重算人物关系、阵营、主线冲突。
8. 生成 2-3 条 alternate plot routes。
9. 推荐一条路线。
10. 生成新分卷大纲和前若干章细纲。
11. 运行合理性检查。
```

### 7.5 build_outline：生成大纲 / 细纲

输出层级：

```text
一句话故事
主线大纲
分卷大纲
章节大纲
场景细纲
章节功能卡
```

大纲必须关注：

```text
主线
人物成长线
关系线
反派线
伏笔线
世界观揭示线
情绪线
能力 / 资源成长线
```

### 7.6 draft_chapter：写正文

写正文前必须有：

```text
当前 branch
章节目标
上一章摘要或结尾原文
相关人物状态
相关世界观设定
相关伏笔
文风指南
不可违背事项
```

写正文后必须生成：

```text
quality_report
post_write_patch
下一章建议
```

### 7.7 revise_text：润色 / 改写

支持：

```text
润色
扩写
缩写
改风格
增强冲突
增强人物声音
降低 AI 味
```

规则：

```text
不要默认覆盖原文。
不要擅自改变剧情方向。
修改前先判断用户要求是语言层、场景层还是剧情层。
```

### 7.8 review_story：审稿与一致性检查

检查：

```text
人物 OOC
设定冲突
时间线冲突
角色信息差错误
物品状态错误
分支污染
伏笔遗漏
文风漂移
节奏问题
AI 味问题
```

输出要有优先级：

```text
严重问题
中等问题
轻微问题
建议修改
```

### 7.9 view_bible：查看资料库

支持用户查看：

```text
人物表
世界观
物品表
名词表
时间线
伏笔表
分支列表
当前 context pack
pending updates
```

---

## 8. Context Pack 规则

### 8.1 不允许读取全量资料

续写、改写、审稿时不能把全部资料库塞进上下文。必须构建 context pack。

### 8.2 默认 context pack 结构

```markdown
# Context Pack

## Task
- type:
- user_request:
- output_mode:
- branch:

## Project Snapshot
- project_overview:
- genre_strategy:
- style_guide_summary:

## Current Arc
- current_volume_summary:
- current_outline:
- current_chapter_goal:

## Recent Context
- previous_chapter_summaries:
- previous_chapter_ending_excerpt:

## Relevant Entities
- characters:
- relationships:
- locations:
- organizations:
- items:

## Relevant Plot Threads
- main_plot:
- side_plots:
- antagonist_plan:

## Foreshadowing and Open Questions
- open_foreshadowing:
- payoff_candidates:
- open_questions:

## Timeline Constraints
- current_story_time:
- recent_events:
- forbidden_time_conflicts:

## Hard Constraints
- must_not_change:
- must_not_reveal_yet:
- branch_boundaries:
```

### 8.3 预算优先级

如果上下文过长，按以下优先级保留：

```text
1. 用户本次要求
2. 当前分支与当前章节目标
3. 上一章结尾原文
4. 最近 3 章摘要
5. 当前卷摘要
6. 相关人物 / 地点 / 物品
7. 相关伏笔和未解问题
8. 时间线和硬限制
9. 文风指南摘要
10. 更久远的原文证据片段
```

---

## 9. Branch System 规则

### 9.1 canon/main/branch 区分

```text
canon：原作基础设定，不直接写正文。
main：默认续写线。
branch：每个剧情重构线。
```

### 9.2 改写分支创建规则

用户提出以下请求时，默认创建 branch：

```text
如果……会怎样
假如……没有发生
保留设定，但重写发展
让原反派成为朋友
让某个角色没有死
让主角加入反派阵营
改变世界规则
```

### 9.3 分支不得污染

硬规则：

```text
branch 的人物状态不能写回 canon。
branch 的时间线不能写回 main。
branch 的伏笔不能写回其他 branch。
canon 只记录原作基础事实。
```

---

## 10. Patch-based Update 规则

### 10.1 写后必须生成 patch

每次写作、续写、改写后生成：

```text
pending_updates/<branch>_chapter_<number>_patch.yaml
```

### 10.2 patch 模板

```yaml
patch_id: ""
branch: "main"
chapter: null
created_at: ""
source_draft: ""

updates:
  characters: []
  relationships: []
  worldbuilding: []
  locations: []
  organizations: []
  items: []
  terms: []
  timeline: []
  foreshadowing_added: []
  foreshadowing_paid_off: []
  open_questions_added: []
  hard_constraints_added: []

potential_conflicts: []
requires_user_confirmation: []
notes: ""
```

### 10.3 合并规则

```text
confirmed 可以合并。
inferred 默认保留为 inferred。
uncertain 不得自动提升。
user_override 优先级最高。
deprecated 不能进入 context pack，除非用户要求查看历史。
重大剧情变化需要用户确认。
```

---

## 11. Quality Gate 规则

每次正文生成后自动检查。

### 11.1 检查项

```text
人物一致性
世界观一致性
能力边界
物品状态
时间线
角色信息差
分支边界
伏笔状态
文风一致性
章节功能
节奏问题
AI 味问题
是否擅自改变重大剧情
```

### 11.2 输出格式

默认简短输出：

```markdown
## 写后检查
- 设定一致性：通过 / 有问题
- 人物一致性：通过 / 有问题
- 时间线：通过 / 有问题
- 风格一致性：通过 / 有问题
- 伏笔变化：新增 X 个，回收 X 个
- 需要注意：...
```

如果用户要求详细审稿，再输出完整报告。

---

## 12. 输出模式

必须支持：

```yaml
output_mode:
  draft_only: 只输出正文
  draft_with_notes: 正文 + 简短写后说明
  full: 正文 + 细纲 + 检查 + patch 摘要 + 下一章建议
  analysis_only: 只分析，不写正文
  bible_only: 只输出资料库整理结果
```

默认：

```yaml
preferred_output_mode: draft_with_notes
```

规则：

```text
用户说“只要正文”，就使用 draft_only。
用户说“详细分析”，就使用 full 或 analysis_only。
用户没有指定时，使用 draft_with_notes。
```

---

## 13. 用户控制权规则

skill 不得擅自决定以下重大事项：

```text
主角死亡
核心人物死亡
核心人物背叛
CP 关系确认
核心秘密提前揭示
最终反派身份确认
世界规则大反转
主线目标改变
原主线被改写
分支合并回主线
```

如果生成中需要涉及这些事项，必须：

```text
1. 标记为重大剧情变化。
2. 放入 requires_user_confirmation。
3. 提供 2-3 个方案。
4. 不默认写死。
```

---

## 14. Codex 具体开发任务

请 Codex 按顺序完成以下任务。

### Task 01：创建 skill 骨架

创建：

```text
.agents/skills/chinese-novel-studio/
  SKILL.md
  README.md
  references/
  scripts/
  assets/templates/
```

验收：

```text
目录结构完整。
SKILL.md 有正确 front matter。
README.md 能说明这个 skill 的用途。
```

### Task 02：编写 SKILL.md

`SKILL.md` 必须包含：

```text
适用场景
三种模式
P0 硬规则
用户意图识别
工作流选择
何时加载 references
何时运行 scripts
输出模式
禁止行为
```

验收：

```text
SKILL.md 不要过长。
Codex 读取后能知道如何处理原创、续写、剧情重构。
```

### Task 03：编写 references 文档

创建并填充：

```text
overview.md
workflows.md
data_model.md
context_pack.md
branch_system.md
patch_update.md
quality_gate.md
output_modes.md
codex_usage.md
```

验收：

```text
每个文件职责明确。
内容足够指导 Codex 后续执行小说项目任务。
不要互相矛盾。
```

### Task 04：创建模板文件

在 `assets/templates/` 中创建所有模板。

验收：

```text
模板能被复制到小说项目中。
YAML 文件格式有效。
Markdown 文件有清晰标题和占位说明。
```

### Task 05：实现 `scripts/novel_project.py`

实现子命令：

```text
init
split-import
new-branch
build-context-pack
create-patch
validate
```

要求：

```text
只使用 Python 标准库。
中文路径尽量兼容。
错误信息要清楚。
不要依赖真实测试小说。
不要调用外部 API。
```

验收：

```text
python scripts/novel_project.py --help 可以运行。
init 能创建小说项目结构。
split-import 能按章节粗切文本并生成 import_manifest。
new-branch 能创建分支目录。
build-context-pack 能生成 context_packs/latest_context_pack.md 骨架。
create-patch 能生成 pending_updates patch 模板。
validate 能检查关键文件是否存在。
```

### Task 06：补充 README 使用说明

README 必须包含：

```text
skill 是什么
适用场景
不适用场景
如何让 Codex 使用该 skill
如何初始化小说项目
如何导入文本
如何创建改写分支
如何构建 context pack
如何查看 pending updates
```

### Task 07：加入最小自检

因为用户会自行测试，不需要复杂测试套件。

但必须提供：

```text
validate 命令
README 中的手动验证步骤
```

可选：

```text
创建一个极短的 synthetic sample，不要使用真实小说文本。
```

如果创建 sample，必须很短，只用于验证脚本能跑，不用于评估写作质量。

---

## 15. 验收标准

第一版完成后，应满足以下标准：

```text
1. 仓库中存在 .agents/skills/chinese-novel-studio/。
2. 该目录包含有效 SKILL.md。
3. skill 有清晰 description，便于 Codex 触发。
4. references 文档完整。
5. assets/templates 包含小说项目所需模板。
6. scripts/novel_project.py 可运行。
7. 能创建一个空小说项目。
8. 能切分一个普通中文 txt 小说文件。
9. 能创建 main 以外的改写分支。
10. 能生成 context pack 骨架。
11. 能生成 post-write patch 模板。
12. 能执行 validate 并输出项目缺失项。
13. 文档明确禁止把整本长篇塞进上下文。
14. 文档明确禁止改写分支污染主线。
15. 文档明确要求每条设定带 source/status/confidence。
16. 文档明确要求写后更新使用 patch。
```

---

## 16. 开发优先级

请按以下优先级实现：

```text
P0：skill 骨架 + SKILL.md + references + templates
P0：小说项目目录结构
P0：长文本导入切分脚本
P0：context pack 骨架生成
P0：branch 创建与隔离
P0：patch 模板生成
P0：validate 自检
P1：更细的章节识别规则
P1：更完整的 indexes 生成
P1：质量门报告模板
P1：输出模式说明
P2：语义检索、向量库、复杂事件图谱
```

第一版不要实现 P2。

---

## 17. 禁止行为清单

Codex 不要做以下事情：

```text
1. 不要把整个 skill 做成一个超长 SKILL.md。
2. 不要把真实小说样例写进仓库。
3. 不要默认创建成人内容安全检查器。
4. 不要把剧情重构写进 main 分支。
5. 不要让 branch 覆盖 canon。
6. 不要把 inferred/uncertain 自动写成 confirmed。
7. 不要直接覆盖核心资料库文件。
8. 不要让脚本依赖外部网络或 API。
9. 不要创建复杂依赖管理。
10. 不要把 prompt 写死成只适合仙侠或网文。
11. 不要用英文替代中文写作需求说明。
12. 不要在 README 里声称已经能完美处理 200 万字小说；只能说明架构支持长文本分层导入。
```

---

## 18. 最终目标描述

这个 skill 的最终目标是：

```text
让 Codex / 模型在处理中文小说项目时，不是一次性生成零散文本，而是按照小说项目工作流执行：

1. 建立项目资料库。
2. 分层导入长文本。
3. 维护人物、世界观、物品、名词、时间线、伏笔、文风。
4. 根据当前任务构建 context pack。
5. 支持原创、续写和剧情重构。
6. 改写剧情走独立 branch。
7. 写后生成 patch。
8. 自动做一致性检查。
9. 尊重用户控制权。
```

一句话总结：

```text
这个 skill 应该像中文小说项目的编辑部，而不只是一个续写提示词。
```
