#!/usr/bin/env python3
"""Initialize imports/extraction_progress.yaml from chunk_manifest.yaml."""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

from _novel_utils import now_iso, parse_mapping_list, safe_relative, write_progress


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize extraction progress from chunk_manifest.yaml.")
    parser.add_argument("--project", required=True, type=Path, help="Novel project root.")
    parser.add_argument("--manifest", type=Path, help="Optional chunk_manifest.yaml path.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing extraction_progress.yaml.")
    parser.add_argument("--batch-size", type=int, default=10, help="Default batch size to record.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    manifest = args.manifest.resolve() if args.manifest else project / "imports" / "chunk_manifest.yaml"
    output = project / "imports" / "extraction_progress.yaml"
    if not project.exists():
        print(f"error: project not found: {project}", file=sys.stderr)
        return 1
    if not manifest.exists():
        print(f"error: chunk manifest not found: {manifest}", file=sys.stderr)
        return 1
    if output.exists() and not args.force:
        print(f"error: extraction progress exists: {output}. Use --force to overwrite.", file=sys.stderr)
        return 1

    chunks = parse_mapping_list(manifest, "chunks")
    if not chunks:
        print(f"error: no chunks found in manifest: {manifest}", file=sys.stderr)
        return 1

    now = now_iso()
    chapter_chunks: dict[str, list[str]] = defaultdict(list)
    chunk_map: dict[str, dict[str, object]] = {}
    for record in chunks:
        chunk_id = str(record.get("chunk_id", "")).strip()
        chapter_id = str(record.get("chapter_id", "")).strip()
        if not chunk_id:
            continue
        chapter_chunks[chapter_id].append(chunk_id)
        chunk_map[chunk_id] = {
            "chapter_id": chapter_id,
            "source_file": str(record.get("source_file", "")),
            "output_file": str(record.get("output_file", "")),
            "status": "pending",
            "batch_id": "",
            "chunk_card": "",
            "error": "",
            "updated_at": now,
        }

    chapters = {
        chapter_id: {
            "status": "pending",
            "chunk_ids": chunk_ids,
            "chapter_card": "",
            "updated_at": now,
        }
        for chapter_id, chunk_ids in sorted(chapter_chunks.items())
    }
    data: dict[str, object] = {
        "project": {
            "name": project.name,
            "source_manifest": safe_relative(manifest, project),
            "created_at": now,
            "updated_at": now,
        },
        "settings": {
            "batch_size": args.batch_size,
            "active_stage": "chunk_cards",
            "stages": ["chunk_cards", "chapter_cards", "volume_summaries", "story_bible_patches", "indexes"],
        },
        "chunks": dict(sorted(chunk_map.items())),
        "chapters": chapters,
        "batches": {},
    }
    write_progress(output, data)
    print(f"Initialized extraction progress: {output}")
    print(f"Chunks: {len(chunk_map)}")
    print(f"Chapters: {len(chapters)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

