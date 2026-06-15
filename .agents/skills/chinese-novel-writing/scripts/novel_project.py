#!/usr/bin/env python3
"""Unified CLI for chinese-novel-writing deterministic project helpers."""

from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


class StepFailed(RuntimeError):
    def __init__(self, label: str, code: int) -> None:
        super().__init__(f"{label} failed with exit code {code}")
        self.label = label
        self.code = code


def path_text(path: Path | str) -> str:
    return str(path)


def add_flag(args: list[str], enabled: bool, flag: str) -> None:
    if enabled:
        args.append(flag)


def add_value(args: list[str], flag: str, value: object | None) -> None:
    if value is not None and value != "":
        args.extend([flag, str(value)])


def add_values(args: list[str], flag: str, values: list[str] | None) -> None:
    if values:
        args.append(flag)
        args.extend(str(value) for value in values)


def run_script(script_name: str, script_args: list[str]) -> int:
    """Run a sibling helper script with preserved exit code."""
    script_path = SCRIPT_DIR / script_name
    if not script_path.exists():
        print(f"error: helper script not found: {script_path}", file=sys.stderr)
        return 1
    old_argv = sys.argv[:]
    sys.argv = [str(script_path), *script_args]
    try:
        runpy.run_path(str(script_path), run_name="__main__")
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        print(code, file=sys.stderr)
        return 1
    finally:
        sys.argv = old_argv
    return 0


def run_step(label: str, script_name: str, script_args: list[str]) -> None:
    print(f"\n==> {label}")
    code = run_script(script_name, script_args)
    if code != 0:
        raise StepFailed(label, code)


def project_arg(
    parser: argparse.ArgumentParser, required: bool = True, aliases: tuple[str, ...] = ()
) -> None:
    parser.add_argument(
        "--project-root",
        "--project",
        *aliases,
        dest="project_root",
        required=required,
        type=Path,
        help="Novel project root.",
    )


def command_init(args: argparse.Namespace) -> int:
    project_root = args.project_root
    name = args.name or project_root.name
    script_args = ["--name", name, "--output", path_text(project_root)]
    add_flag(script_args, args.force, "--force")
    run_step("Initialize project", "init_project.py", script_args)
    print(f"\nDone: initialized project at {project_root}")
    return 0


def command_split_import(args: argparse.Namespace) -> int:
    if args.clean and not args.force:
        print("error: --clean requires --force for split-import", file=sys.stderr)
        return 2
    project_root = args.project_root
    chapter_dir = project_root / "raw_text" / "chapters"

    split_chapter_args = ["--input", path_text(args.source), "--output", path_text(chapter_dir)]
    add_flag(split_chapter_args, args.force, "--force")
    run_step("Split source into chapters", "split_chapters.py", split_chapter_args)

    split_chunk_args = [
        "--project",
        path_text(project_root),
        "--chunk-size",
        str(args.chunk_size),
        "--overlap",
        str(args.overlap),
    ]
    add_flag(split_chunk_args, args.force, "--force")
    add_flag(split_chunk_args, args.clean, "--clean")
    run_step("Split chapters into chunks", "split_chunks.py", split_chunk_args)

    if args.no_progress:
        print("\nDone: import split completed; progress and batch creation skipped.")
        return 0

    progress_args = [
        "--project",
        path_text(project_root),
        "--batch-size",
        str(args.batch_size),
    ]
    add_flag(progress_args, args.force, "--force")
    run_step("Initialize extraction progress", "init_extraction_progress.py", progress_args)

    if args.no_batch:
        print("\nDone: import split and progress initialization completed; batch creation skipped.")
        return 0

    batch_args = [
        "--project",
        path_text(project_root),
        "--stage",
        "chunk_cards",
        "--batch-size",
        str(args.batch_size),
    ]
    add_flag(batch_args, args.force, "--force")
    run_step("Create first extraction batch", "create_extraction_batch.py", batch_args)
    print("\nDone: split-import completed.")
    return 0


def command_init_progress(args: argparse.Namespace) -> int:
    script_args = ["--project", path_text(args.project_root), "--batch-size", str(args.batch_size)]
    add_value(script_args, "--manifest", args.manifest)
    add_flag(script_args, args.force, "--force")
    run_step("Initialize extraction progress", "init_extraction_progress.py", script_args)
    return 0


def command_create_batch(args: argparse.Namespace) -> int:
    script_args = [
        "--project",
        path_text(args.project_root),
        "--stage",
        args.stage,
        "--batch-size",
        str(args.batch_size),
    ]
    add_flag(script_args, args.retry_failed, "--retry-failed")
    add_flag(script_args, args.dry_run, "--dry-run")
    add_flag(script_args, args.force, "--force")
    run_step("Create extraction batch", "create_extraction_batch.py", script_args)
    return 0


