"""Helpers for deterministic v0.6 rewrite artifact scripts."""

from __future__ import annotations

from pathlib import Path

from _novel_utils import now_iso, parse_scalar, safe_relative, yaml_quote


SCHEMA_VERSION = "0.6"
IMPACT_RADIUS_CHOICES = (
    "level_1_local",
    "level_2_relationship",
    "level_3_main_plot",
    "level_4_world_rule",
)


def read_text(path: Path, limit: int | None = None) -> str:
    if not path.exists() or not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if limit is not None and len(text) > limit:
        return text[:limit].rstrip() + "\n...[truncated]"
    return text


def top_value(path: Path, key: str) -> str:
    text = read_text(path)
    for line in text.splitlines():
        if line.startswith(f"{key}:"):
            return str(parse_scalar(line.split(":", 1)[1]))
    return ""


def project_name(project: Path) -> str:
    config = project / "project_config.yaml"
    return top_value(config, "project_name") or project.name


def ensure_project_branch(project: Path, branch: str) -> Path:
    if not project.exists():
        raise FileNotFoundError(f"project not found: {project}")
    branch_dir = project / "branches" / branch
    if not branch_dir.exists():
        raise FileNotFoundError(f"branch not found: {branch_dir}")
    return branch_dir


def rewrite_dir(project: Path, branch: str) -> Path:
    return project / "branches" / branch / "rewrite"


def write_text_if_allowed(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"output exists: {path}. Use --force to overwrite.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def yaml_list(values: list[str], indent: str = "") -> list[str]:
    if not values:
        return [f"{indent}[]"]
    return [f"{indent}- {yaml_quote(value)}" for value in values]


def yaml_block_list(lines: list[str], key: str, values: list[str], indent: str = "") -> None:
    lines.append(f"{indent}{key}:")
    lines.extend(yaml_list(values, indent + "  "))


def branch_source_scope(project: Path, branch: str, base_branch: str) -> tuple[list[str], list[str]]:
    candidates = [
        "project_config.yaml",
        "canon/original_plot_map.md",
        "canon/canon_bible.md",
        f"branches/{base_branch}/outline.md",
        f"branches/{base_branch}/chapter_outlines.md",
        f"branches/{base_branch}/timeline.yaml",
        f"branches/{branch}/branch_config.yaml",
        f"branches/{branch}/divergence_point.yaml",
        f"branches/{branch}/outline.md",
        f"branches/{branch}/chapter_outlines.md",
        f"branches/{branch}/timeline.yaml",
        f"branches/{branch}/foreshadowing.yaml",
        f"branches/{branch}/causal_impact_log.md",
        "context_packs/latest_context_pack.md",
    ]
    existing: list[str] = []
    missing: list[str] = []
    for rel in candidates:
        path = project / rel
        if path.exists() and path.is_file():
            existing.append(rel)
        else:
            missing.append(rel)
    return existing, missing


def artifact_status(path: Path) -> str:
    return "present" if path.exists() else "missing"


def frontmatter(metadata: dict[str, str]) -> str:
    lines = ["---"]
    for key, value in metadata.items():
        lines.append(f"{key}: {yaml_quote(value)}")
    lines.append("---")
    return "\n".join(lines)


def rel(path: Path, project: Path) -> str:
    return safe_relative(path, project)


def timestamp_id(prefix: str, branch: str) -> str:
    stamp = now_iso().replace(":", "").replace("+", "_")
    safe_branch = branch.replace("\\", "-").replace("/", "-").replace(" ", "_")
    return f"{prefix}_{safe_branch}_{stamp}"
