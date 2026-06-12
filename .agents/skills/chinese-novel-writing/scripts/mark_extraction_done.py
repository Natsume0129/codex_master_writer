#!/usr/bin/env python3
"""Mark extraction chunks or stage-aware batches as done/failed/skipped."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _novel_utils import (
    chapter_label_candidates,
    now_iso,
    parse_progress,
    resolve_project_relative,
    safe_relative,
    write_progress,
)


TERMINAL_STATUSES = {"done", "failed", "skipped"}


def update_chapter_states(progress: dict[str, object]) -> None:
    chunks = progress.get("chunks", {})
    chapters = progress.get("chapters", {})
    if not isinstance(chunks, dict) or not isinstance(chapters, dict):
        return
    now = now_iso()
    for _chapter_id, chapter in chapters.items():
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


def default_chapter_card(project: Path, chapter_id: str) -> Path:
    for candidate in chapter_label_candidates(chapter_id):
        path = project / "extracted" / "chapter_cards" / f"{candidate}.yaml"
        if path.exists():
            return path
    return project / "extracted" / "chapter_cards" / f"{chapter_id}.yaml"


def infer_stage(args: argparse.Namespace, batch: dict[str, object] | None) -> str:
    if args.stage:
        return args.stage
    if args.chapter_id or args.chapter_card:
        return "chapter_cards"
    if batch:
        stage = str(batch.get("stage", "") or "")
        if stage:
            return stage
        if batch.get("chapter_ids"):
            return "chapter_cards"
        if batch.get("volume"):
            return "volume_summaries"
        if batch.get("patch_skeleton"):
            return "story_bible_patches"
        if batch.get("chunk_ids"):
            return "chunk_cards"
    return "chunk_cards"


def update_batch_metadata(
    batch: dict[str, object] | None, args: argparse.Namespace, now: str
) -> None:
    if not batch:
        return
    batch["status"] = args.status
    if args.status in TERMINAL_STATUSES:
        batch["completed_at"] = now
    if args.error:
        batch["notes"] = args.error


def find_chapter_record(
    chapters: dict[object, object], chapter_id: str
) -> tuple[str, dict[str, object]] | tuple[None, None]:
    if chapter_id in chapters and isinstance(chapters[chapter_id], dict):
        return chapter_id, chapters[chapter_id]  # type: ignore[return-value]
    for candidate in chapter_label_candidates(chapter_id):
        value = chapters.get(candidate)
        if isinstance(value, dict):
            return candidate, value
    return None, None


def warn_missing(path: Path, label: str, warnings: list[str]) -> None:
    if not path.exists():
        warnings.append(f"{label} missing: {path}")


def mark_chunk_cards(
    project: Path,
    progress: dict[str, object],
    batch: dict[str, object] | None,
    args: argparse.Namespace,
    now: str,
    warnings: list[str],
) -> int:
    chunks = progress.get("chunks", {})
    if not isinstance(chunks, dict):
        print("error: extraction_progress chunks section is malformed", file=sys.stderr)
        return -1

    update_batch_metadata(batch, args, now)
    target_chunk_ids: list[str] = []
    if batch:
        ids = batch.get("chunk_ids", [])
        if isinstance(ids, list):
            target_chunk_ids.extend(str(item) for item in ids if item)
    if args.chunk_id:
        target_chunk_ids.append(args.chunk_id)
    if not target_chunk_ids:
        print("error: no chunk targets found", file=sys.stderr)
        return -1

    changed = 0
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
            card = (
                args.chunk_card.resolve()
                if args.chunk_card and args.chunk_id == chunk_id
                else default_chunk_card(project, chunk_id)
            )
            record["chunk_card"] = str(card)
            warn_missing(card, f"chunk_card for {chunk_id}", warnings)
        changed += 1

    update_chapter_states(progress)
    return changed


def mark_chapter_cards(
    project: Path,
    progress: dict[str, object],
    batch: dict[str, object] | None,
    args: argparse.Namespace,
    now: str,
    warnings: list[str],
) -> int:
    chapters = progress.get("chapters", {})
    if not isinstance(chapters, dict):
        print("error: extraction_progress chapters section is malformed", file=sys.stderr)
        return -1

    update_batch_metadata(batch, args, now)
    target_chapter_ids: list[str] = []
    if batch:
        ids = batch.get("chapter_ids", [])
        if isinstance(ids, list):
            target_chapter_ids.extend(str(item) for item in ids if item)
    if args.chapter_id:
        target_chapter_ids.append(args.chapter_id)
    elif args.chunk_id:
        target_chapter_ids.append(args.chunk_id)
    if not target_chapter_ids:
        print("error: no chapter targets found", file=sys.stderr)
        return -1

    changed = 0
    single_target = len(set(target_chapter_ids)) == 1
    for chapter_id in sorted(set(target_chapter_ids)):
        chapter_key, record = find_chapter_record(chapters, chapter_id)
        if not chapter_key or not isinstance(record, dict):
            warnings.append(f"chapter not found in progress: {chapter_id}")
            continue
        record["updated_at"] = now
        if args.status == "done":
            record["status"] = "done"
            explicit_card = resolve_project_relative(project, args.chapter_card) if args.chapter_card else None
            card = explicit_card if explicit_card and single_target else default_chapter_card(project, chapter_key)
            record["chapter_card"] = safe_relative(card, project)
            warn_missing(card, f"chapter_card for {chapter_key}", warnings)
        elif args.status == "failed":
            record["status"] = "failed"
            record["error"] = args.error
        elif args.status == "skipped":
            record["status"] = "skipped"
        else:
            record["status"] = args.status
        changed += 1
    return changed


def mark_generic_batch(
    project: Path,
    batch: dict[str, object] | None,
    args: argparse.Namespace,
    now: str,
    warnings: list[str],
    stage: str,
) -> int:
    if not batch:
        print(f"error: {stage} updates require --batch-id", file=sys.stderr)
        return -1
    update_batch_metadata(batch, args, now)

    output = resolve_project_relative(project, args.output) if args.output else None
    if output:
        batch["output"] = safe_relative(output, project)
        if args.status == "done":
            warn_missing(output, "output", warnings)

    if stage == "volume_summaries":
        raw_output = str(batch.get("output", "") or "")
        if raw_output and args.status == "done":
            output_path = resolve_project_relative(project, raw_output)
            if output_path:
                warn_missing(output_path, "volume summary output", warnings)
    elif stage == "story_bible_patches":
        raw_patch = str(batch.get("patch_skeleton", "") or "")
        if raw_patch:
            patch_path = resolve_project_relative(project, raw_patch)
            if patch_path:
                warn_missing(patch_path, "patch_skeleton", warnings)
    return 1


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mark extraction progress entries.")
    parser.add_argument("--project", required=True, type=Path, help="Novel project root.")
    parser.add_argument("--batch-id", help="Batch id to mark.")
    parser.add_argument("--stage", default="", help="Stage for updates. Defaults to batch metadata when omitted.")
    parser.add_argument("--chunk-id", help="Single chunk id to mark.")
    parser.add_argument("--chapter-id", help="Single chapter id to mark for chapter_cards stage.")
    parser.add_argument("--chunk-card", type=Path, help="Chunk card path for a single chunk.")
    parser.add_argument("--chapter-card", type=Path, help="Chapter card path for a single chapter.")
    parser.add_argument("--output", type=Path, help="Output file for non-chunk batch stages.")
    parser.add_argument(
        "--status",
        required=True,
        choices=("done", "failed", "skipped", "processing", "queued"),
        help="New status.",
    )
    parser.add_argument("--error", default="", help="Error message for failed status.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    if not project.exists():
        print(f"error: project not found: {project}", file=sys.stderr)
        return 1
    progress_path = project / "imports" / "extraction_progress.yaml"
    if not progress_path.exists():
        print(f"error: extraction progress not found: {progress_path}", file=sys.stderr)
        return 1
    if not args.batch_id and not args.chunk_id and not args.chapter_id:
        print("error: provide --batch-id, --chunk-id, or --chapter-id", file=sys.stderr)
        return 1

    progress = parse_progress(progress_path)
    batches = progress.get("batches", {})
    if not isinstance(batches, dict):
        print("error: extraction_progress batches section is malformed", file=sys.stderr)
        return 1

    batch = None
    if args.batch_id:
        raw_batch = batches.get(args.batch_id)
        if not isinstance(raw_batch, dict):
            print(f"error: batch not found: {args.batch_id}", file=sys.stderr)
            return 1
        batch = raw_batch

    now = now_iso()
    warnings: list[str] = []
    stage = infer_stage(args, batch)

    if stage == "chunk_cards":
        changed = mark_chunk_cards(project, progress, batch, args, now, warnings)
        changed_label = "chunks"
    elif stage == "chapter_cards":
        changed = mark_chapter_cards(project, progress, batch, args, now, warnings)
        changed_label = "chapters"
    else:
        changed = mark_generic_batch(project, batch, args, now, warnings, stage)
        changed_label = "batches"

    if changed < 0:
        return 1

    project_meta = progress.get("project", {})
    if isinstance(project_meta, dict):
        project_meta["updated_at"] = now
    write_progress(progress_path, progress)
    print(f"Stage: {stage}")
    print(f"Updated {changed_label}: {changed}")
    for warning in warnings:
        print(f"warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
