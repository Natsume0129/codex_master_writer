#!/usr/bin/env python3
"""Audit a context pack for budget, traceability, and branch-boundary risks."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from _novel_utils import safe_relative, yaml_quote
from _retrieval_utils import SCHEMA_VERSION, resolve_project_relative, timestamped_report_header, write_text_if_allowed


EXPECTED_SECTIONS = (
    "Task",
    "Branch Boundaries",
    "Project Snapshot",
    "Current Arc",
    "Recent Context",
    "Retrieval Notes",
    "Missing Sections",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def section_sizes(text: str) -> list[tuple[str, int]]:
    headings: list[tuple[str, int]] = []
    for match in re.finditer(r"(?m)^##+\s+(.+?)\s*$", text):
        headings.append((match.group(1).strip(), match.start()))
    sizes: list[tuple[str, int]] = []
    for index, (heading, start) in enumerate(headings):
        end = headings[index + 1][1] if index + 1 < len(headings) else len(text)
        sizes.append((heading, end - start))
    return sizes


def branch_references(text: str) -> set[str]:
    return set(re.findall(r"branches[/\\]([^/\\`\\s]+)", text))


def metadata_present(text: str, key: str, value: str = "") -> bool:
    if value:
        patterns = [
            f"- {key}: {value}",
            f"{key}: {value}",
            f"{key}: \"{value}\"",
        ]
        return any(pattern in text for pattern in patterns)
    return re.search(rf"(?m)(^|\s){re.escape(key)}\s*:", text) is not None


def audit_context(
    project: Path,
    context_pack: Path,
    branch: str,
    task: str,
    chapter: str,
    budget_chars: int,
    index: Path | None,
) -> dict[str, object]:
    warnings: list[str] = []
    suggestions: list[str] = []
    failures: list[str] = []
    oversized: list[tuple[str, int]] = []
    missing_sections: list[str] = []

    if not context_pack.exists():
        failures.append(f"context pack not found: {context_pack}")
        return {
            "status": "fail",
            "warnings": warnings,
            "suggestions": suggestions,
            "failures": failures,
            "oversized_sections": oversized,
            "missing_sections": missing_sections,
            "char_count": 0,
            "budget_chars": budget_chars,
            "raw_text_risk": "unknown",
            "branch_risks": [],
            "retrieval_trace": "missing",
        }

    text = read_text(context_pack)
    char_count = len(text)
    if budget_chars > 0 and char_count > budget_chars:
        warnings.append(f"context pack exceeds budget: {char_count} chars > {budget_chars}")
    raw_full_text = project / "raw_text" / "full_text.txt"
    raw_text_risk = "not_checked"
    if raw_full_text.exists():
        full_size = raw_full_text.stat().st_size
        pack_size = context_pack.stat().st_size
        raw_text_risk = "low"
        if full_size > 0 and pack_size >= full_size * 0.9 and full_size >= 10000:
            warnings.append("context pack size is close to raw_text/full_text.txt size")
            raw_text_risk = "high"
    if "raw_text/full_text.txt" in text or "raw_text\\full_text.txt" in text:
        warnings.append("context pack references raw_text/full_text.txt")
    refs = branch_references(text)
    allowed = {branch, "main", ""}
    branch_risks = sorted(ref for ref in refs if ref not in allowed)
    if branch_risks:
        warnings.append(f"context pack references other branches: {', '.join(branch_risks)}")

    for section in EXPECTED_SECTIONS:
        if f"## {section}" not in text:
            missing_sections.append(section)
    if missing_sections:
        suggestions.append(f"context pack missing expected sections: {', '.join(missing_sections)}")

    if not metadata_present(text, "type", task) and not metadata_present(text, "task"):
        suggestions.append("context pack may be missing task metadata")
    if branch and branch not in text:
        suggestions.append("context pack may be missing branch metadata")
    if chapter and str(chapter) not in text:
        suggestions.append("context pack may be missing chapter metadata")
    if "source:" not in text and "Source:" not in text:
        suggestions.append("context pack has little or no source trace")
    if "status:" not in text:
        suggestions.append("context pack has no visible fact status markers")
    if "confidence:" not in text:
        suggestions.append("context pack has no visible confidence markers")
    if "deprecated" in text.lower():
        warnings.append("context pack references deprecated facts")
    retrieval_trace = "present" if "## Retrieval Trace" in text else "missing"
    if retrieval_trace == "missing" and index and index.exists():
        suggestions.append("retrieval index exists but context pack has no Retrieval Trace section")

    threshold = max(8000, budget_chars // 3 if budget_chars else 8000)
    for heading, size in section_sizes(text):
        if size > threshold:
            oversized.append((heading, size))
    if oversized:
        warnings.append("context pack has oversized sections")

    status = "pass"
    if failures:
        status = "fail"
    elif warnings or suggestions:
        status = "warn"
    return {
        "status": status,
        "warnings": warnings,
        "suggestions": suggestions,
        "failures": failures,
        "oversized_sections": oversized,
        "missing_sections": missing_sections,
        "char_count": char_count,
        "budget_chars": budget_chars,
        "raw_text_risk": raw_text_risk,
        "branch_risks": branch_risks,
        "retrieval_trace": retrieval_trace,
    }


def bullet(values: list[str]) -> str:
    return "\n".join(f"- {value}" for value in values) if values else "- None"


def render_report(
    project: Path,
    context_pack: Path,
    branch: str,
    task: str,
    chapter: str,
    result: dict[str, object],
) -> str:
    warnings = result.get("warnings", [])
    suggestions = result.get("suggestions", [])
    failures = result.get("failures", [])
    missing = result.get("missing_sections", [])
    branch_risks = result.get("branch_risks", [])
    oversized = result.get("oversized_sections", [])
    oversized_text = (
        "\n".join(f"- `{heading}`: {size} chars" for heading, size in oversized)
        if isinstance(oversized, list) and oversized
        else "- None"
    )
    return f"""{timestamped_report_header("context_audit_report", context_pack=safe_relative(context_pack, project), branch=branch, task=task, chapter=chapter, status=result.get("status", "warn"))}

