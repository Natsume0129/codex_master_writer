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