def command_import_status(args: argparse.Namespace) -> int:
    script_args = ["--project", path_text(args.project_root), "--format", args.format]
    add_value(script_args, "--output", args.output)
    add_flag(script_args, args.show_pending, "--show-pending")
    add_flag(script_args, args.show_failed, "--show-failed")
    add_flag(script_args, args.show_ready, "--show-ready")
    add_flag(script_args, args.show_next, "--show-next")
    run_step("Create import status report", "import_status.py", script_args)
    return 0


def command_create_chapter_card_batch(args: argparse.Namespace) -> int:
    script_args = [
        "--project",
        path_text(args.project_root),
        "--batch-size",
        str(args.batch_size),
    ]
    add_value(script_args, "--chapter", args.chapter)
    add_flag(script_args, args.only_ready, "--only-ready")
    add_flag(script_args, args.retry_failed, "--retry-failed")
    add_flag(script_args, args.dry_run, "--dry-run")
    add_flag(script_args, args.force, "--force")
    run_step("Create chapter-card batch", "create_chapter_card_batch.py", script_args)
    return 0


def command_create_volume_summary_batch(args: argparse.Namespace) -> int:
    script_args = [
        "--project",
        path_text(args.project_root),
        "--volume",
        args.volume,
        "--batch-size",
        str(args.batch_size),
    ]
    add_values(script_args, "--chapters", args.chapters)
    add_value(script_args, "--from-chapter", args.from_chapter)
    add_value(script_args, "--to-chapter", args.to_chapter)
    add_flag(script_args, args.dry_run, "--dry-run")
    add_flag(script_args, args.force, "--force")
    run_step("Create volume-summary batch", "create_volume_summary_batch.py", script_args)
    return 0


def command_create_bible_patch_batch(args: argparse.Namespace) -> int:
    script_args = ["--project", path_text(args.project_root), "--source", args.source]
    add_values(script_args, "--chapters", args.chapters)
    add_value(script_args, "--volume", args.volume)
    add_flag(script_args, args.dry_run, "--dry-run")
    add_flag(script_args, args.force, "--force")
    run_step("Create story-bible patch batch", "create_bible_patch_batch.py", script_args)
    return 0


def command_mark_done(args: argparse.Namespace) -> int:
    if not args.batch_id and not args.chunk_id and not args.chapter_id:
        print("error: provide --batch-id, --chunk-id, or --chapter-id", file=sys.stderr)
        return 2
    script_args = [
        "--project",
        path_text(args.project_root),
        "--status",
        args.status,
    ]
    add_value(script_args, "--stage", args.stage)
    add_value(script_args, "--batch-id", args.batch_id)
    add_value(script_args, "--chunk-id", args.chunk_id)
    add_value(script_args, "--chapter-id", args.chapter_id)
    add_value(script_args, "--chunk-card", args.chunk_card)
    add_value(script_args, "--chapter-card", args.chapter_card)
    add_value(script_args, "--output", args.output)
    add_value(script_args, "--error", args.error)
    run_step("Mark extraction progress", "mark_extraction_done.py", script_args)
    return 0


def command_build_indexes(args: argparse.Namespace) -> int:
    script_args = ["--project", path_text(args.project_root), "--source", args.source]
    add_flag(script_args, args.dry_run, "--dry-run")
    add_flag(script_args, args.force, "--force")
    run_step("Build indexes", "build_indexes.py", script_args)
    return 0


def command_new_branch(args: argparse.Namespace) -> int:
    if args.inherit == "current-state" and not args.base_chapter:
        print("error: --base-chapter is required when --inherit current-state", file=sys.stderr)
        return 2
    script_args = [
        "--project",
        path_text(args.project_root),
        "--branch",
        args.name,
        "--inherit",
        args.inherit,
    ]
    add_value(script_args, "--title", args.title)
    add_value(script_args, "--divergence", args.divergence)
    add_value(script_args, "--base-chapter", args.base_chapter)
    add_flag(script_args, args.force, "--force")
    run_step("Create isolated branch", "create_branch.py", script_args)
    return 0


def command_create_function_card(args: argparse.Namespace) -> int:
    script_args = [
        "--project",
        path_text(args.project_root),
        "--branch",
        args.branch,
        "--chapter",
        args.chapter,
        "--source",
        args.source,
        "--status",
        args.status,
        "--confidence",
        args.confidence,
    ]
    add_value(script_args, "--goal", args.goal)
    add_flag(script_args, args.force, "--force")
    run_step("Create chapter function card", "create_chapter_function_card.py", script_args)
    return 0


