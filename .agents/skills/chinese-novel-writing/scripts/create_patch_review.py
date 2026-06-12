#!/usr/bin/env python3
"""Create a human-readable review report for a pending patch."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _novel_utils import now_iso, parse_scalar, resolve_project_relative, safe_relative


SAFE_UPDATE_TARGETS = {
    "timeline": "branches/<branch>/timeline.yaml",
    "foreshadowing_added": "branches/<branch>/foreshadowing.yaml",
    "open_questions_added": "branches/<branch>/open_questions.md",
    "continuity_issues": "branches/<branch>/continuity_log.md",
}

REVIEW_ONLY_FIELDS = [
    "characters",
    "relationships",
    "worldbuilding",
    "locations",
    "organizations",
    "items",
    "terms",
    "foreshadowing_paid_off",
    "hard_constraints_added",
]


def top_value(text: str, key: str) -> str:
    for line in text.splitlines():
        if line.startswith(f"{key}:"):
            return str(parse_scalar(line.split(":", 1)[1]))
    return ""


def top_block(text: str, key: str) -> list[str]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith(f"{key}:"):
            rest = line.split(":", 1)[1].strip()
            parsed = parse_scalar(rest)
            if isinstance(parsed, list):
                return [f"- {item}" for item in parsed]
            collected: list[str] = []
            for follow in lines[index + 1 :]:
                if follow and not follow.startswith(" "):
                    break
                if follow.strip():
                    collected.append(follow.rstrip())
            return collected
    return []


def update_block(text: str, field: str) -> list[str]:
    lines = text.splitlines()
    in_updates = False
    in_field = False
    collected: list[str] = []
    for line in lines:
        if line.startswith("updates:"):
            in_updates = True
            continue
        if in_updates and line and not line.startswith(" "):
            break
        if not in_updates:
            continue
        if line.startswith(f"  {field}:"):
            rest = line.split(":", 1)[1].strip()
            parsed = parse_scalar(rest)
            if isinstance(parsed, list):
                return [f"- {item}" for item in parsed]
            in_field = True
            continue
        if in_field:
            if line.startswith("  ") and not line.startswith("    "):
                break
            if line.startswith("    "):
                collected.append(line[4:])
    return collected


def has_items(lines: list[str]) -> bool:
    return any(line.strip() and line.strip() != "[]" for line in lines)


def item_count(lines: list[str]) -> int:
    count = sum(1 for line in lines if line.lstrip().startswith("- "))
    return count if count else (1 if has_items(lines) else 0)


def display_path(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path)


def shell_arg(value: str) -> str:
    if not value:
        return '""'
    if any(char.isspace() for char in value):
        return f'"{value}"'
    return value


def resolve_patch_path(project: Path, raw: Path) -> Path:
    if raw.is_absolute():
        return raw
    direct = raw.resolve()
    if direct.exists():
        return direct
    return (project / raw).resolve()


def code_block(lines: list[str]) -> list[str]:
    if not has_items(lines):
        return ["- None"]
    return ["```yaml", *lines, "```"]


def render_update_section(
    title: str,
    fields: list[str],
    updates: dict[str, list[str]],
    branch: str,
) -> list[str]:
    lines = [f"## {title}", ""]
    found = False
    for field in fields:
        values = updates.get(field, [])
        if not has_items(values):
            continue
        found = True
        lines.append(f"### updates.{field}")
        if field in SAFE_UPDATE_TARGETS:
            target = SAFE_UPDATE_TARGETS[field].replace("<branch>", branch)
            lines.append(f"- Target: `{target}`")
        lines.append(f"- Items: {item_count(values)}")
        lines.append("")
        lines.extend(code_block(values))
        lines.append("")
    if not found:
        lines.append("- None")
        lines.append("")
    return lines


def recommendation(
    safe_updates: dict[str, list[str]],
    review_updates: dict[str, list[str]],
    confirmations: list[str],
    conflicts: list[str],
) -> str:
    has_safe = any(has_items(values) for values in safe_updates.values())
    has_review = any(has_items(values) for values in review_updates.values())
    has_confirmations = has_items(confirmations)
    has_conflicts = has_items(conflicts)
    if has_confirmations or has_conflicts:
        return "Do not apply yet. Resolve confirmations or conflicts first, then dry-run again."
    if has_safe and has_review:
        return "Dry-run is allowed for safe fields, but review-only fields will not be merged automatically."
    if has_safe:
        return "Run dry-run first; apply only after the report has been reviewed."
    if has_review:
        return "No automatically mergeable updates. Review and edit target files or patch structure manually."
    return "Patch has no actionable update items yet."


def render_report(args: argparse.Namespace, patch: Path, output: Path, text: str) -> str:
    project = args.project.resolve()
    cwd = Path.cwd()
    branch = top_value(text, "branch") or "main"
    patch_id = top_value(text, "patch_id") or patch.stem
    chapter = top_value(text, "chapter")
    source_draft = top_value(text, "source_draft")
    status = top_value(text, "status")
    safe_updates = {field: update_block(text, field) for field in SAFE_UPDATE_TARGETS}
    review_updates = {field: update_block(text, field) for field in REVIEW_ONLY_FIELDS}
    confirmations = top_block(text, "requires_user_confirmation")
    conflicts = top_block(text, "potential_conflicts")

    project_cli = shell_arg(display_path(project, cwd))
    patch_cli = shell_arg(display_path(patch, cwd))
    dry_run = (
        "python .agents/skills/chinese-novel-writing/scripts/novel_project.py "
        f"apply-patch --project-root {project_cli} --patch {patch_cli}"
    )
    apply = dry_run + " --confirm"
    apply_major = apply + " --confirm-major"

    lines = [
        "# Patch Review Report",
        "",
        "schema_version: 0.5",
        f"generated_at: {now_iso()}",
        f"patch: {safe_relative(patch, project)}",
        f"patch_id: {patch_id}",
        f"branch: {branch}",
        f"chapter: {chapter}",
        f"source_draft: {source_draft}",
        f"patch_status: {status}",
        f"review_report: {safe_relative(output, project)}",
        "",
        "## Summary",
        "",
        f"- Safe update items: {sum(item_count(values) for values in safe_updates.values())}",
        f"- Review-only update items: {sum(item_count(values) for values in review_updates.values())}",
        f"- Requires user confirmation: {item_count(confirmations)}",
        f"- Potential conflicts: {item_count(conflicts)}",
        f"- Recommendation: {recommendation(safe_updates, review_updates, confirmations, conflicts)}",
        "",
    ]
    lines.extend(render_update_section("Safe Updates", list(SAFE_UPDATE_TARGETS), safe_updates, branch))
    lines.extend(render_update_section("Review-Only Updates", REVIEW_ONLY_FIELDS, review_updates, branch))
    lines.extend(["## Requires User Confirmation", ""])
    lines.extend(code_block(confirmations))
    lines.extend(["", "## Potential Conflicts", ""])
    lines.extend(code_block(conflicts))
    lines.extend(
        [
            "",
            "## Dry-Run And Apply Guidance",
            "",
            "Run dry-run first; it should not write files:",
            "",
            "```bash",
            dry_run,
            "```",
            "",
            "Apply only limited safe updates after review:",
            "",
            "```bash",
            apply,
            "```",
            "",
            "If and only if the user explicitly confirms major plot changes, use:",
            "",
            "```bash",
            apply_major,
            "```",
            "",
            "Review-only fields are not automatically merged by `apply-patch`; convert them manually or keep them in the patch queue.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a human-readable patch review report.")
    parser.add_argument("--project", "--project-root", dest="project", required=True, type=Path)
    parser.add_argument("--patch", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    args.project = project
    if not project.exists():
        print(f"error: project not found: {project}", file=sys.stderr)
        return 1
    patch = resolve_patch_path(project, args.patch)
    if not patch.exists():
        print(f"error: patch not found: {patch}", file=sys.stderr)
        return 1
    output = (
        resolve_project_relative(project, args.output)
        if args.output
        else patch.with_name(f"{patch.stem}_review.md")
    )
    assert output is not None
    if output.exists() and not args.force:
        print(f"error: report exists: {output}. Use --force to overwrite.", file=sys.stderr)
        return 1

    text = patch.read_text(encoding="utf-8", errors="replace")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(args, patch, output, text), encoding="utf-8")
    print(f"Wrote patch review report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
