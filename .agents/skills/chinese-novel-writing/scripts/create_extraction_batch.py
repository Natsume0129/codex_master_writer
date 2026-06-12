#!/usr/bin/env python3
"""Create the next extraction batch from extraction_progress.yaml."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from _novel_utils import now_iso, parse_progress, safe_relative, write_progress, yaml_quote


def next_batch_id(batches: dict[str, object]) -> str:
    highest = 0
    for batch_id in batches:
        match = re.search(r"batch_(\d+)", batch_id)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"batch_{highest + 1:04d}"


def render_batch_markdown(batch_id: str, stage: str, records: list[tuple[str, dict[str, object]]]) -> str:
    lines = [
        f"# Extraction Batch {batch_id}",
        "",
        f"- batch_id: `{batch_id}`",
        f"- stage: `{stage}`",
        "",
        "## Chunks",
        "",
    ]
    for chunk_id, record in records:
        lines.extend(
            [
                f"### {chunk_id}",
                "",
                f"- chapter_id: `{record.get('chapter_id', '')}`",
                f"- source_file: `{record.get('source_file', '')}`",
                f"- output_file: `{record.get('output_file', '')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Codex Instructions",
            "",
            "- Use `references/extraction_prompts.md`.",
            "- Read only the chunk files listed in this batch.",
            "- Generate `extracted/chunk_cards/<chunk_id>.yaml` for each chunk.",
            "- Every fact must include `source`, `status`, and `confidence`.",
            "- Do not read `raw_text/full_text.txt`.",
            "- Do not load the whole novel into context.",
            "- Do not write inferred content as `confirmed`.",
            "- Do not directly modify canon; use pending updates for proposed changes.",
            "",
        ]
    )
    return "\n".join(lines)


def render_batch_yaml(batch_id: str, stage: str, chunk_ids: list[str]) -> str:
    lines = [
        f"batch_id: {yaml_quote(batch_id)}",
        f"stage: {yaml_quote(stage)}",
        'status: "queued"',
        "chunk_ids:",
    ]
    for chunk_id in chunk_ids:
        lines.append(f"  - {yaml_quote(chunk_id)}")
    lines.extend(
        [
            f"created_at: {yaml_quote(now_iso())}",
            'instructions: "Read only listed chunks; use references/extraction_prompts.md; facts require source/status/confidence."',
            "outputs_expected:",
            '  - "extracted/chunk_cards/*.yaml"',
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create the next extraction batch.")
    parser.add_argument("--project", required=True, type=Path, help="Novel project root.")
    parser.add_argument("--stage", default="chunk_cards", help="Extraction stage.")
    parser.add_argument("--batch-size", type=int, default=10, help="Maximum chunks in the batch.")
    parser.add_argument("--retry-failed", action="store_true", help="Include failed chunks for retry.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing batch files.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned batch without writing files.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    progress_path = project / "imports" / "extraction_progress.yaml"
    if not progress_path.exists():
        print(f"error: extraction progress not found: {progress_path}", file=sys.stderr)
        return 1
    progress = parse_progress(progress_path)
    chunks = progress.get("chunks", {})
    batches = progress.get("batches", {})
    if not isinstance(chunks, dict) or not isinstance(batches, dict):
        print("error: invalid extraction_progress.yaml", file=sys.stderr)
        return 1

    allowed = {"pending"} | ({"failed"} if args.retry_failed else set())
    selected: list[tuple[str, dict[str, object]]] = []
    for chunk_id, record in chunks.items():
        if not isinstance(record, dict):
            continue
        if str(record.get("status", "")) in allowed:
            selected.append((str(chunk_id), record))
        if len(selected) >= args.batch_size:
            break
    if not selected:
        print("No eligible chunks found.")
        return 0

    batch_id = next_batch_id(batches)
    chunk_ids = [chunk_id for chunk_id, _ in selected]
    batch_dir = project / "imports" / "batches"
    md_path = batch_dir / f"{batch_id}_{args.stage}.md"
    yaml_path = batch_dir / f"{batch_id}_{args.stage}.yaml"

    print(f"Batch: {batch_id}")
    print(f"Stage: {args.stage}")
    print(f"Chunks: {len(chunk_ids)}")
    if args.dry_run:
        for chunk_id in chunk_ids:
            print(f"- {chunk_id}")
        return 0
    if (md_path.exists() or yaml_path.exists()) and not args.force:
        print(f"error: batch files exist. Use --force to overwrite: {batch_id}", file=sys.stderr)
        return 1

    batch_dir.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_batch_markdown(batch_id, args.stage, selected), encoding="utf-8")
    yaml_path.write_text(render_batch_yaml(batch_id, args.stage, chunk_ids), encoding="utf-8")

    now = now_iso()
    for chunk_id, record in selected:
        record["status"] = "queued"
        record["batch_id"] = batch_id
        record["updated_at"] = now
    batches[batch_id] = {
        "stage": args.stage,
        "status": "queued",
        "chunk_ids": chunk_ids,
        "created_at": now,
        "completed_at": "",
        "notes": "",
    }
    project_meta = progress.get("project", {})
    if isinstance(project_meta, dict):
        project_meta["updated_at"] = now
    write_progress(progress_path, progress)
    print(f"Wrote: {md_path}")
    print(f"Wrote: {yaml_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

