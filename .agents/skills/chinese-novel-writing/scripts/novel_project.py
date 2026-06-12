#!/usr/bin/env python3
"""Compatibility wrapper exposing helper scripts as subcommands."""

from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path


SCRIPT_MAP = {
    "init": "init_project.py",
    "split-import": "split_chapters.py",
    "split-chunks": "split_chunks.py",
    "new-branch": "create_branch.py",
    "create-function-card": "create_chapter_function_card.py",
    "build-context-pack": "build_context_pack.py",
    "create-patch": "create_patch.py",
    "validate": "validate_project.py",
}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run chinese-novel-writing project helper subcommands."
    )
    parser.add_argument("command", choices=sorted(SCRIPT_MAP))
    parser.add_argument("args", nargs=argparse.REMAINDER)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    script_path = Path(__file__).resolve().parent / SCRIPT_MAP[args.command]
    sys.argv = [str(script_path), *args.args]
    try:
        runpy.run_path(str(script_path), run_name="__main__")
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
