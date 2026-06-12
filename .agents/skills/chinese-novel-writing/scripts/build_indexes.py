#!/usr/bin/env python3
"""Build lightweight navigation indexes from extracted cards and canon files."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from _novel_utils import now_iso, yaml_quote


INDEX_FILES = {
    "characters": "character_index.yaml",
    "locations": "location_index.yaml",
    "items": "item_index.yaml",
    "organizations": "organization_index.yaml",
    "events": "event_index.yaml",
    "foreshadowing": "foreshadowing_index.yaml",
    "terms": "term_index.yaml",
    "chapters": "chapter_index.yaml",
    "chunks": "chunk_index.yaml",
}


def clean_value(value: str) -> str:
    return value.strip().strip('"').strip("'")


def slug(value: str, prefix: str) -> str:
    text = re.sub(r"\s+", "_", value.strip())
    text = re.sub(r"[^\w\u4e00-\u9fff-]", "_", text)
    return text or prefix


def add_entry(index: dict[str, dict[str, object]], category: str, name: str, source: Path, project: Path) -> None:
    if not name:
        return
    entry_id = slug(name, category)
    entry = index.setdefault(
        entry_id,
        {
            "id": entry_id,
            "name": name,
            "aliases": [],
            "type": category,
            "sources": [],
            "chapters": [],
            "chunks": [],
            "last_seen": "",
            "status": "",
            "confidence": "",
            "notes": "",
        },
    )
    sources = entry.setdefault("sources", [])
    if isinstance(sources, list):
        rel = str(source.relative_to(project)) if source.is_relative_to(project) else str(source)
        if rel not in sources:
            sources.append(rel)


def scan_list_after_key(text: str, key: str) -> list[str]:
    lines = text.splitlines()
    values: list[str] = []
    in_section = False
    for line in lines:
        if not in_section:
            if line.strip() == f"{key}:":
                in_section = True
            continue
        if line and not line.startswith(" "):
            break
        stripped = line.strip()
        if stripped.startswith("- "):
            item = clean_value(stripped[2:])
            if item and ":" not in item:
                values.append(item)
        elif stripped.startswith("name:"):
            values.append(clean_value(stripped.split(":", 1)[1]))
        elif stripped.startswith("id:"):
            values.append(clean_value(stripped.split(":", 1)[1]))
    return values


def scan_yaml_file(path: Path, project: Path, index: dict[str, dict[str, dict[str, object]]]) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    for section, category in [
        ("characters", "characters"),
        ("locations", "locations"),
        ("items", "items"),
        ("organizations", "organizations"),
        ("terms", "terms"),
        ("timeline_events", "events"),
        ("foreshadowing", "foreshadowing"),
        ("foreshadowing_candidates", "foreshadowing"),
    ]:
        for value in scan_list_after_key(text, section):
            add_entry(index[category], category, value, path, project)

    if "chapter_id:" in text:
        match = re.search(r"^\s*chapter_id:\s*(.+)$", text, flags=re.MULTILINE)
        if match:
            add_entry(index["chapters"], "chapters", clean_value(match.group(1)), path, project)
    if "chunk_id:" in text:
        match = re.search(r"^\s*chunk_id:\s*(.+)$", text, flags=re.MULTILINE)
        if match:
            add_entry(index["chunks"], "chunks", clean_value(match.group(1)), path, project)


def scan_canon(project: Path, index: dict[str, dict[str, dict[str, object]]]) -> None:
    canon_map = {
        "characters": project / "canon" / "characters.yaml",
        "locations": project / "canon" / "locations.yaml",
        "items": project / "canon" / "items.yaml",
        "organizations": project / "canon" / "organizations.yaml",
        "terms": project / "canon" / "terms.yaml",
    }
    for category, path in canon_map.items():
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(r"^\s{2}([\w\u4e00-\u9fff-]+):\s*$", text, flags=re.MULTILINE):
            add_entry(index[category], category, match.group(1), path, project)
        for value in scan_list_after_key(text, category):
            add_entry(index[category], category, value, path, project)


def render_index(root_key: str, entries: dict[str, dict[str, object]]) -> str:
    lines = [f"{root_key}:"]
    if not entries:
        lines.append("  []")
        return "\n".join(lines) + "\n"
    for entry in sorted(entries.values(), key=lambda item: str(item.get("id", ""))):
        lines.append(f"  - id: {yaml_quote(entry.get('id', ''))}")
        lines.append(f"    name: {yaml_quote(entry.get('name', ''))}")
        lines.append("    aliases: []")
        lines.append(f"    type: {yaml_quote(entry.get('type', ''))}")
        lines.append("    sources:")
        sources = entry.get("sources", [])
        if isinstance(sources, list) and sources:
            for source in sources:
                lines.append(f"      - {yaml_quote(source)}")
        else:
            lines.append("      []")
        lines.append("    chapters: []")
        lines.append("    chunks: []")
        lines.append(f"    last_seen: {yaml_quote(entry.get('last_seen', ''))}")
        lines.append(f"    status: {yaml_quote(entry.get('status', ''))}")
        lines.append(f"    confidence: {yaml_quote(entry.get('confidence', ''))}")
        lines.append(f"    notes: {yaml_quote(entry.get('notes', ''))}")
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build navigation indexes from extracted cards and canon.")
    parser.add_argument("--project", required=True, type=Path, help="Novel project root.")
    parser.add_argument("--source", choices=("extracted", "canon", "all"), default="all")
    parser.add_argument("--force", action="store_true", help="Overwrite index files.")
    parser.add_argument("--dry-run", action="store_true", help="Print summary without writing.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    if not project.exists():
        print(f"error: project not found: {project}", file=sys.stderr)
        return 1
    index: dict[str, dict[str, dict[str, object]]] = {key: {} for key in INDEX_FILES}

    if args.source in {"extracted", "all"}:
        for directory in [project / "extracted" / "chunk_cards", project / "extracted" / "chapter_cards"]:
            if directory.exists():
                for path in directory.glob("*.yaml"):
                    scan_yaml_file(path, project, index)
    if args.source in {"canon", "all"}:
        scan_canon(project, index)

    print(f"Generated indexes at {now_iso()}:")
    for category, entries in index.items():
        print(f"- {category}: {len(entries)} entries")
    if args.dry_run:
        return 0

    index_dir = project / "indexes"
    index_dir.mkdir(parents=True, exist_ok=True)
    for category, file_name in INDEX_FILES.items():
        target = index_dir / file_name
        output = target if args.force or not target.exists() else target.with_name(target.stem + ".pending.yaml")
        output.write_text(render_index(category, index[category]), encoding="utf-8")
        print(f"Wrote: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