def command_build_context_pack(args: argparse.Namespace) -> int:
    script_args = [
        "--project",
        path_text(args.project_root),
        "--branch",
        args.branch,
        "--task",
        args.task,
        "--chapter",
        args.chapter,
        "--user-request",
        args.user_request,
        "--output-mode",
        args.output_mode,
        "--include-recent",
        str(args.include_recent),
        "--previous-ending-chars",
        str(args.previous_ending_chars),
    ]
    add_values(script_args, "--characters", args.characters)
    add_values(script_args, "--locations", args.locations)
    add_values(script_args, "--items", args.items)
    add_values(script_args, "--organizations", args.organizations)
    add_values(script_args, "--terms", args.terms)
    add_values(script_args, "--foreshadowing-ids", args.foreshadowing_ids)
    add_values(script_args, "--event-ids", args.event_ids)
    add_flag(script_args, args.auto_select, "--auto-select")
    add_value(script_args, "--selector-source", args.selector_source)
    add_value(script_args, "--max-selectors", args.max_selectors)
    add_flag(script_args, args.write_selector_report, "--write-selector-report")
    add_value(script_args, "--selector-report-output", args.selector_report_output)
    add_flag(script_args, args.use_retrieval_index, "--use-retrieval-index")
    add_value(script_args, "--retrieval-index", args.retrieval_index)
    add_value(script_args, "--retrieval-query", args.retrieval_query)
    add_value(script_args, "--retrieval-top-k", args.retrieval_top_k)
    add_value(script_args, "--context-budget-chars", args.context_budget_chars)
    add_flag(script_args, args.write_audit, "--write-audit")
    add_value(script_args, "--audit-output", args.audit_output)
    add_value(script_args, "--format", args.format)
    add_value(script_args, "--output", args.output)
    add_flag(script_args, args.force, "--force")
    run_step("Build context pack", "build_context_pack.py", script_args)
    return 0


def command_build_retrieval_index(args: argparse.Namespace) -> int:
    script_args = ["--project", path_text(args.project_root), "--branch", args.branch]
    add_flag(script_args, args.include_branches, "--include-branches")
    add_values(script_args, "--source-types", args.source_types)
    add_value(script_args, "--output", args.output)
    add_value(script_args, "--report-output", args.report_output)
    add_flag(script_args, args.force, "--force")
    run_step("Build retrieval index", "build_retrieval_index.py", script_args)
    return 0


def command_query_retrieval_index(args: argparse.Namespace) -> int:
    script_args = ["--project", path_text(args.project_root)]
    add_value(script_args, "--index", args.index)
    add_value(script_args, "--query", args.query)
    add_value(script_args, "--branch", args.branch)
    add_value(script_args, "--chapter", args.chapter)
    add_values(script_args, "--characters", args.characters)
    add_values(script_args, "--locations", args.locations)
    add_values(script_args, "--items", args.items)
    add_values(script_args, "--organizations", args.organizations)
    add_values(script_args, "--terms", args.terms)
    add_values(script_args, "--source-types", args.source_types)
    add_value(script_args, "--top-k", args.top_k)
    add_value(script_args, "--output", args.output)
    add_value(script_args, "--format", args.format)
    add_flag(script_args, args.force, "--force")
    run_step("Query retrieval index", "query_retrieval_index.py", script_args)
    return 0


def command_audit_context_pack(args: argparse.Namespace) -> int:
    script_args = ["--project", path_text(args.project_root)]
    add_value(script_args, "--context-pack", args.context_pack)
    add_value(script_args, "--branch", args.branch)
    add_value(script_args, "--task", args.task)
    add_value(script_args, "--chapter", args.chapter)
    add_value(script_args, "--budget-chars", args.budget_chars)
    add_value(script_args, "--index", args.index)
    add_value(script_args, "--output", args.output)
    add_flag(script_args, args.force, "--force")
    run_step("Audit context pack", "audit_context_pack.py", script_args)
    return 0


def command_acceptance_check(args: argparse.Namespace) -> int:
    script_args = ["--repo-root", path_text(args.repo_root)]
    add_value(script_args, "--project-root", args.project_root)
    add_flag(script_args, args.keep, "--keep")
    add_flag(script_args, args.fast, "--fast")
    add_flag(script_args, args.skip_v05, "--skip-v05")
    add_flag(script_args, args.skip_v06, "--skip-v06")
    add_flag(script_args, args.skip_v07, "--skip-v07")
    add_value(script_args, "--output", args.output)
    add_flag(script_args, args.force, "--force")
    run_step("Run acceptance checks", "run_acceptance_checks.py", script_args)
    return 0


def command_create_draft_prompt(args: argparse.Namespace) -> int:
    script_args = [
        "--project",
        path_text(args.project_root),
        "--branch",
        args.branch,
        "--chapter",
        args.chapter,
        "--output-mode",
        args.output_mode,
    ]
    add_value(script_args, "--context-pack", args.context_pack)
    add_value(script_args, "--function-card", args.function_card)
    add_value(script_args, "--output", args.output)
    add_value(script_args, "--draft-output", args.draft_output)
    add_value(script_args, "--target-length", args.target_length)
    add_value(script_args, "--style-strictness", args.style_strictness)
    add_flag(script_args, args.force, "--force")
    run_step("Create chapter draft prompt", "create_draft_prompt.py", script_args)
    return 0


