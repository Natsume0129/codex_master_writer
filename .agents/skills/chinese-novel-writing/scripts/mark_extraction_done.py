#!/usr/bin/env python3
"""Mark extraction chunks or batches as done/failed/skipped."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _novel_utils import now_iso, parse_progress, write_progress


def update_chapter_states(progress: dict[str, object]) -> None:
    chunks = progress.get("chunks", {})
    chapters = progress.get("chapters", {})
    if not isinstance(chunks, dict) or not isinstance(chapters, dict):
        return
    now = now_iso()
    for chapter_id, chapter in chapters.items():
        if not isinstance(chapter, dict):
            continue
        ids = chapter.get("chunk_ids", [])
        if not isinstance(ids, list) or not ids:
            continue
        statuses = []
        for chunk_id in ids:
            record = chunks.get(str(chunk_id), {})
            if isinstance(record, dict):
                statuses.append(str(record.get("status", "")))
        if statuses and all(status == "done" for status in statuses):
            chapter["status"] = "ready_for_chapter_card"
        elif any(status == "failed" for status in statuses):
            chapter["status"] = "partial"
        elif any(status == "done" for status in statuses):
            chapter["status"] = "partial"
        else:
            chapter["status"] = "pending"
        chapter["updated_at"] = now


def default_chunk_card(project: Path, chunk_id: str) -> Path:
    return project / "extracted" / "chunk_cards" / f"{chunk_id}.yaml"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mark extraction progress entries.")
    parser.add_argument("--project", required=True, type=Path, help="Novel project root.")
    parser.add_argument("--batch-id", help="Batch id to mark.")
    parser.add_argument("--stage", default="chunk_cards", help="Stage for batch updates.")
    parser.add_argument("--chunk-id", help="Single chunk id to mark.")
    parser.add_argument("--chunk-card", type=Path, help="Chunk card path for a single chunk.")
    parser.add_argument("--status", required=True, choices=("done", "failed", "skipped", "processing", "queued"), help="New status.")
    parser.add_argument("--error", default="", help="Error message for failed status.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    progress_path = project / "imports" / "extraction_progress.yaml"
    if not progress_path.exists():
        print(f"error: extraction progress not found: {progress_path}", file=sys.stderr)
        return 1
    if not args.batch_id and not args.chunk_id:
        print("error: provide --batch-id or --chunk-id", file=sys.stderr)
        return 1
    progress = parse_progress(progress_path)
    chunks = progress.get("chunks", {})
    batches = progress.get("batches", {})
    if not isinstance(chunks, dict) or not isinstance(batches, dict):
        print("error: invalid extraction_progress.yaml", file=sys.stderr)
        return 1

    now = now_iso()
    warnings: list[str] = []
    changed = 0

    target_chunk_ids: list[str] = []
    if args.batch_id:
        batch = batches.get(args.batch_id)
        if not isinstance(batch, dict):
            print(f"error: batch not found: {args.batch_id}", file=sys.stderr)
            return 1
        batch["status"] = args.status
        if args.status in {"done", "failed", "skipped"}:
            batch["completed_at"] = now
        if args.error:
            batch["notes"] = args.error
        ids = batch.get("chunk_ids", [])
        target_chunk_ids.extend(str(item) for item in ids if item)
    if args.chunk_id:
        target_chunk_ids.append(args.chunk_id)

    for chunk_id in sorted(set(target_chunk_ids)):
        record = chunks.get(chunk_id)
        if not isinstance(record, dict):
            warnings.append(f"chunk not found in progress: {chunk_id}")
            continue
        record["status"] = args.status
        record["updated_at"] = now
        if args.batch_id:
            record["batch_id"] = args.batch_id
        if args.status == "failed":
            record["error"] = args.error
        if args.status == "done":
            card = args.chunk_card.resolve() if args.chunk_card and args.chunk_id == chunk_id else default_chunk_card(project, chunk_id)
            record["chunk_card"] = str(card)
            if not card.exists():
                warnings.append(f"chunk_card missing for {chunk_id}: {card}")
        changed += 1

    project_meta = progress.get("project", {})
    if isinstance(project_meta, dict):
        project_meta["updated_at"] = now
    update_chapter_states(progress)
    write_progress(progress_path, progress)
    print(f"Updated chunks: {changed}")
    for warning in warnings:
        print(f"warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

