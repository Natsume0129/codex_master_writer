"""Deterministic helpers for v0.8 style, voice, scene, and revision artifacts."""

from __future__ import annotations

from pathlib import Path

from _novel_utils import chapter_label_candidates, normalize_chapter_label, now_iso, safe_relative, yaml_quote


SCHEMA_VERSION = "0.8"


def ensure_branch(project: Path, branch: str) -> Path:
    if not project.exists():
        raise FileNotFoundError(f"project not found: {project}")
    branch_dir = project / "branches" / branch
    if not branch_dir.exists():
        raise FileNotFoundError(f"branch not found: {branch_dir}")
    return branch_dir


def resolve_project_relative(project: Path, path: Path | str | None) -> Path | None:
    if path is None or str(path) == "":
        return None
    candidate = Path(path)
    return candidate if candidate.is_absolute() else (project / candidate).resolve()


def write_text_if_allowed(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"output exists: {path}. Use --force to overwrite.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_head(path: Path, limit: int = 5000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        return data[:limit].rstrip() + "\n...[truncated]"
    return data.strip()


def artifact_status(path: Path | None) -> str:
    return "present" if path and path.exists() else "missing"


def rel(path: Path | None, project: Path) -> str:
    return safe_relative(path, project) if path else ""


def default_context_pack(project: Path) -> Path:
    return project / "context_packs" / "latest_context_pack.md"


def default_style_profile(project: Path, branch: str) -> Path:
    return project / "branches" / branch / "style" / "style_profile.yaml"


def default_voice_sheet(project: Path, branch: str) -> Path:
    return project / "branches" / branch / "style" / "character_voice_sheet.yaml"


def default_scene_outline(project: Path, branch: str, chapter_label: str) -> Path:
    return project / "branches" / branch / "outlines" / f"{chapter_label}_scene_outline.yaml"


def default_style_audit(project: Path, branch: str, chapter_label: str) -> Path:
    return project / "branches" / branch / "reviews" / f"{chapter_label}_style_audit.md"


def default_revision_plan(project: Path, branch: str, chapter_label: str) -> Path:
    return project / "branches" / branch / "revision" / f"{chapter_label}_revision_plan.md"


def default_draft(project: Path, branch: str, chapter_label: str) -> Path:
    drafts_dir = project / "branches" / branch / "drafts"
    for suffix in (".md", ".txt", ".yaml"):
        path = drafts_dir / f"{chapter_label}{suffix}"
        if path.exists():
            return path
    return drafts_dir / f"{chapter_label}.md"


def default_function_card(project: Path, branch: str, chapter: str, chapter_label: str) -> Path:
    cards_dir = project / "branches" / branch / "chapter_function_cards"
    for candidate in chapter_label_candidates(chapter):
        path = cards_dir / f"{candidate}_function_card.yaml"
        if path.exists():
            return path
    return cards_dir / f"{chapter_label}_function_card.yaml"


def yaml_list(lines: list[str], key: str, values: list[str], indent: str = "") -> None:
    lines.append(f"{indent}{key}:")
    if values:
        lines.extend(f"{indent}  - {yaml_quote(value)}" for value in values)
    else:
        lines.append(f"{indent}  []")


def missing_paths(project: Path, paths: list[tuple[str, Path | None]]) -> list[str]:
    missing: list[str] = []
    for label, path in paths:
        if path is None or not path.exists():
            missing.append(label)
    return missing


def split_csvish(raw: list[str] | str) -> list[str]:
    values = raw if isinstance(raw, list) else [raw]
    result: list[str] = []
    for value in values:
        for item in str(value).replace(",", " ").split():
            if item.strip():
                result.append(item.strip())
    return list(dict.fromkeys(result))


def chapter_label(chapter: str) -> str:
    return normalize_chapter_label(chapter)


def frontmatter(metadata: dict[str, object]) -> str:
    lines = ["---"]
    for key, value in metadata.items():
        lines.append(f"{key}: {yaml_quote(value)}")
    lines.append("---")
    return "\n".join(lines)


def project_name(project: Path) -> str:
    config = project / "project_config.yaml"
    if not config.exists():
        return project.name
    for line in config.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("project_name:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'") or project.name
    return project.name


def source_scope(project: Path, branch: str, context_pack: Path | None, source: Path | None) -> list[str]:
    values = [f"branches/{branch}/branch_config.yaml"]
    if context_pack:
        values.append(rel(context_pack, project))
    if source:
        values.append(rel(source, project))
    return list(dict.fromkeys(value for value in values if value))


def limited_source_note(project: Path, source: Path | None) -> str:
    if not source:
        return ""
    if not source.exists():
        return f"missing source: {rel(source, project)}"
    size = source.stat().st_size
    if size > 20_000:
        return f"source too large for prompt embedding; path={rel(source, project)} size={size}"
    return f"source available for model review; path={rel(source, project)} size={size}"