def command_create_plot_node_map(args: argparse.Namespace) -> int:
    script_args = [
        "--project",
        path_text(args.project_root),
        "--branch",
        args.branch,
        "--base-branch",
        args.base_branch,
    ]
    add_value(script_args, "--source", args.source)
    add_value(script_args, "--output", args.output)
    add_flag(script_args, args.force, "--force")
    run_step("Create plot node map", "create_plot_node_map.py", script_args)
    return 0


def command_create_divergence_analysis(args: argparse.Namespace) -> int:
    script_args = [
        "--project",
        path_text(args.project_root),
        "--branch",
        args.branch,
        "--base-branch",
        args.base_branch,
    ]
    add_value(script_args, "--base-chapter", args.base_chapter)
    add_value(script_args, "--divergence", args.divergence)
    add_value(script_args, "--original-fact", args.original_fact)
    add_value(script_args, "--changed-fact", args.changed_fact)
    add_value(script_args, "--impact-radius", args.impact_radius)
    add_value(script_args, "--output", args.output)
    add_flag(script_args, args.force, "--force")
    run_step("Create divergence analysis", "create_divergence_analysis.py", script_args)
    return 0


def command_create_rewrite_plan(args: argparse.Namespace) -> int:
    script_args = [
        "--project",
        path_text(args.project_root),
        "--branch",
        args.branch,
        "--base-branch",
        args.base_branch,
    ]
    add_value(script_args, "--context-pack", args.context_pack)
    add_value(script_args, "--plot-node-map", args.plot_node_map)
    add_value(script_args, "--divergence-analysis", args.divergence_analysis)
    add_value(script_args, "--replacement-routes", args.replacement_routes)
    add_value(script_args, "--output", args.output)
    add_flag(script_args, args.force, "--force")
    run_step("Create rewrite plan prompt", "create_rewrite_plan.py", script_args)
    return 0


def command_create_branch_diff_report(args: argparse.Namespace) -> int:
    script_args = [
        "--project",
        path_text(args.project_root),
        "--branch",
        args.branch,
        "--base-branch",
        args.base_branch,
    ]
    add_value(script_args, "--divergence-analysis", args.divergence_analysis)
    add_value(script_args, "--replacement-routes", args.replacement_routes)
    add_value(script_args, "--plot-node-map", args.plot_node_map)
    add_value(script_args, "--output", args.output)
    add_flag(script_args, args.force, "--force")
    run_step("Create branch diff report", "create_branch_diff_report.py", script_args)
    return 0


def command_create_patch(args: argparse.Namespace) -> int:
    script_args = [
        "--project",
        path_text(args.project_root),
        "--branch",
        args.branch,
        "--chapter",
        args.chapter,
    ]
    add_value(script_args, "--source-draft", args.source_draft)
    add_value(script_args, "--output", args.output)
    add_flag(script_args, args.force, "--force")
    run_step("Create pending patch", "create_patch.py", script_args)
    return 0


def command_create_patch_review(args: argparse.Namespace) -> int:
    script_args = [
        "--project",
        path_text(args.project_root),
        "--patch",
        path_text(args.patch),
    ]
    add_value(script_args, "--output", args.output)
    add_flag(script_args, args.force, "--force")
    run_step("Create patch review report", "create_patch_review.py", script_args)
    return 0


def command_create_quality_report(args: argparse.Namespace) -> int:
    script_args = [
        "--project",
        path_text(args.project_root),
        "--branch",
        args.branch,
        "--chapter",
        args.chapter,
        "--severity",
        args.severity,
    ]
    add_value(script_args, "--draft", args.draft)
    add_value(script_args, "--context-pack", args.context_pack)
    add_value(script_args, "--output", args.output)
    add_value(script_args, "--prompt-output", args.prompt_output)
    add_flag(script_args, args.template_only, "--template-only")
    add_flag(script_args, args.with_prompt, "--with-prompt")
    add_flag(script_args, args.prompt_only, "--prompt-only")
    add_flag(script_args, args.force, "--force")
    run_step("Create chapter quality report", "create_quality_report.py", script_args)
    return 0


def command_apply_patch(args: argparse.Namespace) -> int:
    script_args = ["--project", path_text(args.project_root), "--patch", path_text(args.patch)]
    add_flag(script_args, args.confirm, "--confirm")
    add_flag(script_args, args.confirm_major, "--confirm-major")
    run_step("Apply patch dry-run or confirmed update", "apply_patch.py", script_args)
    return 0


