#!/usr/bin/env python3
"""Create volume-summary batch files from chapter cards."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _novel_utils import chapter_label_candidates, chapter_number, next_batch_id, now_iso, safe_relative, yaml_quote


def chapter_card_for(project: Path, chapter_id: str) -> Path | None:
    for candidate in chapter_label_candidates(chapter_id):
        path = project / "extracted" / "chapter_cards" / f"{candidate}.yaml"
        if path.exists():
            return path
    return None


def available_chapter_ids(project: Path) -> list[str]:
    cards = sorted((project / "extracted" / "chapter_cards").glob("*.yaml"))
    return [path.stem for path in cards]


def selected_chapters(project: Path, args: argparse.Namespace) -> tuple[list[str], list[str]]:
    if args.chapters:
        requested = args.chapters
    else:
        requested = available_chapter_ids(project)
        start = chapter_number(args.from_chapter) if args.from_chapter else None
        end = chapter_number(args.to_chapter) if args.to_chapter else None
        if start is not None or end is not None:
            filtered = []
            for chapter_id in requested:
                number = chapter_number(chapter_id)
                if number is None:
                    continue
                if start is not None and number < start:
                    continue
                if end is not None and number > end:
                    continue
                filtered.append(chapter_id)
            requested = filtered
        if args.batch_size:
            requested = requested[: args.batch_size]
    found: list[str] = []
    missing: list[str] = []
    for chapter_id in requested:
        if chapter_card_for(project, chapter_id):
            found.append(chapter_id)
        else:
            missing.append(chapter_id)
    return found, missing


def volume_label(volume: str) -> str:
    text = str(volume or "1").strip()
    if text.isdigit():
        return f"volume_{int(text):04d}"
    if text.startswith("volume_"):
        return text
    return "volume_" + text.replace(" ", "_")


def render_markdown(batch_id: str, project: Path, volume_id: str, chapters: list[str], missing: list[str]) -> str:
    lines = [
        f"# Volume Summary Batch {batch_id}",
        "",
        f"- schema_version: `0.4`",
        f"- batch_id: `{batch_id}`",
        "- stage: `volume_summaries`",
        f"- volume: `{volume_id}`",
        "",
        "## Source Chapter Cards",
        "",
    ]
    for chapter_id in chapters:
        card = chapter_card_for(project, chapter_id)
        if card:
            lines.append(f"- `{safe_relative(card, project)}`")
    if missing:
        lines.extend(["", "## Missing Chapter Cards", ""])
        for chapter_id in missing:
            lines.append(f"- `{chapter_id}`")
    lines.extend(
        [
            "",
            "## Codex Instructions",
            "",
            "- Read only the chapter cards listed in this batch.",
            "- Do not read `raw_text/full_text.txt`.",
            "- Do not read raw chapter files or the whole novel.",
            f"- Generate `extracted/volume_summaries/{volume_id}.md`.",
            "- Summarize main plot movement, character states, relationship changes, worldbuilding additions, foreshadowing, timeline, open questions, and style notes.",
            "",
            "## Required Output Template",
            "",
            f"# Volume Summary {volume_id}",
            "",
            "## Source Chapter Cards",
            "",
            "## Arc Summary",
            "",
            "## Major Plot Movement",
            "",
            "## Character State Changes",
            "",
            "## Relationship Changes",
            "",
            "## Worldbuilding Additions",
            "",
            "## Timeline",
            "",
            "## Foreshadowing",
            "- added",
            "- reinforced",
            "- paid_off",
            "- still_open",
            "",
            "## Open Questions",
            "",
            "## Continuation Constraints",
            "",
            "## Style Notes",
            "",
        ]
    )
    return "\n".join(lines)


def render_yaml(batch_id: str, volume_id: str, chapters: list[str], missing: list[str]) -> str:
    lines = [
        'schema_version: "0.4"',
        f"batch_id: {yaml_quote(batch_id)}",
        'stage: "volume_summaries"',
        'status: "queued"',
        f"volume: {yaml_quote(volume_id)}",
        "chapter_ids:",
    ]
    for chapter_id in chapters:
        lines.append(f"  - {yaml_quote(chapter_id)}")
    lines.append("missing_chapter_cards:")
    if missing:
        for chapter_id in missing:
            lines.append(f"  - {yaml_quote(chapter_id)}")
    else:
        lines.append("  []")
    lines.extend([f"created_at: {yaml_quote(now_iso())}", f"output: {yaml_quote('extracted/volume_summaries/' + volume_id + '.md')}", ""])
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a volume-summary batch from chapter cards.")
    parser.add_argument("--project", "--project-root", dest="project", required=True, type=Path)
    parser.add_argument("--volume", default="1")
    parser.add_argument("--chapters", nargs="*", default=[])
    parser.add_argument("--from-chapter", default="")
    parser.add_argument("--to-chapter", default="")
    parser.add_argument("--batch-size", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    if not project.exists():
        print(f"error: project not found: {project}", file=sys.stderr)
        return 1
    volume_id = volume_label(args.volume)
    chapters, missing = selected_chapters(project, args)
    if not chapters:
        print("No eligible chapter cards found.")
        if missing:
            print("Missing chapter cards:")
            for chapter_id in missing:
                print(f"- {chapter_id}")
        return 0
    batch_dir = project / "imports" / "batches"
    batch_id = next_batch_id(batch_dir)
    md_path = batch_dir / f"{batch_id}_volume_summaries.md"
    yaml_path = batch_dir / f"{batch_id}_volume_summaries.yaml"
    print(f"Batch: {batch_id}")
    print(f"Stage: volume_summaries")
    print(f"Volume: {volume_id}")
    print(f"Chapters: {len(chapters)}")
    for chapter_id in chapters:
        print(f"- {chapter_id}")
    for chapter_id in missing:
        print(f"warning: missing chapter card: {chapter_id}")
    if args.dry_run:
        return 0
    if (md_path.exists() or yaml_path.exists()) and not args.force:
        print(f"error: batch files exist. Use --force to overwrite: {batch_id}", file=sys.stderr)
        return 1
    batch_dir.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_markdown(batch_id, project, volume_id, chapters, missing), encoding="utf-8")
    yaml_path.write_text(render_yaml(batch_id, volume_id, chapters, missing), encoding="utf-8")
    print(f"Wrote: {md_path}")
    print(f"Wrote: {yaml_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
