#!/usr/bin/env python3
"""Create a Chinese novel project from the bundled template."""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE_DIR = SKILL_DIR / "templates" / "novel_project"


def quote_yaml(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def update_config(path: Path, project_name: str) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    replacements = {
        "project_name": quote_yaml(project_name),
        "created_at": quote_yaml(now),
        "updated_at": quote_yaml(now),
    }
    lines = path.read_text(encoding="utf-8").splitlines()
    updated = []
    seen = set()
    for line in lines:
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]
        if ":" in stripped:
            key = stripped.split(":", 1)[0].strip()
            if key in replacements:
                updated.append(f"{indent}{key}: {replacements[key]}")
                seen.add(key)
                continue
        updated.append(line)
    for key, value in replacements.items():
        if key not in seen:
            updated.append(f"{key}: {value}")
    path.write_text("\n".join(updated) + "\n", encoding="utf-8")


def copy_template(output: Path, force: bool) -> None:
    if not TEMPLATE_DIR.exists():
        raise FileNotFoundError(f"Template directory not found: {TEMPLATE_DIR}")

    if output.exists():
        if not force:
            raise FileExistsError(
                f"Output already exists: {output}. Use --force to replace it."
            )
        if output.is_file():
            output.unlink()
        else:
            shutil.rmtree(output)

    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(TEMPLATE_DIR, output)


def ensure_directories(project: Path) -> None:
    required = [
        "raw_text/chapters",
        "chunks",
        "imports",
        "extracted/chunk_cards",
        "extracted/chapter_cards",
        "extracted/volume_summaries",
        "canon",
        "branches/main/chapter_summaries",
        "branches/main/chapter_function_cards",
        "branches/main/drafts",
        "branches/main/reviews",
        "indexes",
        "pending_updates",
        "context_packs",
        "drafts",
        "reviews",
    ]
    for rel in required:
        (project / rel).mkdir(parents=True, exist_ok=True)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a Chinese novel project from templates."
    )
    parser.add_argument("--name", required=True, help="Project name written to config.")
    parser.add_argument(
        "--output", required=True, type=Path, help="Project directory to create."
    )
    parser.add_argument(
        "--force", action="store_true", help="Replace the output directory if it exists."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    output = args.output.resolve()
    try:
        copy_template(output, args.force)
        ensure_directories(output)
        update_config(output / "project_config.yaml", args.name)
    except Exception as exc:  # noqa: BLE001 - CLI should show clear user errors.
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Created novel project: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
