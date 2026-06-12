#!/usr/bin/env python3
"""Split a raw Chinese novel text file into chapter files."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


CHAPTER_RE = re.compile(
    r"^[ \t]*(第[零〇一二三四五六七八九十百千万\d]{1,10}\s*[章节回卷]"
    r"|卷[零〇一二三四五六七八九十百千万\d]{1,10}"
    r"|[零〇一二三四五六七八九十百千万\d]{1,10}\s*卷"
    r"|序章|楔子|番外(?:[零〇一二三四五六七八九十百千万\d]+)?)"
    r"(?:[ \t:：、.-].*)?$",
    re.MULTILINE,
)


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", b"", 0, 1, "could not decode as utf-8 or gb18030")


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def find_chapters(text: str) -> list[tuple[str, str]]:
    matches = list(CHAPTER_RE.finditer(text))
    chapters: list[tuple[str, str]] = []
    if not matches:
        stripped = text.strip()
        return [("全文", stripped)] if stripped else []

    preface = text[: matches[0].start()].strip()
    if preface:
        chapters.append(("导入前置文本", preface))

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        title = match.group(0).strip()
        chapters.append((title, block))
    return chapters


def write_manifest(
    manifest_path: Path,
    source: Path,
    output: Path,
    records: list[dict[str, object]],
    warnings: list[str],
) -> None:
    lines = [
        f"source_file: {yaml_quote(str(source))}",
        f"created_at: {yaml_quote(datetime.now(timezone.utc).isoformat(timespec='seconds'))}",
        f"chapter_output: {yaml_quote(str(output))}",
        f"chapter_count: {len(records)}",
        "chapters:",
    ]
    for record in records:
        lines.extend(
            [
                f"  - id: {yaml_quote(str(record['id']))}",
                f"    title: {yaml_quote(str(record['title']))}",
                f"    file: {yaml_quote(str(record['file']))}",
                f"    char_count: {record['char_count']}",
                f"    warning_count: {record['warning_count']}",
            ]
        )
    lines.append("warnings:")
    for warning in warnings:
        lines.append(f"  - {yaml_quote(warning)}")
    if not warnings:
        lines.append("  []")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def infer_project_root(output: Path) -> Path | None:
    parts = [part.lower() for part in output.parts]
    if len(parts) >= 2 and parts[-2:] == ["raw_text", "chapters"]:
        return output.parents[1]
    return None


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split a raw Chinese txt novel into chapter files."
    )
    parser.add_argument("--input", required=True, type=Path, help="Source txt file.")
    parser.add_argument(
        "--output", required=True, type=Path, help="Output directory for chapter files."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Optional import_manifest.yaml path. Defaults to project imports/ when possible.",
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing chapter files."
    )
    parser.add_argument(
        "--long-chapter-threshold",
        type=int,
        default=20000,
        help="Character count that triggers a long-chapter warning.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    source = args.input.resolve()
    output = args.output.resolve()

    if not source.exists():
        print(f"error: input file not found: {source}", file=sys.stderr)
        return 1
    if output.exists() and any(output.glob("chapter_*.txt")) and not args.force:
        print(
            f"error: chapter files already exist in {output}. Use --force to overwrite.",
            file=sys.stderr,
        )
        return 1

    try:
        text = normalize_newlines(read_text(source))
        chapters = find_chapters(text)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not chapters:
        print("error: source text is empty after basic normalization.", file=sys.stderr)
        return 1

    output.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    title_counts = Counter(title for title, _ in chapters)
    for title, count in title_counts.items():
        if count > 1:
            warnings.append(f"疑似重复章节标题：{title} ({count} 次)")

    records: list[dict[str, object]] = []
    for number, (title, body) in enumerate(chapters, start=1):
        file_name = f"chapter_{number:04d}.txt"
        file_path = output / file_name
        if file_path.exists() and not args.force:
            print(f"error: output file exists: {file_path}", file=sys.stderr)
            return 1
        body_warnings = []
        content_without_title = body.split("\n", 1)[1].strip() if "\n" in body else ""
        if not content_without_title and title != "全文":
            body_warnings.append(f"疑似空章节：{title}")
        if len(body) > args.long_chapter_threshold:
            body_warnings.append(f"疑似超长章节：{title} ({len(body)} 字符)")
        warnings.extend(body_warnings)
        file_path.write_text(body.rstrip() + "\n", encoding="utf-8")
        records.append(
            {
                "id": f"chapter_{number:04d}",
                "title": title,
                "file": str(file_path),
                "char_count": len(body),
                "warning_count": len(body_warnings),
            }
        )

    project_root = infer_project_root(output)
    if args.manifest:
        manifest_path = args.manifest.resolve()
    elif project_root:
        manifest_path = project_root / "imports" / "import_manifest.yaml"
        full_text_path = project_root / "raw_text" / "full_text.txt"
        if not full_text_path.exists() or args.force:
            full_text_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, full_text_path)
    else:
        manifest_path = output / "import_manifest.yaml"

    write_manifest(manifest_path, source, output, records, warnings)
    print(f"Split {len(records)} chapters into: {output}")
    print(f"Wrote manifest: {manifest_path}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

