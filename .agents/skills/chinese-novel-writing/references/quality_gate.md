# Quality Gate

Run a quality gate after drafting, continuation, plot rewrite, and substantial outline changes. The check is a writing and continuity review, not a content morality filter.

## Checks

- Character consistency and OOC behavior.
- World-rule consistency.
- Ability/resource boundaries.
- Timeline conflicts.
- Item state and ownership conflicts.
- Character information asymmetry errors.
- Branch boundary pollution.
- Foreshadowing added, reinforced, paid off, abandoned, or forgotten.
- Style drift from project guide.
- Chapter function and pacing.
- AI-like repetition, generic phrasing, or flattened character voice.
- Unapproved major plot decisions.

## Severity

Use:

- `严重问题`: breaks canon, branch boundary, timeline, or user-stated constraints.
- `中等问题`: weakens continuity, character logic, foreshadowing, or pacing.
- `轻微问题`: local style, clarity, or rhythm issue.
- `建议修改`: optional improvement.

## Concise Default Output

```markdown
## 写后检查
- 设定一致性：通过 / 有问题
- 人物一致性：通过 / 有问题
- 时间线：通过 / 有问题
- 分支边界：通过 / 有问题
- 风格一致性：通过 / 有问题
- 伏笔变化：新增 X 个，回收 X 个
- 需要注意：...
```

## Full Review Output

When the user asks for detailed review, include evidence, file/source references, impact, and recommended fix. Do not silently rewrite the story unless revision is requested.

## v0.4 Quality Report File

Use `create-quality-report` when a draft or outline needs a durable review artifact:

```bash
python scripts/novel_project.py create-quality-report --project-root ./projects/my-novel --branch main --chapter 12 --template-only --force
```

Default output:

```text
branches/<branch>/reviews/chapter_XXX_quality_report.md
```

The report includes:

- `schema_version: 0.4`
- summary
- serious, medium, and light issue tables
- suggested fixes
- patch candidates
- `requires_user_confirmation`
- evidence table
- next actions

The script creates a template only. Codex/model review must fill findings with evidence from the draft and context pack. Major plot fixes still require explicit user confirmation before patch application.
