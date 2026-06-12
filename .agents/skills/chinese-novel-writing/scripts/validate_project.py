#!/usr/bin/env python3
"""Validate a Chinese novel project directory."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from _novel_utils import parse_mapping_list, parse_progress


REQUIRED_DIRS = [
    "raw_text",
    "raw_text/chapters",
    "imports",
    "imports/batches",
    "chunks",
    "extracted/chunk_cards",
    "extracted/chapter_cards",
    "extracted/volume_summaries",
    "canon",
    "branches/main",
    "branches/main/chapter_summaries",
    "branches/main/chapter_function_cards",
    "indexes",
    "pending_updates",
    "context_packs",
    "backups",
]

REQUIRED_FILES = [
    "project_config.yaml",
    "user_preferences.md",
    "changelog.md",
    "imports/extraction_progress.yaml",
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
    "indexes/chapter_index.yaml",
    "indexes/chunk_index.yaml",
    "indexes/character_index.yaml",
    "indexes/location_index.yaml",
    "indexes/item_index.yaml",
    "indexes/organization_index.yaml",
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
    "chapter_function_cards",
]

ALT_BRANCH_REQUIRED = [
    "branch_config.yaml",
    "divergence_point.yaml",
    "causal_impact_log.md",
    "timeline.yaml",
    "foreshadowing.yaml",
    "continuity_log.md",
]

PENDING_PATCH_FIELDS = [
    "patch_id",
    "branch",
    "chapter",
    "source_draft",
    "status",
    "updates",
    "requires_user_confirmation",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def basic_yaml_check(path: Path) -> list[str]:
    errors: list[str] = []
    text = read_text(path)
    if "\x00" in text:
        errors.append("contains NUL byte")
    for number, line in enumerate(text.splitlines(), start=1):
        if "\t" in line[: len(line) - len(line.lstrip())]:
            errors.append(f"line {number}: leading tab indentation")
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped in {"---", "..."}:
            continue
        if stripped.startswith("- ") or stripped.startswith(("[]", "{}")):
            continue
        if ":" not in stripped:
            errors.append(f"line {number}: suspicious YAML line without ':'")
    if text.count("[") != text.count("]"):
        errors.append("unbalanced square brackets")
    if text.count("{") != text.count("}"):
        errors.append("unbalanced curly braces")
    return errors


def simple_yaml_value(path: Path, key: str) -> str:
    if not path.exists():
        return ""
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*:\s*(.*)\s*$")
    for line in read_text(path).splitlines():
        match = pattern.match(line)
        if match:
            return match.group(1).strip().strip('"').strip("'")
    return ""


def visible_fields(path: Path, fields: list[str]) -> list[str]:
    if not path.exists():
        return fields
    text = read_text(path)
    missing: list[str] = []
    for field in fields:
        if re.search(rf"^\s*-?\s*{re.escape(field)}\s*:", text, flags=re.MULTILINE) is None:
            missing.append(field)
    return missing


def check_fact_fields(project: Path, errors: list[str], warnings: list[str]) -> None:
    for yaml_file in project.rglob("*.yaml"):
        text = read_text(yaml_file)
        legacy_key = "fact_" + "status"
        if legacy_key in text:
            errors.append(f"{yaml_file.relative_to(project)} uses deprecated fact status key; use status")

    required_fact_files = [
        "canon/characters.yaml",
        "canon/items.yaml",
        "branches/main/timeline.yaml",
        "branches/main/foreshadowing.yaml",
    ]
    for rel in required_fact_files:
        path = project / rel
        if not path.exists():
            continue
        text = read_text(path)
        for field in ("source:", "status:", "confidence:"):
            if field not in text:
                warnings.append(f"{rel} does not visibly include {field}")


def check_schema_hints(project: Path, warnings: list[str]) -> None:
    schema_groups = {
        "canon/characters.yaml": [
            "name",
            "aliases",
            "role",
            "life_state",
            "identity",
            "current_state",
            "source",
            "status",
            "confidence",
        ],
        "canon/items.yaml": ["id", "name", "owner", "state", "source", "status", "confidence"],
        "branches/main/timeline.yaml": [
            "id",
            "story_time",
            "narrative_order",
            "chapter",
            "event",
            "source",
            "status",
            "confidence",
        ],
        "branches/main/foreshadowing.yaml": [
            "id",
            "content",
            "first_appeared",
            "status",
            "source",
            "confidence",
        ],
    }
    for rel, fields in schema_groups.items():
        missing = visible_fields(project / rel, fields)
        if missing:
            warnings.append(f"{rel} is missing visible schema fields: {', '.join(missing)}")


def check_branches(project: Path, errors: list[str]) -> None:
    branches_dir = project / "branches"
    if not branches_dir.exists():
        errors.append("missing branches directory")
        return
    for branch_dir in sorted(item for item in branches_dir.iterdir() if item.is_dir()):
        branch_name = branch_dir.name
        for rel in BRANCH_REQUIRED:
            if not (branch_dir / rel).exists():
                errors.append(f"branch {branch_name} missing: {rel}")
        if branch_name != "main":
            for rel in ALT_BRANCH_REQUIRED:
                if not (branch_dir / rel).exists():
                    errors.append(f"alternate branch {branch_name} missing: {rel}")


def check_pending_patches(project: Path, errors: list[str], warnings: list[str]) -> None:
    pending_dir = project / "pending_updates"
    if not pending_dir.exists():
        return
    for patch in sorted(pending_dir.glob("*.yaml")):
        text = read_text(patch)
        for field in PENDING_PATCH_FIELDS:
            if re.search(rf"^\s*{field}\s*:", text, flags=re.MULTILINE) is None:
                errors.append(f"pending patch {patch.relative_to(project)} missing {field}")
        if "requires_user_confirmation: []" not in text and "requires_user_confirmation:" in text:
            warnings.append(
                f"pending patch {patch.relative_to(project)} may require explicit user confirmation"
            )


def check_current_branch(project: Path, errors: list[str]) -> None:
    config = project / "project_config.yaml"
    branch = simple_yaml_value(config, "current_branch")
    if branch and not (project / "branches" / branch).exists():
        errors.append(f"project_config current_branch does not exist: {branch}")


def check_context_pack_size(project: Path, warnings: list[str]) -> None:
    full_text = project / "raw_text" / "full_text.txt"
    if not full_text.exists():
        return
    full_size = full_text.stat().st_size
    if full_size == 0 or full_size < 10_000:
        return
    if full_size <= 200_000:
        full_head = read_text(full_text)[:2000]
    else:
        with full_text.open("r", encoding="utf-8", errors="replace") as handle:
            full_head = handle.read(2000)
    for context_pack in (project / "context_packs").glob("*.*"):
        if not context_pack.is_file():
            continue
        if context_pack.stat().st_size >= full_size * 0.9:
            warnings.append(f"context pack may contain too much raw text: {context_pack.relative_to(project)}")
        if full_head and full_head.strip() and full_head.strip() in read_text(context_pack):
            warnings.append(f"context pack appears to include the beginning of full_text: {context_pack.relative_to(project)}")


def resolve_project_path(project: Path, raw: object) -> Path:
    text = str(raw or "")
    path = Path(text)
    return path if path.is_absolute() else project / path


def check_chunk_manifest(project: Path, errors: list[str], warnings: list[str]) -> None:
    manifest = project / "imports" / "chunk_manifest.yaml"
    if not manifest.exists():
        warnings.append("imports/chunk_manifest.yaml is missing; run split_chunks.py after splitting chapters")
        return
    for number, line in enumerate(read_text(manifest).splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("output_file:"):
            raw = stripped.split(":", 1)[1].strip().strip('"').strip("'")
            path = resolve_project_path(project, raw)
            if not path.exists():
                errors.append(f"chunk_manifest line {number} points to missing chunk: {raw}")


def check_extraction_progress(project: Path, errors: list[str], warnings: list[str], suggestions: list[str]) -> None:
    manifest = project / "imports" / "chunk_manifest.yaml"
    progress_path = project / "imports" / "extraction_progress.yaml"
    if not manifest.exists():
        return
    if not progress_path.exists():
        warnings.append("imports/extraction_progress.yaml is missing; run init_extraction_progress.py")
        return

    manifest_chunks = parse_mapping_list(manifest, "chunks")
    progress = parse_progress(progress_path)
    progress_chunks = progress.get("chunks", {})
    progress_chapters = progress.get("chapters", {})
    progress_batches = progress.get("batches", {})

    if not isinstance(progress_chunks, dict):
        errors.append("imports/extraction_progress.yaml chunks section is malformed")
        return

    for chunk in manifest_chunks:
        chunk_id = str(chunk.get("chunk_id", ""))
        if not chunk_id:
            continue
        if chunk_id not in progress_chunks:
            warnings.append(f"extraction_progress missing chunk from manifest: {chunk_id}")
        output_file = chunk.get("output_file", "")
        if output_file and not resolve_project_path(project, output_file).exists():
            errors.append(f"manifest chunk {chunk_id} output_file is missing: {output_file}")

    for chunk_id, value in progress_chunks.items():
        if not isinstance(value, dict):
            errors.append(f"extraction_progress chunk {chunk_id} is malformed")
            continue
        status = str(value.get("status", ""))
        output_file = value.get("output_file", "")
        chunk_card = value.get("chunk_card", "")
        if output_file and not resolve_project_path(project, output_file).exists():
            errors.append(f"extraction_progress chunk {chunk_id} output_file is missing: {output_file}")
        if status == "done":
            if not chunk_card:
                errors.append(f"extraction_progress chunk {chunk_id} is done but chunk_card is empty")
            elif not resolve_project_path(project, chunk_card).exists():
                errors.append(f"extraction_progress chunk {chunk_id} chunk_card is missing: {chunk_card}")
        if status == "failed" and not value.get("error"):
            warnings.append(f"extraction_progress chunk {chunk_id} failed without error text")

    if isinstance(progress_chapters, dict):
        for chapter_id, value in progress_chapters.items():
            if isinstance(value, dict) and value.get("status") == "ready_for_chapter_card":
                suggestions.append(f"chapter {chapter_id} is ready for chapter card generation")

    if isinstance(progress_batches, dict):
        for batch_id, value in progress_batches.items():
            if not isinstance(value, dict):
                errors.append(f"extraction_progress batch {batch_id} is malformed")
                continue
            if value.get("status") in {"queued", "processing"}:
                prompt = project / "imports" / "batches" / f"{batch_id}_chunk_cards.md"
                meta = project / "imports" / "batches" / f"{batch_id}_chunk_cards.yaml"
                if not prompt.exists() or not meta.exists():
                    warnings.append(f"batch {batch_id} is queued but batch prompt/meta file is missing")


def validate_project(project: Path) -> tuple[list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    suggestions: list[str] = []

    if not project.exists():
        return [f"project directory does not exist: {project}"], warnings, suggestions

    for rel in REQUIRED_DIRS:
        if not (project / rel).is_dir():
            errors.append(f"missing directory: {rel}")

    for rel in REQUIRED_FILES:
        if not (project / rel).is_file():
            errors.append(f"missing file: {rel}")

    for yaml_file in project.rglob("*.yaml"):
        for error in basic_yaml_check(yaml_file):
            errors.append(f"yaml issue in {yaml_file.relative_to(project)}: {error}")

    check_fact_fields(project, errors, warnings)
    check_schema_hints(project, warnings)
    check_branches(project, errors)
    check_pending_patches(project, errors, warnings)
    check_current_branch(project, errors)
    check_context_pack_size(project, warnings)
    check_chunk_manifest(project, errors, warnings)
    check_extraction_progress(project, errors, warnings, suggestions)

    if not (project / "context_packs" / "latest_context_pack.md").exists():
        suggestions.append("generate context_packs/latest_context_pack.md before drafting or review")
    if not any((project / "branches" / "main" / "chapter_function_cards").glob("*.yaml")):
        suggestions.append("create a chapter function card before drafting the next chapter")
    if not any((project / "pending_updates").glob("*.yaml")):
        suggestions.append("create post-write patches after drafting or outline changes")
    if not any((project / "indexes").glob("*_index.yaml")):
        suggestions.append("build indexes after extraction; indexes are navigation aids, not source of truth")

    return errors, warnings, suggestions


def print_section(title: str, items: list[str]) -> None:
    if items:
        print(f"\n{title}:")
        for item in items:
            print(f"- {item}")
    else:
        print(f"\n{title}: none")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a novel project structure and v0.3 schemas.")
    parser.add_argument("--project", required=True, type=Path, help="Novel project root.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    errors, warnings, suggestions = validate_project(project)

    print(f"Validation report for: {project}")
    print_section("Errors", errors)
    print_section("Warnings", warnings)
    print_section("Suggestions", suggestions)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
