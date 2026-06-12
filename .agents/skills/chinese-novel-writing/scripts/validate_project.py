#!/usr/bin/env python3
"""Validate a Chinese novel project directory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_DIRS = [
    "raw_text",
    "raw_text/chapters",
    "imports",
    "extracted/chunk_cards",
    "extracted/chapter_cards",
    "extracted/volume_summaries",
    "canon",
    "branches/main",
    "branches/main/chapter_summaries",
    "indexes",
    "pending_updates",
    "context_packs",
]

REQUIRED_FILES = [
    "project_config.yaml",
    "user_preferences.md",
    "changelog.md",
    "canon/canon_bible.md",
    "canon/original_plot_map.md",
    "canon/world_bible.md",
    "canon/characters.yaml",
    "canon/relationships.yaml",
    "canon/locations.yaml",
    "canon/organizations.yaml",
    "canon/items.yaml",
    "canon/terms.yaml",
    "branches/main/branch_config.yaml",
    "branches/main/outline.md",
    "branches/main/volume_outline.md",
    "branches/main/chapter_outlines.md",
    "branches/main/timeline.yaml",
    "branches/main/foreshadowing.yaml",
    "branches/main/continuity_log.md",
    "indexes/character_index.yaml",
    "indexes/location_index.yaml",
    "indexes/item_index.yaml",
    "indexes/event_index.yaml",
    "indexes/foreshadowing_index.yaml",
    "indexes/term_index.yaml",
]

BRANCH_REQUIRED = [
    "branch_config.yaml",
    "outline.md",
    "timeline.yaml",
    "foreshadowing.yaml",
    "continuity_log.md",
    "chapter_summaries",
]

ALT_BRANCH_REQUIRED = [
    "divergence_point.yaml",
    "causal_impact_log.md",
]


def basic_yaml_check(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    if "\x00" in text:
        errors.append("contains NUL byte")
    for number, line in enumerate(text.splitlines(), start=1):
        if "\t" in line[: len(line) - len(line.lstrip())]:
            errors.append(f"line {number}: leading tab indentation")
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped in {"---", "..."}:
            continue
        if stripped.startswith("- "):
            continue
        if ":" not in stripped and not stripped.startswith(("[]", "{}")):
            errors.append(f"line {number}: suspicious YAML line without ':'")
    if text.count("[") != text.count("]"):
        errors.append("unbalanced square brackets")
    if text.count("{") != text.count("}"):
        errors.append("unbalanced curly braces")
    return errors


def validate_project(project: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not project.exists():
        return [f"project directory does not exist: {project}"], warnings

    for rel in REQUIRED_DIRS:
        path = project / rel
        if not path.is_dir():
            errors.append(f"missing directory: {rel}")

    for rel in REQUIRED_FILES:
        path = project / rel
        if not path.is_file():
            errors.append(f"missing file: {rel}")

    for yaml_file in project.rglob("*.yaml"):
        for error in basic_yaml_check(yaml_file):
            errors.append(f"yaml issue in {yaml_file.relative_to(project)}: {error}")

    branches_dir = project / "branches"
    if branches_dir.exists():
        for branch_dir in sorted(item for item in branches_dir.iterdir() if item.is_dir()):
            branch_name = branch_dir.name
            for rel in BRANCH_REQUIRED:
                path = branch_dir / rel
                if not path.exists():
                    errors.append(f"branch {branch_name} missing: {rel}")
            if branch_name != "main":
                for rel in ALT_BRANCH_REQUIRED:
                    path = branch_dir / rel
                    if not path.exists():
                        errors.append(f"alternate branch {branch_name} missing: {rel}")
    else:
        errors.append("missing branches directory")

    full_text = project / "raw_text" / "full_text.txt"
    context_pack = project / "context_packs" / "latest_context_pack.md"
    if full_text.exists() and context_pack.exists():
        if full_text.stat().st_size > 10000 and context_pack.stat().st_size > 10000:
            warnings.append(
                "context pack is large while full_text exists; confirm it does not contain full source text"
            )

    return errors, warnings


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a novel project structure.")
    parser.add_argument("--project", required=True, type=Path, help="Novel project root.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    errors, warnings = validate_project(project)

    print(f"Validation report for: {project}")
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"- {error}")
    else:
        print("\nErrors: none")

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("\nWarnings: none")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