# Context Audit Report

## Summary

- Status: `{result.get("status", "warn")}`
- Context pack: `{safe_relative(context_pack, project)}`
- Character count: `{result.get("char_count", 0)}`

## Budget

- Budget chars: `{result.get("budget_chars", 0)}`
- Actual chars: `{result.get("char_count", 0)}`

## Source Trace

- Source/status/confidence markers are checked heuristically.
- Warnings: {len(warnings) if isinstance(warnings, list) else 0}

## Branch Boundary Check

{bullet(branch_risks if isinstance(branch_risks, list) else [])}

## Raw Text Risk

- Risk: `{result.get("raw_text_risk", "unknown")}`
- This audit checks raw file size only; it does not read `raw_text/full_text.txt` content.

## Fact Envelope Check

- Missing source/status/confidence markers are reported as suggestions, not fatal errors.

## Deprecated Fact Check

- Deprecated markers are treated as warnings.

## Oversized Sections

{oversized_text}

## Missing Sections

{bullet(missing if isinstance(missing, list) else [])}

## Retrieval Trace Check

- Retrieval Trace: `{result.get("retrieval_trace", "missing")}`

## Suggestions

{bullet(suggestions if isinstance(suggestions, list) else [])}

## Failures

{bullet(failures if isinstance(failures, list) else [])}

## Warnings

{bullet(warnings if isinstance(warnings, list) else [])}

## Next Action

Fix failures first. For warnings, regenerate the context pack with narrower selectors or add a Retrieval Trace through `build-context-pack --use-retrieval-index --write-audit`.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit a context pack for v0.7 traceability and budget rules.")
    parser.add_argument("--project", "--project-root", dest="project", required=True, type=Path)
    parser.add_argument("--context-pack", type=Path)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--task", default="")
    parser.add_argument("--chapter", default="")
    parser.add_argument("--budget-chars", type=int, default=60000)
    parser.add_argument("--index", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    if not project.exists():
        print(f"error: project not found: {project}", file=sys.stderr)
        return 1
    context_pack = (
        resolve_project_relative(project, args.context_pack)
        if args.context_pack
        else project / "context_packs" / "latest_context_pack.md"
    )
    index = resolve_project_relative(project, args.index) if args.index else project / "indexes" / "retrieval_index.jsonl"
    assert context_pack is not None
    assert index is not None
    output = (
        resolve_project_relative(project, args.output)
        if args.output
        else context_pack.parent / f"{context_pack.stem}_audit.md"
    )
    assert output is not None
    result = audit_context(project, context_pack, args.branch, args.task, args.chapter, args.budget_chars, index)
    try:
        write_text_if_allowed(
            output,
            render_report(project, context_pack, args.branch, args.task, args.chapter, result),
            args.force,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote context audit report: {output}")
    print(f"Audit status: {result.get('status', 'warn')}")
    return 1 if result.get("status") == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
