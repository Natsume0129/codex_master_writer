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


def render_prompt(
    args: argparse.Namespace,
    context_pack: Path,
    function_card: Path,
    prompt_output: Path,
    draft_output: Path,
) -> str:
    project = args.project.resolve()
    context_rel = safe_relative(context_pack, project)
    card_rel = safe_relative(function_card, project)
    prompt_rel = safe_relative(prompt_output, project)
    draft_rel = safe_relative(draft_output, project)
    return f"""# Chapter Draft Prompt

schema_version: 0.5
generated_at: {now_iso()}
branch: {args.branch}
chapter: {args.chapter}
chapter_label: {args.chapter_label}
output_mode: {args.output_mode}
target_length: {args.target_length}
style_strictness: {args.style_strictness}
context_pack: {context_rel}
context_pack_status: {status(context_pack)}
chapter_function_card: {card_rel}
chapter_function_card_status: {status(function_card)}
prompt_output: {prompt_rel}
suggested_draft_output: {draft_rel}

## Task

Draft the chapter for the active branch using only the task-relevant context pack and the chapter function card listed above.

## Required Reading

1. Read `{context_rel}` first.
2. Read `{card_rel}` second.
3. Do not read `raw_text/full_text.txt`.
4. Do not load unrelated full canon files unless the context pack explicitly points to a narrow source that is needed.

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

    prompt_output.parent.mkdir(parents=True, exist_ok=True)
    prompt_output.write_text(
        render_prompt(args, context_pack, function_card, prompt_output, draft_output),
        encoding="utf-8",
    )
    print(f"Wrote draft prompt: {prompt_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