def command_validate(args: argparse.Namespace) -> int:
    script_args = ["--project", path_text(args.project_root)]
    return run_script("validate_project.py", script_args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Unified CLI for chinese-novel-writing project helpers."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create a novel project from templates.")
    project_arg(init, aliases=("--output",))
    init.add_argument("--name", default="", help="Project name. Defaults to project-root folder name.")
    init.add_argument("--force", action="store_true", help="Replace project-root if it exists.")
    init.set_defaults(func=command_init)

    split_import = subparsers.add_parser(
        "split-import",
        help="Split source text into chapters/chunks, initialize progress, and create the first batch.",
    )
    project_arg(split_import)
    split_import.add_argument("--source", required=True, type=Path, help="Source txt file.")
    split_import.add_argument("--chunk-size", type=int, default=6000)
    split_import.add_argument("--overlap", type=int, default=500)
    split_import.add_argument("--batch-size", type=int, default=5)
    split_import.add_argument("--force", action="store_true")
    split_import.add_argument("--clean", action="store_true")
    split_import.add_argument("--no-progress", action="store_true")
    split_import.add_argument("--no-batch", action="store_true")
    split_import.set_defaults(func=command_split_import)

    init_progress = subparsers.add_parser("init-progress", help="Initialize extraction progress.")
    project_arg(init_progress)
    init_progress.add_argument("--manifest", type=Path)
    init_progress.add_argument("--batch-size", type=int, default=10)
    init_progress.add_argument("--force", action="store_true")
    init_progress.set_defaults(func=command_init_progress)

    create_batch = subparsers.add_parser("create-batch", help="Create the next extraction batch.")
    project_arg(create_batch)
    create_batch.add_argument("--stage", default="chunk_cards")
    create_batch.add_argument("--batch-size", type=int, default=5)
    create_batch.add_argument("--retry-failed", action="store_true")
    create_batch.add_argument("--dry-run", action="store_true")
    create_batch.add_argument("--force", action="store_true")
    create_batch.set_defaults(func=command_create_batch)

    import_status = subparsers.add_parser("import-status", help="Report import progress and next actions.")
    project_arg(import_status)
    import_status.add_argument("--format", choices=("markdown", "text", "yaml"), default="markdown")
    import_status.add_argument("--output", type=Path)
    import_status.add_argument("--show-pending", action="store_true")
    import_status.add_argument("--show-failed", action="store_true")
    import_status.add_argument("--show-ready", action="store_true")
    import_status.add_argument("--show-next", action="store_true")
    import_status.set_defaults(func=command_import_status)

    chapter_card_batch = subparsers.add_parser(
        "create-chapter-card-batch",
        help="Create a chapter-card extraction batch from completed chunk cards.",
    )
    project_arg(chapter_card_batch)
    chapter_card_batch.add_argument("--batch-size", type=int, default=5)
    chapter_card_batch.add_argument("--chapter", default="")
    chapter_card_batch.add_argument("--only-ready", action="store_true")
    chapter_card_batch.add_argument("--retry-failed", action="store_true")
    chapter_card_batch.add_argument("--dry-run", action="store_true")
    chapter_card_batch.add_argument("--force", action="store_true")
    chapter_card_batch.set_defaults(func=command_create_chapter_card_batch)

    volume_summary_batch = subparsers.add_parser(
        "create-volume-summary-batch",
        help="Create a volume-summary batch from reviewed chapter cards.",
    )
    project_arg(volume_summary_batch)
    volume_summary_batch.add_argument("--volume", default="1")
    volume_summary_batch.add_argument("--chapters", nargs="*", default=[])
    volume_summary_batch.add_argument("--from-chapter", default="")
    volume_summary_batch.add_argument("--to-chapter", default="")
    volume_summary_batch.add_argument("--batch-size", type=int, default=0)
    volume_summary_batch.add_argument("--dry-run", action="store_true")
    volume_summary_batch.add_argument("--force", action="store_true")
    volume_summary_batch.set_defaults(func=command_create_volume_summary_batch)

    bible_patch_batch = subparsers.add_parser(
        "create-bible-patch-batch",
        help="Create story-bible patch batch prompts without editing canon.",
    )
    project_arg(bible_patch_batch)
    bible_patch_batch.add_argument(
        "--source",
        choices=("chunk_cards", "chapter_cards", "volume_summaries", "all"),
        default="chapter_cards",
    )
    bible_patch_batch.add_argument("--chapters", nargs="*", default=[])
    bible_patch_batch.add_argument("--volume", default="")
    bible_patch_batch.add_argument("--dry-run", action="store_true")
    bible_patch_batch.add_argument("--force", action="store_true")
    bible_patch_batch.set_defaults(func=command_create_bible_patch_batch)

    mark_done = subparsers.add_parser("mark-done", help="Mark extraction batch or chunk state.")
    project_arg(mark_done)
    mark_done.add_argument("--batch-id")
    mark_done.add_argument("--chunk-id")
    mark_done.add_argument("--chapter-id")
    mark_done.add_argument("--chunk-card", type=Path)
    mark_done.add_argument("--chapter-card", type=Path)
    mark_done.add_argument("--output", type=Path)
    mark_done.add_argument("--stage", default="", help="Defaults to batch metadata stage when omitted.")
    mark_done.add_argument(
        "--status",
        required=True,
        choices=("done", "failed", "skipped", "processing", "queued"),
    )
    mark_done.add_argument("--error", default="")
    mark_done.set_defaults(func=command_mark_done)

    build_indexes = subparsers.add_parser("build-indexes", help="Build navigation indexes.")
    project_arg(build_indexes)
    build_indexes.add_argument("--source", choices=("extracted", "canon", "all"), default="all")
    build_indexes.add_argument("--dry-run", action="store_true")
    build_indexes.add_argument("--force", action="store_true")
    build_indexes.set_defaults(func=command_build_indexes)

    new_branch = subparsers.add_parser("new-branch", help="Create an isolated alternate-plot branch.")
    project_arg(new_branch)
    new_branch.add_argument("--name", "--branch", dest="name", required=True)
    new_branch.add_argument("--title", default="")
    new_branch.add_argument("--divergence", default="")
    new_branch.add_argument("--inherit", choices=("skeleton", "current-state"), default="skeleton")
    new_branch.add_argument("--base-chapter", default="")
    new_branch.add_argument("--force", action="store_true")
    new_branch.set_defaults(func=command_new_branch)

    function_card = subparsers.add_parser("create-function-card", help="Create a chapter function card.")
    project_arg(function_card)
    function_card.add_argument("--branch", default="main")
    function_card.add_argument("--chapter", required=True)
    function_card.add_argument("--goal", default="")
    function_card.add_argument("--source", default="user_input")
    function_card.add_argument("--status", default="inferred")
    function_card.add_argument("--confidence", default="medium")
    function_card.add_argument("--force", action="store_true")
    function_card.set_defaults(func=command_create_function_card)

    context_pack = subparsers.add_parser("build-context-pack", help="Build a filtered context pack.")
    project_arg(context_pack)
    context_pack.add_argument("--branch", default="main")
    context_pack.add_argument("--task", default="continue_story")
    context_pack.add_argument("--chapter", default="")
    context_pack.add_argument("--user-request", default="")
    context_pack.add_argument("--output-mode", default="draft_with_notes")
    context_pack.add_argument("--characters", nargs="*", default=[])
    context_pack.add_argument("--locations", nargs="*", default=[])
    context_pack.add_argument("--items", nargs="*", default=[])
    context_pack.add_argument("--organizations", nargs="*", default=[])
    context_pack.add_argument("--terms", nargs="*", default=[])
    context_pack.add_argument("--foreshadowing-ids", nargs="*", default=[])
    context_pack.add_argument("--event-ids", nargs="*", default=[])
    context_pack.add_argument("--include-recent", type=int, default=3)
    context_pack.add_argument("--previous-ending-chars", type=int, default=1500)
    context_pack.add_argument("--auto-select", action="store_true")
    context_pack.add_argument(
        "--selector-source",
        choices=("indexes", "chapter_card", "recent", "all"),
        default="all",
    )
    context_pack.add_argument("--max-selectors", type=int, default=20)
    context_pack.add_argument("--write-selector-report", action="store_true")
    context_pack.add_argument("--selector-report-output", type=Path)
    context_pack.add_argument("--use-retrieval-index", action="store_true")
    context_pack.add_argument("--retrieval-index", type=Path)
    context_pack.add_argument("--retrieval-query", default="")
    context_pack.add_argument("--retrieval-top-k", type=int, default=20)
    context_pack.add_argument("--context-budget-chars", type=int, default=60000)
    context_pack.add_argument("--write-audit", action="store_true")
    context_pack.add_argument("--audit-output", type=Path)
    context_pack.add_argument("--format", choices=("markdown", "yaml"), default=None)
    context_pack.add_argument("--output", type=Path)
    context_pack.add_argument("--force", action="store_true")
    context_pack.set_defaults(func=command_build_context_pack)

    retrieval_index = subparsers.add_parser(
        "build-retrieval-index",
        help="Build a v0.7 deterministic retrieval index from structured artifacts.",
    )
    project_arg(retrieval_index)
    retrieval_index.add_argument("--branch", default="main")
    retrieval_index.add_argument("--include-branches", action="store_true")
    retrieval_index.add_argument("--source-types", nargs="*", default=[])
    retrieval_index.add_argument("--output", type=Path)
    retrieval_index.add_argument("--report-output", type=Path)
    retrieval_index.add_argument("--force", action="store_true")
    retrieval_index.set_defaults(func=command_build_retrieval_index)

    retrieval_query = subparsers.add_parser(
        "query-retrieval-index",
        help="Create a deterministic v0.7 retrieval candidate report.",
    )
    project_arg(retrieval_query)
    retrieval_query.add_argument("--index", type=Path)
    retrieval_query.add_argument("--query", default="")
    retrieval_query.add_argument("--branch", default="")
    retrieval_query.add_argument("--chapter", default="")
    retrieval_query.add_argument("--characters", nargs="*", default=[])
    retrieval_query.add_argument("--locations", nargs="*", default=[])
    retrieval_query.add_argument("--items", nargs="*", default=[])
    retrieval_query.add_argument("--organizations", nargs="*", default=[])
    retrieval_query.add_argument("--terms", nargs="*", default=[])
    retrieval_query.add_argument("--source-types", nargs="*", default=[])
    retrieval_query.add_argument("--top-k", type=int, default=20)
    retrieval_query.add_argument("--output", type=Path)
    retrieval_query.add_argument("--format", choices=("markdown", "yaml"), default="markdown")
    retrieval_query.add_argument("--force", action="store_true")
    retrieval_query.set_defaults(func=command_query_retrieval_index)

    audit_context = subparsers.add_parser(
        "audit-context-pack",
        help="Audit a context pack for v0.7 budget and traceability rules.",
    )
    project_arg(audit_context)
    audit_context.add_argument("--context-pack", type=Path)
    audit_context.add_argument("--branch", default="main")
    audit_context.add_argument("--task", default="")
    audit_context.add_argument("--chapter", default="")
    audit_context.add_argument("--budget-chars", type=int, default=60000)
    audit_context.add_argument("--index", type=Path)
    audit_context.add_argument("--output", type=Path)
    audit_context.add_argument("--force", action="store_true")
    audit_context.set_defaults(func=command_audit_context_pack)

    acceptance = subparsers.add_parser(
        "acceptance-check",
        help="Run deterministic v0.7 acceptance checks without pytest.",
    )
    acceptance.add_argument("--repo-root", type=Path, default=Path("."))
    acceptance.add_argument("--project-root", type=Path)
    acceptance.add_argument("--keep", action="store_true")
    acceptance.add_argument("--fast", action="store_true")
    acceptance.add_argument("--skip-v05", action="store_true")
    acceptance.add_argument("--skip-v06", action="store_true")
    acceptance.add_argument("--skip-v07", action="store_true")
    acceptance.add_argument("--output", type=Path)
    acceptance.add_argument("--force", action="store_true")
    acceptance.set_defaults(func=command_acceptance_check)

    draft_prompt = subparsers.add_parser(
        "create-draft-prompt",
        help="Create a deterministic chapter drafting prompt from a context pack and function card.",
    )
    project_arg(draft_prompt)
    draft_prompt.add_argument("--branch", default="main")
    draft_prompt.add_argument("--chapter", required=True)
    draft_prompt.add_argument("--context-pack", type=Path)
    draft_prompt.add_argument("--function-card", type=Path)
    draft_prompt.add_argument("--output", type=Path)
    draft_prompt.add_argument("--draft-output", type=Path)
    draft_prompt.add_argument("--output-mode", default="draft_with_notes")
    draft_prompt.add_argument("--target-length", default="")
    draft_prompt.add_argument(
        "--style-strictness",
        choices=("low", "medium", "high"),
        default="medium",
    )
    draft_prompt.add_argument("--force", action="store_true")
    draft_prompt.set_defaults(func=command_create_draft_prompt)

    plot_node_map = subparsers.add_parser(
        "create-plot-node-map",
        help="Create a v0.6 rewrite plot-node map skeleton.",
    )
    project_arg(plot_node_map)
    plot_node_map.add_argument("--branch", default="main")
    plot_node_map.add_argument("--base-branch", default="main")
    plot_node_map.add_argument("--source", default="")
    plot_node_map.add_argument("--output", type=Path)
    plot_node_map.add_argument("--force", action="store_true")
    plot_node_map.set_defaults(func=command_create_plot_node_map)

    divergence_analysis = subparsers.add_parser(
        "create-divergence-analysis",
        help="Create a v0.6 divergence-analysis skeleton.",
    )
    project_arg(divergence_analysis)
    divergence_analysis.add_argument("--branch", default="main")
    divergence_analysis.add_argument("--base-branch", default="main")
    divergence_analysis.add_argument("--base-chapter", default="")
    divergence_analysis.add_argument("--divergence", default="")
    divergence_analysis.add_argument("--original-fact", default="")
    divergence_analysis.add_argument("--changed-fact", default="")
    divergence_analysis.add_argument(
        "--impact-radius",
        choices=(
            "level_1_local",
            "level_2_relationship",
            "level_3_main_plot",
            "level_4_world_rule",
            "uncertain",
        ),
        default="",
    )
    divergence_analysis.add_argument("--output", type=Path)
    divergence_analysis.add_argument("--force", action="store_true")
    divergence_analysis.set_defaults(func=command_create_divergence_analysis)

    rewrite_plan = subparsers.add_parser(
        "create-rewrite-plan",
        help="Create a v0.6 rewrite-plan prompt and replacement route skeleton.",
    )
    project_arg(rewrite_plan)
    rewrite_plan.add_argument("--branch", default="main")
    rewrite_plan.add_argument("--base-branch", default="main")
    rewrite_plan.add_argument("--context-pack", type=Path)
    rewrite_plan.add_argument("--plot-node-map", type=Path)
    rewrite_plan.add_argument("--divergence-analysis", type=Path)
    rewrite_plan.add_argument("--replacement-routes", type=Path)
    rewrite_plan.add_argument("--output", type=Path)
    rewrite_plan.add_argument("--force", action="store_true")
    rewrite_plan.set_defaults(func=command_create_rewrite_plan)

    branch_diff_report = subparsers.add_parser(
        "create-branch-diff-report",
        help="Create a v0.6 branch diff report for review.",
    )
    project_arg(branch_diff_report)
    branch_diff_report.add_argument("--branch", default="main")
    branch_diff_report.add_argument("--base-branch", default="main")
    branch_diff_report.add_argument("--divergence-analysis", type=Path)
    branch_diff_report.add_argument("--replacement-routes", type=Path)
    branch_diff_report.add_argument("--plot-node-map", type=Path)
    branch_diff_report.add_argument("--output", type=Path)
    branch_diff_report.add_argument("--force", action="store_true")
    branch_diff_report.set_defaults(func=command_create_branch_diff_report)

    create_patch = subparsers.add_parser("create-patch", help="Create a pending post-write patch.")
    project_arg(create_patch)
    create_patch.add_argument("--branch", default="main")
    create_patch.add_argument("--chapter", required=True)
    create_patch.add_argument("--source-draft", default="")
    create_patch.add_argument("--output", type=Path)
    create_patch.add_argument("--force", action="store_true")
    create_patch.set_defaults(func=command_create_patch)

    patch_review = subparsers.add_parser(
        "create-patch-review",
        help="Create a human-readable review report for a pending patch.",
    )
    project_arg(patch_review)
    patch_review.add_argument("--patch", required=True, type=Path)
    patch_review.add_argument("--output", type=Path)
    patch_review.add_argument("--force", action="store_true")
    patch_review.set_defaults(func=command_create_patch_review)

    review_patch = subparsers.add_parser(
        "review-patch",
        help="Alias for create-patch-review; create a human-readable pending patch report.",
    )
    project_arg(review_patch)
    review_patch.add_argument("--patch", required=True, type=Path)
    review_patch.add_argument("--output", type=Path)
    review_patch.add_argument("--force", action="store_true")
    review_patch.set_defaults(func=command_create_patch_review)

    quality_report = subparsers.add_parser(
        "create-quality-report",
        help="Create a chapter quality-report template and optional review prompt.",
    )
    project_arg(quality_report)
    quality_report.add_argument("--branch", default="main")
    quality_report.add_argument("--chapter", required=True)
    quality_report.add_argument("--draft", type=Path)
    quality_report.add_argument("--context-pack", type=Path)
    quality_report.add_argument("--output", type=Path)
    quality_report.add_argument("--prompt-output", type=Path)
    quality_report.add_argument("--template-only", action="store_true")
    quality_report.add_argument("--with-prompt", action="store_true")
    quality_report.add_argument("--prompt-only", action="store_true")
    quality_report.add_argument("--severity", choices=("serious", "medium", "light", "all"), default="all")
    quality_report.add_argument("--force", action="store_true")
    quality_report.set_defaults(func=command_create_quality_report)

    apply_patch = subparsers.add_parser("apply-patch", help="Dry-run or apply a pending patch.")
    project_arg(apply_patch)
    apply_patch.add_argument("--patch", required=True, type=Path)
    apply_patch.add_argument("--confirm", action="store_true")
    apply_patch.add_argument("--confirm-major", action="store_true")
    apply_patch.set_defaults(func=command_apply_patch)

    validate = subparsers.add_parser("validate", help="Validate a novel project.")
    project_arg(validate)
    validate.set_defaults(func=command_validate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv or sys.argv[1:])
    try:
        return int(args.func(args))
    except StepFailed as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.code


if __name__ == "__main__":
    raise SystemExit(main())
