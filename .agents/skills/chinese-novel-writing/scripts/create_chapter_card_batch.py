#!/usr/bin/env python3
"""Create chapter-card extraction batch files from completed chunk cards."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _novel_utils import (
    chapter_label_candidates,
    next_batch_id,
    now_iso,
    parse_progress,
    safe_relative,
    write_progress,
    yaml_quote,
)


def existing_chapter_card(project: Path, chapter_id: str) -> Path | None:
    for candidate in chapter_label_candidates(chapter_id):
        path = project / "extracted" / "chapter_cards" / f"{candidate}.yaml"
        if path.exists():
            return path
    return None


def chunk_card_path(project: Path, chunk_id: str, record: dict[str, object]) -> str:
    explicit = str(record.get("chunk_card", "") or "")
    if explicit:
        return explicit
    return safe_relative(project / "extracted" / "chunk_cards" / f"{chunk_id}.yaml", project)


def eligible_chapters(project: Path, progress: dict[str, object], args: argparse.Namespace) -> list[tuple[str, list[str]]]:
    chunks = progress.get("chunks", {})
    chapters = progress.get("chapters", {})
    if not isinstance(chunks, dict) or not isinstance(chapters, dict):
        return []
    requested = set()
    if args.chapter:
        requested.update(chapter_label_candidates(args.chapter))
    selected: list[tuple[str, list[str]]] = []
    for chapter_id, chapter in chapters.items():
        chapter_key = str(chapter_id)
        if requested and chapter_key not in requested:
            continue
        if not isinstance(chapter, dict):
            continue
        status = str(chapter.get("status", ""))
        chunk_ids = [str(item) for item in chapter.get("chunk_ids", [])] if isinstance(chapter.get("chunk_ids"), list) else []
        statuses = []
        for chunk_id in chunk_ids:
            record = chunks.get(chunk_id, {})
            if isinstance(record, dict):
                statuses.append(str(record.get("status", "")))
        all_done = bool(statuses) and all(item == "done" for item in statuses)
        ready = status == "ready_for_chapter_card" or all_done
        if args.only_ready and status != "ready_for_chapter_card":
            ready = False
        if args.retry_failed and status == "failed":
            ready = True
        if not ready:
            continue
        if existing_chapter_card(project, chapter_key) and not args.force and not args.retry_failed:
            continue
        selected.append((chapter_key, chunk_ids))
        if len(selected) >= args.batch_size:
            break
    return selected


def render_markdown(batch_id: str, project: Path, chapters: list[tuple[str, list[str]]], progress: dict[str, object]) -> str:
    chunks = progress.get("chunks", {})
    assert isinstance(chunks, dict)
    lines = [
        f"# Chapter Card Batch {batch_id}",
        "",
        f"- schema_version: `0.4`",
        f"- batch_id: `{batch_id}`",
        "- stage: `chapter_cards`",
        "",
        "## Chapters",
        "",
    ]
    for chapter_id, chunk_ids in chapters:
        lines.extend([f"### {chapter_id}", "", "Source chunk cards:"])
        for chunk_id in chunk_ids:
            record = chunks.get(chunk_id, {})
            card = chunk_card_path(project, chunk_id, record) if isinstance(record, dict) else ""
            lines.append(f"- `{card}`")
        lines.append("")
    lines.extend(
        [
            "## Codex Instructions",
            "",
            "- Read only the chunk cards listed in this batch.",
            "- Do not read `raw_text/full_text.txt`.",
            "- Do not read the whole novel or raw chapter files.",
            "- Generate `extracted/chapter_cards/<chapter_id>.yaml` for each chapter.",
            "- Every important fact must include `source`, `status`, and `confidence`.",
            "- Do not write inferred content as `confirmed`.",
            "- Do not directly modify `canon/`; use pending updates for proposed changes.",
            "",
            "## Required Chapter Card Schema",
            "",
            "```yaml",
            'schema_version: "0.4"',
            'chapter_id: ""',
            'title: ""',
            "source_chunk_cards: []",
            'summary: ""',
            'chapter_function: ""',
            "major_events: []",
            "characters_present: []",
            "relationship_changes: []",
            "new_worldbuilding: []",
            "locations: []",
            "organizations: []",
            "items: []",
            "terms: []",
            "timeline_events: []",
            "foreshadowing: []",
            "open_questions: []",
            'ending_hook: ""',
            'style_snapshot: ""',
            "facts:",
            '  - category: ""',
            '    value: ""',
            '    status: "confirmed | inferred | uncertain | user_override | deprecated"',
            "    source: []",
            '    confidence: "high | medium | low"',
            '    notes: ""',
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def render_yaml(batch_id: str, chapters: list[tuple[str, list[str]]]) -> str:
    lines = [
        'schema_version: "0.4"',
        f"batch_id: {yaml_quote(batch_id)}",
        'stage: "chapter_cards"',
        'status: "queued"',
        "chapter_ids:",
    ]
    for chapter_id, _ in chapters:
        lines.append(f"  - {yaml_quote(chapter_id)}")
    lines.extend([f"created_at: {yaml_quote(now_iso())}", "outputs_expected:", '  - "extracted/chapter_cards/*.yaml"', ""])
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a chapter-card batch from completed chunk cards.")
    parser.add_argument("--project", "--project-root", dest="project", required=True, type=Path)
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--chapter", default="")
    parser.add_argument("--only-ready", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    if not project.exists():
        print(f"error: project not found: {project}", file=sys.stderr)
        return 1
    progress_path = project / "imports" / "extraction_progress.yaml"
    if not progress_path.exists():
        print(f"warning: extraction progress not found: {progress_path}")
        print("No eligible chapters found.")
        return 0
    progress = parse_progress(progress_path)
    chapters = eligible_chapters(project, progress, args)
    if not chapters:
        print("No eligible chapters found.")
        return 0
    batch_dir = project / "imports" / "batches"
    batch_id = next_batch_id(batch_dir, progress)
    md_path = batch_dir / f"{batch_id}_chapter_cards.md"
    yaml_path = batch_dir / f"{batch_id}_chapter_cards.yaml"
    print(f"Batch: {batch_id}")
    print(f"Stage: chapter_cards")
    print(f"Chapters: {len(chapters)}")
    for chapter_id, _ in chapters:
        print(f"- {chapter_id}")
    if args.dry_run:
        return 0
    if (md_path.exists() or yaml_path.exists()) and not args.force:
        print(f"error: batch files exist. Use --force to overwrite: {batch_id}", file=sys.stderr)
        return 1
    batch_dir.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_markdown(batch_id, project, chapters, progress), encoding="utf-8")
    yaml_path.write_text(render_yaml(batch_id, chapters), encoding="utf-8")
    batches = progress.get("batches", {})
    if isinstance(batches, dict):
        batches[batch_id] = {
            "stage": "chapter_cards",
            "status": "queued",
            "chapter_ids": [chapter_id for chapter_id, _ in chapters],
            "created_at": now_iso(),
            "completed_at": "",
            "notes": "",
        }
        write_progress(progress_path, progress)
    print(f"Wrote: {md_path}")
    print(f"Wrote: {yaml_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
