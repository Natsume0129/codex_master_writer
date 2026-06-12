#!/usr/bin/env python3
"""Safely apply limited pending update patches after user confirmation."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from _novel_utils import now_iso, parse_scalar, set_top_level_value, yaml_quote


def top_value(text: str, key: str) -> str:
    for line in text.splitlines():
        if line.startswith(f"{key}:"):
            return str(parse_scalar(line.split(":", 1)[1]))
    return ""


def top_list(text: str, key: str) -> list[str]:
    lines = text.splitlines()
    values: list[str] = []
    for index, line in enumerate(lines):
        if line.startswith(f"{key}:"):
            rest = line.split(":", 1)[1].strip()
            parsed = parse_scalar(rest)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
            for follow in lines[index + 1 :]:
                if follow and not follow.startswith(" "):
                    break
                stripped = follow.strip()
                if stripped.startswith("- "):
                    values.append(stripped[2:].strip().strip('"').strip("'"))
            break
    return values


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
                return [str(item) for item in parsed]
            in_field = True
            continue
        if in_field:
            if line.startswith("  ") and not line.startswith("    "):
                break
            if line.startswith("    "):
                collected.append(line[4:])
    return collected


def backup_file(project: Path, path: Path) -> Path:
    stamp = now_iso().replace(":", "").replace("+", "_")
    backup_dir = project / "backups" / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / path.relative_to(project)
    backup.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copyfile(path, backup)
    return backup


def append_yaml_items(path: Path, root_key: str, items: list[str]) -> None:
    if not items:
        return
    existing = path.read_text(encoding="utf-8", errors="replace") if path.exists() else f"{root_key}: []\n"
    if existing.strip() == f"{root_key}: []":
        existing = f"{root_key}:\n"
    if not existing.endswith("\n"):
        existing += "\n"
    lines = [existing.rstrip()]
    for item in items:
        if item.startswith("- ") or item.startswith(" "):
            lines.append(f"  {item}")
        else:
            lines.append(f"  - {yaml_quote(item)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def append_markdown(path: Path, title: str, items: list[str]) -> None:
    if not items:
        return
    existing = path.read_text(encoding="utf-8", errors="replace") if path.exists() else f"# {title}\n"
    if not existing.endswith("\n"):
        existing += "\n"
    lines = [existing.rstrip(), "", f"## Applied Patch {now_iso()}", ""]
    for item in items:
        if item.startswith("- ") or item.startswith(" "):
            lines.append(item)
        else:
            lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply limited pending update patches safely.")
    parser.add_argument("--project", required=True, type=Path, help="Novel project root.")
    parser.add_argument("--patch", required=True, type=Path, help="Patch YAML file.")
    parser.add_argument("--confirm", action="store_true", help="Actually write changes. Default is dry-run.")
    parser.add_argument("--confirm-major", action="store_true", help="Allow patches requiring user confirmation.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    patch = args.patch.resolve()
    if not project.exists():
        print(f"error: project not found: {project}", file=sys.stderr)
        return 1
    if not patch.exists():
        print(f"error: patch not found: {patch}", file=sys.stderr)
        return 1
    text = patch.read_text(encoding="utf-8", errors="replace")
    branch = top_value(text, "branch") or "main"
    patch_id = top_value(text, "patch_id") or patch.stem
    confirmations = top_list(text, "requires_user_confirmation")
    if confirmations and not args.confirm_major:
        print("error: patch requires user confirmation; pass --confirm-major after review", file=sys.stderr)
        return 1

    branch_dir = project / "branches" / branch
    planned = {
        branch_dir / "timeline.yaml": ("timeline", update_block(text, "timeline")),
        branch_dir / "foreshadowing.yaml": ("foreshadowing", update_block(text, "foreshadowing_added")),
        branch_dir / "open_questions.md": ("Open Questions", update_block(text, "open_questions_added")),
        branch_dir / "continuity_log.md": ("Continuity Log", update_block(text, "continuity_issues")),
    }
    review_needed = []
    for field in ("characters", "relationships", "worldbuilding", "locations", "organizations", "items", "terms"):
        if update_block(text, field):
            review_needed.append(field)

    changed = [(path, root, items) for path, (root, items) in planned.items() if items]
    print("Dry-run plan:" if not args.confirm else "Apply plan:")
    print(f"- patch_id: {patch_id}")
    print(f"- branch: {branch}")
    for path, _, items in changed:
        print(f"- update {path.relative_to(project)} ({len(items)} items)")
    for field in review_needed:
            print(f"- review_needed: updates.{field} is not auto-merged in v0.4")
    if not changed:
        print("- no safely mergeable updates found")
    if not args.confirm:
        print("No files changed. Pass --confirm to apply limited safe updates.")
        return 0

    backups = []
    for path, root, items in changed:
        backups.append(backup_file(project, path))
        if path.suffix == ".yaml":
            append_yaml_items(path, root, items)
        else:
            append_markdown(path, root, items)
    set_top_level_value(patch, "status", "applied")
    changelog = project / "changelog.md"
    entry = [
        "",
        f"## {now_iso()}",
        "",
        f"- patch_id: {patch_id}",
        f"- patch: {patch.relative_to(project) if patch.is_relative_to(project) else patch}",
        f"- branch: {branch}",
        f"- changed_files: {len(changed)}",
        f"- backups: {', '.join(str(item.relative_to(project)) for item in backups)}",
        f"- review_needed: {', '.join(review_needed) if review_needed else 'none'}",
        "",
    ]
    changelog.parent.mkdir(parents=True, exist_ok=True)
    with changelog.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(entry))
    print(f"Applied patch. Backups: {len(backups)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
