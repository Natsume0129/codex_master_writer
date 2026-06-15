#!/usr/bin/env python3
"""Create a deterministic drafting prompt from a context pack and function card."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _novel_utils import (
    chapter_label_candidates,
    normalize_chapter_label,
    now_iso,
    resolve_project_relative,
    safe_relative,
)
from _style_voice_utils import default_scene_outline, default_style_profile, default_voice_sheet


def default_context_pack(project: Path) -> Path:
    return project / "context_packs" / "latest_context_pack.md"


def default_function_card(project: Path, branch: str, chapter: str, chapter_label: str) -> Path:
    cards_dir = project / "branches" / branch / "chapter_function_cards"
    for candidate in chapter_label_candidates(chapter):
        path = cards_dir / f"{candidate}_function_card.yaml"
        if path.exists():
            return path
    return cards_dir / f"{chapter_label}_function_card.yaml"


def default_prompt_output(project: Path, branch: str, chapter_label: str) -> Path:
    return project / "branches" / branch / "draft_prompts" / f"{chapter_label}_draft_prompt.md"


def default_draft_output(project: Path, branch: str, chapter_label: str) -> Path:
    return project / "branches" / branch / "drafts" / f"{chapter_label}.md"


def status(path: Path) -> str:
    return "present" if path.exists() else "missing"


def read_head(path: Path, limit: int = 5000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        return data[:limit].rstrip() + "\n...[truncated]"
    return data.strip()


def anti_ai_rules(level: str) -> str:
    if not level:
        return "- Not requested."
    base = [
        "- Avoid generic emotional summary where concrete action can carry the scene.",
        "- Avoid dialogue that sounds like essay exposition.",
        "- Avoid resolving conflict through narrator explanation before the scene earns it.",
    ]
    if level in {"medium", "high"}:
        base.extend(
            [
                "- Watch repeated softeners such as 'seems', 'as if', 'some kind of', or equivalent filler.",
                "- Keep scene turns embodied in action, choice, and information pressure.",
            ]
        )
    if level == "high":
        base.extend(
            [
                "- Prefer specific gesture, object, interruption, and sensory detail over abstract labeling.",
                "- Make character voices visibly different in diction, restraint, and information boundaries.",
                "- Avoid template ending hooks; tie the hook to a concrete unresolved scene pressure.",
            ]
        )
    return "\n".join(base)


def render_prompt(
    args: argparse.Namespace,
    context_pack: Path,
    function_card: Path,
    style_profile: Path | None,
    voice_sheet: Path | None,
    scene_outline: Path | None,
    revision_plan: Path | None,
    prompt_output: Path,
    draft_output: Path,
) -> str:
    project = args.project.resolve()
    context_rel = safe_relative(context_pack, project)
    card_rel = safe_relative(function_card, project)
    style_rel = safe_relative(style_profile, project) if style_profile else ""
    voice_rel = safe_relative(voice_sheet, project) if voice_sheet else ""
    scene_rel = safe_relative(scene_outline, project) if scene_outline else ""
    revision_rel = safe_relative(revision_plan, project) if revision_plan else ""
    prompt_rel = safe_relative(prompt_output, project)
    draft_rel = safe_relative(draft_output, project)
    task_label = "Revise the chapter draft" if args.revision_mode else "Draft the chapter"
    revision_note = (
        f"Read `{revision_rel}` and revise according to its Revision Prompt. Do not create a new-branch draft unless instructed."
        if args.revision_mode and revision_plan
        else "Not in revision mode."
    )
    return f"""# Chapter Draft Prompt

schema_version: 0.8
generated_at: {now_iso()}
branch: {args.branch}
chapter: {args.chapter}
chapter_label: {args.chapter_label}
output_mode: {args.output_mode}
target_length: {args.target_length}
style_strictness: {args.style_strictness}
anti_ai_flavor_level: {args.anti_ai_flavor_level}
revision_mode: {str(args.revision_mode).lower()}
context_pack: {context_rel}
context_pack_status: {status(context_pack)}
chapter_function_card: {card_rel}
chapter_function_card_status: {status(function_card)}
style_profile: {style_rel}
style_profile_status: {status(style_profile) if style_profile else "not_requested"}
character_voice_sheet: {voice_rel}
character_voice_sheet_status: {status(voice_sheet) if voice_sheet else "not_requested"}
scene_outline: {scene_rel}
scene_outline_status: {status(scene_outline) if scene_outline else "not_requested"}
revision_plan: {revision_rel}
revision_plan_status: {status(revision_plan) if revision_plan else "not_requested"}
prompt_output: {prompt_rel}
suggested_draft_output: {draft_rel}

## Task

{task_label} for the active branch using only the task-relevant context pack, chapter function card, and requested v0.8 writing-control artifacts.

## Required Reading

1. Read `{context_rel}` first.
2. Read `{card_rel}` second.
3. Read requested style, voice, scene, or revision artifacts listed above when their status is present.
4. Do not read `raw_text/full_text.txt`.
5. Do not load unrelated full canon files unless the context pack explicitly points to a narrow source that is needed.

## v0.8 Writing Control Artifacts

### Style Profile

```yaml
{read_head(style_profile, 5000) if style_profile else ""}
```

### Character Voice Sheet

```yaml
{read_head(voice_sheet, 5000) if voice_sheet else ""}
```

### Scene Outline

```yaml
{read_head(scene_outline, 6000) if scene_outline else ""}
```

### Revision Plan

```markdown
{read_head(revision_plan, 6000) if revision_plan else ""}
```

## Writing Controls

