#!/usr/bin/env python3
"""Run deterministic acceptance checks for chinese-novel-writing."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

from _novel_utils import now_iso, safe_relative, yaml_quote


RAW_MARKER = "SYNTHETIC_RAW_FULL_TEXT_MARKER_DO_NOT_COPY"


def resolve_repo_root(raw: Path) -> Path:
    return raw.resolve()


def ensure_inside(root: Path, target: Path) -> None:
    target_resolved = target.resolve()
    root_resolved = root.resolve()
    try:
        target_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"refusing to operate outside repo root: {target_resolved}") from exc


def remove_tree_if_allowed(root: Path, target: Path) -> None:
    if not target.exists():
        return
    ensure_inside(root, target)
    shutil.rmtree(target)


def file_hash(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def snapshot(paths: list[Path], root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for base in paths:
        if not base.exists():
            continue
        for path in sorted(item for item in base.rglob("*") if item.is_file()):
            result[safe_relative(path, root)] = file_hash(path)
    return result


def run_command(repo_root: Path, command: list[str]) -> dict[str, object]:
    completed = subprocess.run(  # noqa: S603
        command,
        cwd=repo_root,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "command": " ".join(command),
        "exit_code": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
    }


def append_run(
    runs: list[dict[str, object]],
    repo_root: Path,
    command: list[str],
    failures: list[str],
    continue_on_failure: bool = True,
) -> None:
    result = run_command(repo_root, command)
    runs.append(result)
    if result["exit_code"] != 0:
        failures.append(f"command failed ({result['exit_code']}): {result['command']}")
        if not continue_on_failure:
            raise RuntimeError(str(result["command"]))


def command_lines(runs: list[dict[str, object]]) -> str:
    if not runs:
        return "- None"
    return "\n".join(
        f"- `{item['command']}` -> exit `{item['exit_code']}`" for item in runs
    )


def file_lines(paths: list[Path], repo_root: Path) -> str:
    existing = [path for path in paths if path.exists()]
    if not existing:
        return "- None"
    return "\n".join(f"- `{safe_relative(path, repo_root)}`" for path in existing)


def bullet(values: list[str]) -> str:
    return "\n".join(f"- {value}" for value in values) if values else "- None"


def render_report(
    repo_root: Path,
    project: Path,
    runs: list[dict[str, object]],
    files: list[Path],
    warnings: list[str],
    failures: list[str],
    raw_marker_found: bool,
    pollution_failures: list[str],
) -> str:
    status = "fail" if failures or pollution_failures or raw_marker_found else ("warn" if warnings else "pass")
    return f"""---
schema_version: {yaml_quote("0.7")}
report_type: {yaml_quote("acceptance_report")}
generated_at: {yaml_quote(now_iso())}
status: {yaml_quote(status)}
repo_root: {yaml_quote(repo_root)}
python: {yaml_quote(sys.executable)}
---

# Acceptance Report

## Summary

- Status: `{status}`
- Project: `{safe_relative(project, repo_root)}`
- Commands run: `{len(runs)}`

## Environment

- Python: `{sys.version.split()[0]}`
- Repo root: `{repo_root}`

## Commands Run

{command_lines(runs)}

## Files Created

{file_lines(files, repo_root)}

## Compatibility Checks

- Unified CLI help was executed.
- v0.5, v0.6, and v0.7 flows are included unless skipped by CLI flags.

## v0.5 Flow

- create-function-card
- build-context-pack
- create-draft-prompt --target-length --style-strictness
- create-quality-report --with-prompt
- create-patch
- review-patch

## v0.6 Flow

- new-branch
- build-context-pack --task rewrite_plot
- create-plot-node-map
- create-divergence-analysis
- create-rewrite-plan
- create-branch-diff-report

## v0.7 Flow

- build-retrieval-index
- query-retrieval-index
- build-context-pack --use-retrieval-index --write-audit
- audit-context-pack

## Raw Text Safety Checks

