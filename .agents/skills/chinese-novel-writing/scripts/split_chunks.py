#!/usr/bin/env python3
"""Split chapter files into overlapping chunks for long-form import."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def infer_paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    if args.project:
        project = args.project.resolve()
        chapter_dir = project / "raw_text" / "chapters"
        output = project / "chunks"
        manifest = project / "imports" / "chunk_manifest.yaml"
    else:
        if not args.chapter_dir or not args.output:
            raise ValueError("provide either --project or both --chapter-dir and --output")
        chapter_dir = args.chapter_dir.resolve()
        output = args.output.resolve()
        manifest = args.manifest.resolve() if args.manifest else output / "chunk_manifest.yaml"
    return chapter_dir, output, manifest


def split_text(text: str, chunk_size: int, overlap: int) -> list[tuple[int, int, str]]:
    if chunk_size <= 0:
        raise ValueError("--chunk-size must be positive")
    if overlap < 0:
        raise ValueError("--overlap must not be negative")
    if overlap >= chunk_size:
        raise ValueError("--overlap must be smaller than --chunk-size")

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    chunks: list[tuple[int, int, str]] = []
    start = 0
    length = len(normalized)
    while start < length:
        hard_end = min(start + chunk_size, length)
        end = hard_end
        if hard_end < length:
            paragraph_break = normalized.rfind("\n\n", start + max(1, chunk_size // 2), hard_end)
            line_break = normalized.rfind("\n", start + max(1, chunk_size // 2), hard_end)
            sentence_break = max(
                normalized.rfind(mark, start + max(1, chunk_size // 2), hard_end)
                for mark in ("\u3002", "\uff1b", "\uff01", "\uff1f")
            )
            boundary = max(paragraph_break, line_break, sentence_break)
            if boundary > start:
                end = boundary + 1
        chunk_text = normalized[start:end].strip()
        if chunk_text:
            chunks.append((start, end, chunk_text))
        if end >= length:
            break
        start = max(0, end - overlap)
    return chunks


def chapter_id_from_path(path: Path, fallback: int) -> str:
    stem = path.stem
    if stem.startswith("chapter_"):
        return stem
    return f"chapter_{fallback:04d}"


def write_manifest(manifest: Path, records: list[dict[str, object]], warnings: list[str]) -> None:
    lines = [
        f"created_at: {yaml_quote(datetime.now(timezone.utc).isoformat(timespec='seconds'))}",
        f"chunk_count: {len(records)}",
        "chunks:",
    ]
    for record in records:
        lines.extend(
            [
                f"  - chunk_id: {yaml_quote(str(record['chunk_id']))}",
                f"    chapter_id: {yaml_quote(str(record['chapter_id']))}",
                f"    source_file: {yaml_quote(str(record['source_file']))}",
                f"    output_file: {yaml_quote(str(record['output_file']))}",
                f"    start_char: {record['start_char']}",
                f"    end_char: {record['end_char']}",
                f"    char_count: {record['char_count']}",
                f"    overlap_prev: {record['overlap_prev']}",
                f"    overlap_next: {record['overlap_next']}",
            ]
        )
    lines.append("warnings:")
    if warnings:
        for warning in warnings:
            lines.append(f"  - {yaml_quote(warning)}")
    else:
        lines.append("  []")
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split chapter txt files into overlapping chunks.")
    parser.add_argument("--project", type=Path, help="Novel project root.")
    parser.add_argument("--chapter-dir", type=Path, help="Directory containing chapter_*.txt files.")
    parser.add_argument("--output", type=Path, help="Output directory for chunk txt files.")
    parser.add_argument("--manifest", type=Path, help="Output chunk_manifest.yaml path.")
    parser.add_argument("--chunk-size", type=int, default=6000, help="Target chunk size in characters.")
    parser.add_argument("--overlap", type=int, default=500, help="Overlap between adjacent chunks.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing chunk files.")
    parser.add_argument("--clean", action="store_true", help="Delete old *_chunk_*.txt files before splitting. Requires --force.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        chapter_dir, output, manifest = infer_paths(args)
        if not chapter_dir.is_dir():
            raise FileNotFoundError(f"chapter directory not found: {chapter_dir}")
        output.mkdir(parents=True, exist_ok=True)
        if args.clean and not args.force:
            raise ValueError("--clean requires --force")
        if args.clean:
            removed = 0
            for old_chunk in output.glob("*_chunk_*.txt"):
                if old_chunk.is_file():
                    old_chunk.unlink()
                    removed += 1
            if removed:
                print(f"Cleaned old chunk files: {removed}")
        if any(output.glob("*_chunk_*.txt")) and not args.force:
            raise FileExistsError(f"chunk files already exist in {output}. Use --force to overwrite.")

        records: list[dict[str, object]] = []
        warnings: list[str] = []
        chapter_files = sorted(path for path in chapter_dir.glob("*.txt") if path.is_file())
        if not chapter_files:
            raise FileNotFoundError(f"no .txt chapter files found in {chapter_dir}")

        for chapter_number, chapter_file in enumerate(chapter_files, start=1):
            text = chapter_file.read_text(encoding="utf-8", errors="replace")
            chapter_id = chapter_id_from_path(chapter_file, chapter_number)
            pieces = split_text(text, args.chunk_size, args.overlap)
            if not pieces:
                warnings.append(f"empty chapter skipped: {chapter_file}")
                continue
            for chunk_number, (start, end, chunk_text) in enumerate(pieces, start=1):
                chunk_id = f"{chapter_id}_chunk_{chunk_number:04d}"
                chunk_path = output / f"{chunk_id}.txt"
                if chunk_path.exists() and not args.force:
                    raise FileExistsError(f"chunk file exists: {chunk_path}")
                chunk_path.write_text(chunk_text.rstrip() + "\n", encoding="utf-8")
                records.append(
                    {
                        "chunk_id": chunk_id,
                        "chapter_id": chapter_id,
                        "source_file": chapter_file,
                        "output_file": chunk_path,
                        "start_char": start,
                        "end_char": end,
                        "char_count": len(chunk_text),
                        "overlap_prev": args.overlap if chunk_number > 1 else 0,
                        "overlap_next": args.overlap if end < len(text) else 0,
                    }
                )
        write_manifest(manifest, records, warnings)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {len(records)} chunks to: {output}")
    print(f"Wrote manifest: {manifest}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
