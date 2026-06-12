# 小说项目说明

这是 `chinese-novel-writing` skill 创建的空小说项目模板。

## 使用原则

- 原文保存在 `raw_text/`，不要覆盖。
- 续写、改写、审稿前先生成 `context_packs/`。
- 剧情重构必须创建 `branches/<branch>/`，不能污染 `canon/` 或 `branches/main/`。
- 写后更新先进入 `pending_updates/`，确认后再合并到资料库。
- 重要设定必须保留 source、status、confidence。

## 目录

- `canon/`：基础设定与原剧情图。
- `branches/main/`：默认主线。
- `branches/<branch>/`：剧情改写分支。
- `extracted/`：章节卡、chunk 卡、卷摘要。
- `indexes/`：索引占位文件。
- `pending_updates/`：写后 patch。

