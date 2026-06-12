#!/usr/bin/env python3
"""Create story-bible patch batch prompts without modifying canon."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _novel_utils import chapter_label_candidates, next_batch_id, now_iso, safe_relative, yaml_quote


def volume_label(volume: str) -> str:
    text = str(volume or "").strip()
    if not text:
        return ""
    if text.isdigit():
        return f"volume_{int(text):04d}"
    if text.startswith("volume_"):
        return text
    return "volume_" + text.replace(" ", "_")


def chapter_card(project: Path, chapter_id: str) -> Path | None:
    for candidate in chapter_label_candidates(chapter_id):
        path = project / "extracted" / "chapter_cards" / f"{candidate}.yaml"
        if path.exists():
            return path
    return None


def collect_source_files(project: Path, args: argparse.Namespace) -> list[Path]:
    sources: list[Path] = []
    wanted = {args.source} if args.source != "all" else {"chunk_cards", "chapter_cards", "volume_summaries"}
    if "chunk_cards" in wanted:
        if args.chapters:
            for chapter_id in args.chapters:
                for candidate in chapter_label_candidates(chapter_id):
                    sources.extend(sorted((project / "extracted" / "chunk_cards").glob(f"{candidate}_chunk_*.yaml")))
        else:
            sources.extend(sorted((project / "extracted" / "chunk_cards").glob("*.yaml")))
    if "chapter_cards" in wanted:
        if args.chapters:
            for chapter_id in args.chapters:
                card = chapter_card(project, chapter_id)
                if card:
                    sources.append(card)
        else:
            sources.extend(sorted((project / "extracted" / "chapter_cards").glob("*.yaml")))
    if "volume_summaries" in wanted:
        if args.volume:
            path = project / "extracted" / "volume_summaries" / f"{volume_label(args.volume)}.md"
            if path.exists():
                sources.append(path)
        else:
            sources.extend(sorted((project / "extracted" / "volume_summaries").glob("volume_*.md")))
    return list(dict.fromkeys(sources))


def render_patch_skeleton(batch_id: str, source_files: list[str]) -> str:
    return "\n".join(
        [
            'schema_version: "0.4"',
            f"patch_id: {yaml_quote('import_bible_patch_' + batch_id)}",
            'branch: "main"',
            "chapter: null",
            f"created_at: {yaml_quote(now_iso())}",
            'source_draft: "import batch"',
            'status: "pending"',
            "source_files:",
            *[f"  - {yaml_quote(path)}" for path in source_files],
            "updates:",
            "  characters: []",
            "  relationships: []",
            "  worldbuilding: []",
            "  locations: []",
            "  organizations: []",
            "  items: []",
            "  terms: []",
            "  timeline: []",
            "  foreshadowing_added: []",
            "  foreshadowing_paid_off: []",
            "  open_questions_added: []",
            "  hard_constraints_added: []",
            "  continuity_issues: []",
            "potential_conflicts: []",
            "requires_user_confirmation: []",
            'notes: "Import story bible patch candidate. Review before applying; do not directly overwrite canon."',
            "",
        ]
    )


def render_markdown(batch_id: str, source_files: list[str], patch_path: str) -> str:
    lines = [
        f"# Story Bible Patch Batch {batch_id}",
        "",
        f"- schema_version: `0.4`",
        f"- batch_id: `{batch_id}`",
        "- stage: `story_bible_patches`",
        f"- patch_skeleton: `{patch_path}`",
        "",
        "## Source Files",
        "",
    ]
    for path in source_files:
        lines.append(f"- `{path}`")
    lines.extend(
        [
            "",
            "## Codex Instructions",
            "",
            "- Read only the source files listed in this batch.",
            "- Do not read `raw_text/full_text.txt`.",
            "- Generate or fill the pending update patch skeleton.",
            "- Do not directly modify `canon/` or branch bible files.",
            "- Propose candidate updates for characters, relationships, worldbuilding, locations, organizations, items, terms, timeline, foreshadowing, and open questions.",
            "- Every important fact must include `source`, `status`, and `confidence`.",
            "- Keep uncertain or inferred content as `uncertain` or `inferred`.",
            "- Put conflicts in `potential_conflicts` and/or `imports/conflicts_found.md`.",
            "- Put major plot decisions in `requires_user_confirmation`.",
            "",
        ]
    )
    return "\n".join(lines)


def render_yaml(batch_id: str, source: str, source_files: list[str], patch_path: str) -> str:
    lines = [
        'schema_version: "0.4"',
        f"batch_id: {yaml_quote(batch_id)}",
        'stage: "story_bible_patches"',
        'status: "queued"',
        f"source: {yaml_quote(source)}",
        f"patch_skeleton: {yaml_quote(patch_path)}",
        "source_files:",
    ]
    for path in source_files:
        lines.append(f"  - {yaml_quote(path)}")
    lines.extend([f"created_at: {yaml_quote(now_iso())}", ""])
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a story-bible patch batch prompt.")
    parser.add_argument("--project", "--project-root", dest="project", required=True, type=Path)
    parser.add_argument("--source", choices=("chunk_cards", "chapter_cards", "volume_summaries", "all"), default="chapter_cards")
    parser.add_argument("--chapters", nargs="*", default=[])
    parser.add_argument("--volume", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    if not project.exists():
        print(f"error: project not found: {project}", file=sys.stderr)
        return 1
    source_files_abs = collect_source_files(project, args)
    if not source_files_abs:
        print("No eligible source files found.")
        return 0
    source_files = [safe_relative(path, project) for path in source_files_abs]
    batch_dir = project / "imports" / "batches"
    batch_id = next_batch_id(batch_dir)
    patch_path = project / "pending_updates" / f"import_bible_patch_{batch_id}.yaml"
    patch_rel = safe_relative(patch_path, project)
    md_path = batch_dir / f"{batch_id}_story_bible_patches.md"
    yaml_path = batch_dir / f"{batch_id}_story_bible_patches.yaml"
    print(f"Batch: {batch_id}")
    print(f"Stage: story_bible_patches")
    print(f"Source files: {len(source_files)}")
    for path in source_files:
        print(f"- {path}")
    if args.dry_run:
        return 0
    if (md_path.exists() or yaml_path.exists() or patch_path.exists()) and not args.force:
        print(f"error: output exists for {batch_id}. Use --force to overwrite.", file=sys.stderr)
        return 1
    batch_dir.mkdir(parents=True, exist_ok=True)
    patch_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_markdown(batch_id, source_files, patch_rel), encoding="utf-8")
    yaml_path.write_text(render_yaml(batch_id, args.source, source_files, patch_rel), encoding="utf-8")
    patch_path.write_text(render_patch_skeleton(batch_id, source_files), encoding="utf-8")
    print(f"Wrote: {md_path}")
    print(f"Wrote: {yaml_path}")
    print(f"Wrote: {patch_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