- Raw marker copied into context pack: `{str(raw_marker_found).lower()}`

## Canon/Main Pollution Checks

{bullet(pollution_failures)}

## Failures

{bullet(failures)}

## Warnings

{bullet(warnings)}

## Next Action

If status is pass, this revision is ready for manual review and normal validation.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic acceptance checks for this skill.")
    parser.add_argument("--repo-root", default=".", type=Path)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--keep", action="store_true")
    parser.add_argument("--fast", action="store_true")
    parser.add_argument("--skip-v05", action="store_true")
    parser.add_argument("--skip-v06", action="store_true")
    parser.add_argument("--skip-v07", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = resolve_repo_root(args.repo_root)
    cli = repo_root / ".agents" / "skills" / "chinese-novel-writing" / "scripts" / "novel_project.py"
    scripts_dir = cli.parent
    project = (
        args.project_root.resolve()
        if args.project_root
        else repo_root / "tmp" / "acceptance_demo_novel"
    )
    output = args.output.resolve() if args.output else repo_root / "tmp" / "acceptance_report.md"
    failures: list[str] = []
    warnings: list[str] = []
    runs: list[dict[str, object]] = []

    try:
        ensure_inside(repo_root, project)
        ensure_inside(repo_root, output)
        if project.exists() and not args.keep:
            remove_tree_if_allowed(repo_root, project)
        if output.exists() and not args.force:
            failures.append(f"output exists: {output}. Use --force to overwrite.")
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    py_files = [str(path) for path in sorted(scripts_dir.glob("*.py"))]
    append_run(runs, repo_root, [sys.executable, "-m", "py_compile", *py_files], failures)
    append_run(runs, repo_root, [sys.executable, str(cli), "--help"], failures)
    append_run(
        runs,
        repo_root,
        [sys.executable, str(cli), "init", "--project-root", str(project), "--name", "acceptance_demo", "--force"],
        failures,
    )

    raw_full_text = project / "raw_text" / "full_text.txt"
    raw_full_text.parent.mkdir(parents=True, exist_ok=True)
    raw_full_text.write_text(RAW_MARKER + "\nThis is a tiny synthetic placeholder.\n", encoding="utf-8")

    if args.fast:
        append_run(runs, repo_root, [sys.executable, str(cli), "validate", "--project-root", str(project)], failures)
    else:
        if not args.skip_v05:
            append_run(runs, repo_root, [sys.executable, str(cli), "create-function-card", "--project-root", str(project), "--branch", "main", "--chapter", "1", "--goal", "acceptance test chapter", "--force"], failures)
            append_run(runs, repo_root, [sys.executable, str(cli), "build-context-pack", "--project-root", str(project), "--branch", "main", "--task", "continue_story", "--chapter", "1", "--user-request", "acceptance continue story", "--force"], failures)
            append_run(runs, repo_root, [sys.executable, str(cli), "create-draft-prompt", "--project-root", str(project), "--branch", "main", "--chapter", "1", "--target-length", "3000", "--style-strictness", "high", "--force"], failures)
            append_run(runs, repo_root, [sys.executable, str(cli), "create-quality-report", "--project-root", str(project), "--branch", "main", "--chapter", "1", "--with-prompt", "--force"], failures)
            append_run(runs, repo_root, [sys.executable, str(cli), "create-patch", "--project-root", str(project), "--branch", "main", "--chapter", "1", "--force"], failures)
            append_run(runs, repo_root, [sys.executable, str(cli), "review-patch", "--project-root", str(project), "--patch", "pending_updates/chapter_001_patch.yaml", "--force"], failures)

        baseline = snapshot([project / "canon", project / "branches" / "main"], project)

        if not args.skip_v06:
            append_run(runs, repo_root, [sys.executable, str(cli), "new-branch", "--project-root", str(project), "--name", "what_if_villain_ally", "--title", "villain ally branch", "--divergence", "protagonist allies with antagonist early", "--inherit", "skeleton", "--force"], failures)
            append_run(runs, repo_root, [sys.executable, str(cli), "build-context-pack", "--project-root", str(project), "--branch", "what_if_villain_ally", "--task", "rewrite_plot", "--chapter", "1", "--user-request", "what if protagonist allies with antagonist early", "--force"], failures)
            append_run(runs, repo_root, [sys.executable, str(cli), "create-plot-node-map", "--project-root", str(project), "--branch", "what_if_villain_ally", "--force"], failures)
            append_run(runs, repo_root, [sys.executable, str(cli), "create-divergence-analysis", "--project-root", str(project), "--branch", "what_if_villain_ally", "--divergence", "protagonist allies with antagonist early", "--impact-radius", "level_2_relationship", "--force"], failures)
            append_run(runs, repo_root, [sys.executable, str(cli), "create-rewrite-plan", "--project-root", str(project), "--branch", "what_if_villain_ally", "--force"], failures)
            append_run(runs, repo_root, [sys.executable, str(cli), "create-branch-diff-report", "--project-root", str(project), "--branch", "what_if_villain_ally", "--force"], failures)

        if not args.skip_v07:
            append_run(runs, repo_root, [sys.executable, str(cli), "build-retrieval-index", "--project-root", str(project), "--include-branches", "--force"], failures)
            append_run(runs, repo_root, [sys.executable, str(cli), "query-retrieval-index", "--project-root", str(project), "--query", "protagonist antagonist ally", "--branch", "what_if_villain_ally", "--top-k", "10", "--force"], failures)
            append_run(runs, repo_root, [sys.executable, str(cli), "build-context-pack", "--project-root", str(project), "--branch", "what_if_villain_ally", "--task", "rewrite_plot", "--chapter", "1", "--user-request", "what if protagonist allies with antagonist early", "--use-retrieval-index", "--retrieval-query", "protagonist antagonist ally", "--retrieval-top-k", "10", "--write-audit", "--force"], failures)
            append_run(runs, repo_root, [sys.executable, str(cli), "audit-context-pack", "--project-root", str(project), "--context-pack", "context_packs/latest_context_pack.md", "--branch", "what_if_villain_ally", "--task", "rewrite_plot", "--chapter", "1", "--force"], failures)

        append_run(runs, repo_root, [sys.executable, str(cli), "validate", "--project-root", str(project)], failures)

        after = snapshot([project / "canon", project / "branches" / "main"], project)
        pollution_failures = []
        if baseline != after:
            pollution_failures.append("canon/ or branches/main changed after rewrite/v0.7 flow baseline")
    if args.fast:
        pollution_failures = []

    created = [
        project / "indexes" / "retrieval_index.jsonl",
        project / "indexes" / "retrieval_index.md",
        project / "indexes" / "retrieval_query_report.md",
        project / "context_packs" / "latest_context_pack.md",
        project / "context_packs" / "latest_context_pack_audit.md",
        project / "branches" / "what_if_villain_ally" / "rewrite" / "plot_node_map.yaml",
        project / "branches" / "what_if_villain_ally" / "rewrite" / "divergence_analysis.yaml",
        project / "branches" / "what_if_villain_ally" / "rewrite" / "rewrite_plan_prompt.md",
        project / "branches" / "what_if_villain_ally" / "rewrite" / "branch_diff_report.md",
    ]
    for path in created:
        if not args.fast and not path.exists():
            warnings.append(f"expected file missing: {safe_relative(path, repo_root)}")

    context_pack = project / "context_packs" / "latest_context_pack.md"
    raw_marker_found = context_pack.exists() and RAW_MARKER in context_pack.read_text(encoding="utf-8", errors="replace")
    if raw_marker_found:
        failures.append("raw full text marker was copied into context pack")

    report = render_report(repo_root, project, runs, created, warnings, failures, raw_marker_found, pollution_failures)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(f"Wrote acceptance report: {output}")
    status_fail = bool(failures or pollution_failures or raw_marker_found)
    return 1 if status_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
