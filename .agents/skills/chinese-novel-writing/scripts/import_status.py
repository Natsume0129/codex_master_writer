#!/usr/bin/env python3
"""Report deterministic import progress without reading raw full text."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from _novel_utils import chapter_label_candidates, now_iso, parse_mapping_list, parse_progress, safe_relative, yaml_quote


STATUSES = ("pending", "queued", "processing", "done", "failed", "skipped")


def card_exists(project: Path, rel: str) -> bool:
    return (project / rel).exists()


def chapter_card_exists(project: Path, chapter_id: str) -> bool:
    for candidate in chapter_label_candidates(chapter_id):
        if (project / "extracted" / "chapter_cards" / f"{candidate}.yaml").exists():
            return True
    return False


def collect_status(project: Path) -> dict[str, object]:
    manifest = project / "imports" / "chunk_manifest.yaml"
    progress_path = project / "imports" / "extraction_progress.yaml"
    warnings: list[str] = []
    chunks = parse_mapping_list(manifest, "chunks")
    progress = parse_progress(progress_path)
    progress_chunks = progress.get("chunks", {})
    progress_chapters = progress.get("chapters", {})
    progress_batches = progress.get("batches", {})
    if not manifest.exists():
        warnings.append("imports/chunk_manifest.yaml is missing.")
    if not progress_path.exists():
        warnings.append("imports/extraction_progress.yaml is missing.")

    chunk_statuses = Counter()
    pending_chunks: list[str] = []
    failed_chunks: list[str] = []
    missing_chunk_cards: list[str] = []
    chunk_card_done = 0
    if isinstance(progress_chunks, dict) and progress_chunks:
        for chunk_id, record in progress_chunks.items():
            if not isinstance(record, dict):
                continue
            status = str(record.get("status", ""))
            chunk_statuses[status] += 1
            if status == "pending":
                pending_chunks.append(str(chunk_id))
            card = str(record.get("chunk_card", "")) or f"extracted/chunk_cards/{chunk_id}.yaml"
            if card_exists(project, card):
                chunk_card_done += 1
            elif status == "done":
                missing_chunk_cards.append(str(chunk_id))
            if status == "failed":
                failed_chunks.append(f"{chunk_id}: {record.get('error', '')}")
    else:
        chunk_statuses["pending"] = len(chunks)
        pending_chunks = [str(chunk.get("chunk_id", "")) for chunk in chunks if chunk.get("chunk_id")]

    ready_chapters: list[str] = []
    chapter_ids: list[str] = []
    if isinstance(progress_chapters, dict):
        for chapter_id, record in progress_chapters.items():
            chapter_ids.append(str(chapter_id))
            if isinstance(record, dict) and record.get("status") == "ready_for_chapter_card":
                ready_chapters.append(str(chapter_id))
    else:
        chapter_ids = sorted({str(chunk.get("chapter_id", "")) for chunk in chunks if chunk.get("chapter_id")})

    chapter_cards_done = []
    missing_chapter_cards = []
    for chapter_id in chapter_ids:
        if chapter_card_exists(project, chapter_id):
            chapter_cards_done.append(chapter_id)
        else:
            missing_chapter_cards.append(chapter_id)

    batch_statuses = Counter()
    if isinstance(progress_batches, dict):
        for record in progress_batches.values():
            if isinstance(record, dict):
                batch_statuses[str(record.get("status", ""))] += 1
    batch_files = sorted((project / "imports" / "batches").glob("batch_*_*.yaml"))
    volume_summaries = sorted((project / "extracted" / "volume_summaries").glob("volume_*.md"))
    bible_patches = sorted((project / "pending_updates").glob("import_bible_patch_*.yaml"))
    conflicts = project / "imports" / "conflicts_found.md"

    next_actions: list[str] = []
    if chunk_statuses["pending"]:
        next_actions.append("Run create-batch, then process the listed chunk files with Codex.")
    if chunk_statuses["queued"] or chunk_statuses["processing"]:
        next_actions.append("Process the active batch and run mark-done when chunk cards are created.")
    if ready_chapters:
        next_actions.append("Run create-chapter-card-batch for ready chapters.")
    if chapter_cards_done and not volume_summaries:
        next_actions.append("Run create-volume-summary-batch after chapter cards are reviewed.")
    if volume_summaries and not bible_patches:
        next_actions.append("Run create-bible-patch-batch to prepare story bible patch candidates.")
    if bible_patches:
        next_actions.append("Review pending import bible patches; apply-patch remains dry-run by default.")
    if not next_actions:
        next_actions.append("No immediate deterministic import action found; review import_report.md.")

    return {
        "generated_at": now_iso(),
        "warnings": warnings,
        "chunk_count": len(chunks) or sum(chunk_statuses.values()),
        "chunk_statuses": dict(chunk_statuses),
        "batch_statuses": dict(batch_statuses),
        "batch_files": [safe_relative(path, project) for path in batch_files],
        "chunk_cards_done": chunk_card_done,
        "pending_chunks": pending_chunks,
        "missing_chunk_cards": missing_chunk_cards,
        "ready_chapters": ready_chapters,
        "chapter_cards_done": chapter_cards_done,
        "missing_chapter_cards": missing_chapter_cards,
        "volume_summaries": [safe_relative(path, project) for path in volume_summaries],
        "bible_patches": [safe_relative(path, project) for path in bible_patches],
        "failed_chunks": failed_chunks,
        "conflicts_file": safe_relative(conflicts, project) if conflicts.exists() else "",
        "next_actions": next_actions,
    }


def render_markdown(status: dict[str, object]) -> str:
    chunk_statuses = status["chunk_statuses"]
    assert isinstance(chunk_statuses, dict)
    batch_statuses = status["batch_statuses"]
    assert isinstance(batch_statuses, dict)
    lines = [
        "# Import Status",
        "",
        f"Generated at: {status['generated_at']}",
        "",
        "## Summary",
        "",
        f"- chunks_total: {status['chunk_count']}",
    ]
    for item in STATUSES:
        lines.append(f"- chunks_{item}: {chunk_statuses.get(item, 0)}")
    lines.extend(
        [
            f"- batches_total: {sum(batch_statuses.values())}",
            f"- chunk_cards_done: {status['chunk_cards_done']}",
            f"- missing_chunk_cards: {len(status['missing_chunk_cards'])}",
            f"- ready_for_chapter_card: {len(status['ready_chapters'])}",
            f"- chapter_cards_done: {len(status['chapter_cards_done'])}",
            f"- missing_chapter_cards: {len(status['missing_chapter_cards'])}",
            f"- volume_summaries_done: {len(status['volume_summaries'])}",
            f"- bible_patches_done: {len(status['bible_patches'])}",
            "",
            "## Next Actions",
            "",
        ]
    )
    for index, item in enumerate(status["next_actions"], start=1):
        lines.append(f"{index}. {item}")
    for title, key in [
        ("Warnings", "warnings"),
        ("Pending Chunks", "pending_chunks"),
        ("Missing Chunk Cards", "missing_chunk_cards"),
        ("Failed Chunks", "failed_chunks"),
        ("Ready Chapters", "ready_chapters"),
        ("Missing Chapter Cards", "missing_chapter_cards"),
        ("Batch Files", "batch_files"),
        ("Volume Summaries", "volume_summaries"),
        ("Bible Patches", "bible_patches"),
    ]:
        values = status[key]
        assert isinstance(values, list)
        lines.extend(["", f"## {title}", ""])
        if values:
            for value in values:
                lines.append(f"- {value}")
        else:
            lines.append("- None")
    lines.extend(["", "## Notes", "", "- This report does not read raw_text/full_text.txt."])
    return "\n".join(lines) + "\n"


def render_text(status: dict[str, object]) -> str:
    return render_markdown(status)


def render_yaml(status: dict[str, object]) -> str:
    lines = ['schema_version: "0.4"', f"generated_at: {yaml_quote(status['generated_at'])}"]
    for key in (
        "warnings",
        "chunk_count",
        "chunk_statuses",
        "batch_statuses",
        "batch_files",
        "chunk_cards_done",
        "pending_chunks",
        "missing_chunk_cards",
        "ready_chapters",
        "chapter_cards_done",
        "missing_chapter_cards",
        "volume_summaries",
        "bible_patches",
        "failed_chunks",
        "next_actions",
    ):
        value = status[key]
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for subkey, subvalue in value.items():
                lines.append(f"  {subkey}: {subvalue}")
        elif isinstance(value, list):
            lines.append(f"{key}:")
            if value:
                for item in value:
                    lines.append(f"  - {yaml_quote(item)}")
            else:
                lines.append("  []")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report import progress and next deterministic actions.")
    parser.add_argument("--project", "--project-root", dest="project", required=True, type=Path)
    parser.add_argument("--format", choices=("markdown", "text", "yaml"), default="markdown")
    parser.add_argument("--output", type=Path, help="Optional report path. Defaults to imports/import_status.md.")
    parser.add_argument("--show-pending", action="store_true", help="Accepted for CLI clarity; markdown always includes missing chunks.")
    parser.add_argument("--show-failed", action="store_true", help="Accepted for CLI clarity; markdown always includes failures.")
    parser.add_argument("--show-ready", action="store_true", help="Accepted for CLI clarity; markdown always includes ready chapters.")
    parser.add_argument("--show-next", action="store_true", help="Accepted for CLI clarity; markdown always includes next actions.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    if not project.exists():
        print(f"error: project not found: {project}", file=sys.stderr)
        return 1
    status = collect_status(project)
    if args.format == "yaml":
        content = render_yaml(status)
    elif args.format == "text":
        content = render_text(status)
    else:
        content = render_markdown(status)
    output = args.output.resolve() if args.output else project / "imports" / "import_status.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    print(content.rstrip())
    print(f"\nWrote import status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