- Treat `chapter_goal` as the local chapter objective.
- Treat `target_length` as a target character count, not a hard cutoff.
- Interpret `style_strictness` as: `low` allows some expressive freedom; `medium` follows the project style and context pack; `high` strictly follows the context pack, function card, and style guide without expanding unconfirmed content.
- Use `chapter_function.type`, `purpose`, and `reader_promise` to decide why the chapter exists.
- Follow `scene_beats` as the chapter's beat-level control surface.
- Preserve `main_conflict`, `emotional_arc`, `continuity_constraints`, `hard_constraints`, and `forbidden`.
- Include only the reveals listed in `new_information`, `worldbuilding_to_reveal`, and foreshadowing fields unless the user asks for more.
- Do not automatically decide any item listed under `requires_user_confirmation`.
- If a major irreversible plot change appears necessary, stop and list the decision instead of writing it as settled fact.
- Treat style profile and character voice sheet as writing controls, not fact sources.
- If style or voice artifacts conflict with canon, outline, context pack, or chapter function card, follow canon/outline/context and record the conflict.
- Follow scene outline order and scene function when provided; if it is incomplete, fill gaps conservatively without inventing major plot changes.

## Anti-AI Flavor Controls

{anti_ai_rules(args.anti_ai_flavor_level)}

## Revision Mode

{revision_note}

## Output Contract

- Write the draft to `{draft_rel}` only if the user has asked you to write files; otherwise return the draft in chat.
- Keep generated prose separate from imported source text.
- Do not edit `canon/`, `branches/<branch>/timeline.yaml`, or `branches/<branch>/foreshadowing.yaml` directly after drafting.
- After drafting, run or request a quality report prompt with `create-quality-report --with-prompt`.
- Stage any story-bible changes through `create-patch`; review them before `apply-patch`.

## Review Checklist After Drafting

- Chapter function achieved.
- Scene beats have conflict and outcomes.
- Character and relationship changes match the card.
- New information is sourced or clearly marked as inferred.
- Foreshadowing added or paid off is recorded as patch candidates.
- Ending hook is present without violating forbidden changes.
- No unconfirmed major plot decision has been silently committed.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a deterministic chapter drafting prompt.")
    parser.add_argument("--project", "--project-root", dest="project", required=True, type=Path)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--chapter", required=True)
    parser.add_argument("--context-pack", type=Path)
    parser.add_argument("--function-card", type=Path)
    parser.add_argument("--output", type=Path, help="Prompt output path.")
    parser.add_argument("--draft-output", type=Path, help="Suggested draft output path written into the prompt.")
    parser.add_argument("--output-mode", default="draft_with_notes")
    parser.add_argument("--target-length", default="", help="Target character count written into the prompt.")
    parser.add_argument("--style-profile", type=Path)
    parser.add_argument("--voice-sheet", type=Path)
    parser.add_argument("--scene-outline", type=Path)
    parser.add_argument("--anti-ai-flavor-level", choices=("low", "medium", "high"), default="")
    parser.add_argument("--revision-mode", action="store_true")
    parser.add_argument("--revision-plan", type=Path)
    parser.add_argument(
        "--style-strictness",
        choices=("low", "medium", "high"),
        default="medium",
        help="How strictly the draft should follow context, function card, and style guide.",
    )
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    args.project = project
    if not project.exists():
        print(f"error: project not found: {project}", file=sys.stderr)
        return 1
    branch_dir = project / "branches" / args.branch
    if not branch_dir.exists():
        print(f"error: branch not found: {branch_dir}", file=sys.stderr)
        return 1

    args.chapter_label = normalize_chapter_label(args.chapter)
    context_pack = (
        resolve_project_relative(project, args.context_pack)
        if args.context_pack
        else default_context_pack(project)
    )
    function_card = (
        resolve_project_relative(project, args.function_card)
        if args.function_card
        else default_function_card(project, args.branch, args.chapter, args.chapter_label)
    )
    style_profile = resolve_project_relative(project, args.style_profile) if args.style_profile else None
    voice_sheet = resolve_project_relative(project, args.voice_sheet) if args.voice_sheet else None
    scene_outline = resolve_project_relative(project, args.scene_outline) if args.scene_outline else None
    revision_plan = resolve_project_relative(project, args.revision_plan) if args.revision_plan else None
    prompt_output = (
        resolve_project_relative(project, args.output)
        if args.output
        else default_prompt_output(project, args.branch, args.chapter_label)
    )
    draft_output = (
        resolve_project_relative(project, args.draft_output)
        if args.draft_output
        else default_draft_output(project, args.branch, args.chapter_label)
    )
    assert context_pack is not None
    assert function_card is not None
    assert prompt_output is not None
    assert draft_output is not None

    if prompt_output.exists() and not args.force:
        print(f"error: prompt exists: {prompt_output}. Use --force to overwrite.", file=sys.stderr)
        return 1
    if not context_pack.exists():
        print(f"warning: context pack not found: {context_pack}")
    if not function_card.exists():
        print(f"warning: chapter function card not found: {function_card}")
    for label, path in (
        ("style profile", style_profile),
        ("character voice sheet", voice_sheet),
        ("scene outline", scene_outline),
        ("revision plan", revision_plan),
    ):
        if path and not path.exists():
            print(f"warning: {label} not found: {path}")

    prompt_output.parent.mkdir(parents=True, exist_ok=True)
    prompt_output.write_text(
        render_prompt(args, context_pack, function_card, style_profile, voice_sheet, scene_outline, revision_plan, prompt_output, draft_output),
        encoding="utf-8",
    )
    print(f"Wrote draft prompt: {prompt_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
