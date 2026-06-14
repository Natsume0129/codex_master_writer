# Output Modes

Use `output_mode` to control response size and workflow detail. `output_mode` is the canonical field in `project_config.yaml` and context pack metadata. `preferred_output_mode` is an older requirements name and should not be introduced into new project files.

v0.5.1 draft prompts may also include `target_length` and `style_strictness`. These are writing controls for the generated prompt, not replacements for `output_mode`.

## Modes

- `draft_only`: only the requested prose draft.
- `draft_with_notes`: draft plus concise post-write notes. This is the default.
- `concise`: short answer, minimal explanation, useful for file or bible lookups.
- `full`: draft or analysis plus outline notes, quality gate, patch summary, and next suggestions.
- `analysis_only`: analysis without prose drafting.
- `bible_only`: structured bible or project data output only.

## Selection

- User says "只要正文": `draft_only`.
- User asks "详细分析" or "完整流程": `full` or `analysis_only`.
- User asks to inspect project data: `bible_only` or `concise`.
- Otherwise use `draft_with_notes`.

## Draft Prompt Controls

- `target_length`: target character count for drafting, not a hard cutoff.
- `style_strictness: low`: allow some expressive freedom.
- `style_strictness: medium`: follow project style and context pack. This is the default.
- `style_strictness: high`: strictly follow the context pack, chapter function card, and style guide; do not expand unconfirmed content.

## Automation Level

- `low`: ask before most structure changes; generate fewer automatic notes.
- `medium`: default. Build context pack, run quality gate, create patch templates.
- `high`: proactively propose outline cards, patch candidates, and review notes, but still require confirmation for major plot changes.

## Report Size

Avoid giant reports by default. The skill should behave like a project editor: surface the critical checks and leave detailed logs in files when appropriate.
