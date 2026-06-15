"""Deterministic retrieval-index helpers for chinese-novel-writing v0.7."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from _novel_utils import now_iso, parse_scalar, safe_relative, yaml_quote


SCHEMA_VERSION = "0.7"
LIST_FIELDS = (
    "keywords",
    "characters",
    "locations",
    "items",
    "organizations",
    "terms",
    "plot_threads",
    "foreshadowing",
    "timeline_ids",
    "source",
)
TEXT_FIELDS = (
    "title",
    "summary",
    "notes",
    "keywords",
    "characters",
    "locations",
    "items",
    "organizations",
    "terms",
    "plot_threads",
    "foreshadowing",
    "source_file",
)
SOURCE_TYPE_WEIGHTS = {
    "chapter_card": 14,
    "chunk_card": 12,
    "volume_summary": 10,
    "canon": 13,
    "bible": 13,
    "branch_config": 10,
    "divergence_point": 11,
    "rewrite_artifact": 12,
    "pending_patch": 8,
    "review": 8,
    "summary": 9,
    "index": 4,
}
STATUS_WEIGHTS = {
    "confirmed": 8,
    "user_override": 8,
    "inferred": 4,
    "draft": 2,
    "uncertain": 1,
    "deprecated": -8,
}
CONFIDENCE_WEIGHTS = {
    "high": 5,
    "medium": 3,
    "low": 1,
    "unknown": 0,
}


def read_text_limited(path: Path, limit: int = 30000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        return data[:limit].rstrip() + "\n...[truncated]"
    return data


def write_text_if_allowed(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"output exists: {path}. Use --force to overwrite.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def resolve_project_relative(project: Path, value: Path | str | None) -> Path | None:
    if value is None or str(value) == "":
        return None
    path = Path(value)
    return path if path.is_absolute() else (project / path).resolve()


def normalize(text: object) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def split_terms(text: str) -> list[str]:
    raw = normalize(text)
    parts = [part for part in re.split(r"[\s,，;；、|/]+", raw) if part]
    if raw and raw not in parts:
        parts.insert(0, raw)
    return list(dict.fromkeys(parts))


def parse_list_value(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    if not text or text in {"[]", "{}"}:
        return []
    parsed = parse_scalar(text)
    if isinstance(parsed, list):
        return [str(item).strip() for item in parsed if str(item).strip()]
    if "," in text:
        return [item.strip().strip('"').strip("'") for item in text.strip("[]").split(",") if item.strip()]
    return [text.strip('"').strip("'")]


def parse_yamlish_metadata(text: str) -> dict[str, object]:
    data: dict[str, object] = {}
    current_list = ""
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()
        if current_list and indent > 0 and stripped.startswith("- "):
            values = data.setdefault(current_list, [])
            if isinstance(values, list):
                item = stripped[2:].strip()
                if ":" in item:
                    key, value = item.split(":", 1)
                    values.append({key.strip(): parse_scalar(value)})
                else:
                    values.append(str(parse_scalar(item)))
            continue
        current_list = ""
        if ":" not in stripped:
            continue
        key, value = stripped.lstrip("- ").split(":", 1)
        key = key.strip()
        value = value.strip()
        if key in LIST_FIELDS and value in {"", "[]"}:
            data[key] = [] if value == "[]" else []
            current_list = key
        elif key in LIST_FIELDS:
            data[key] = parse_list_value(value)
        elif key in {
            "id",
            "entry_id",
            "chapter",
            "chapter_id",
            "volume",
            "title",
            "name",
            "summary",
            "notes",
            "status",
            "confidence",
            "updated_at",
            "created_at",
            "generated_at",
            "branch",
        }:
            data[key] = parse_scalar(value)
    return data


def extract_frontmatter(text: str) -> tuple[dict[str, object], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            frontmatter = "\n".join(lines[1:index])
            body = "\n".join(lines[index + 1 :])
            return parse_yamlish_metadata(frontmatter), body
    return {}, text


def first_heading(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return ""


def short_markdown_summary(body: str, limit: int = 500) -> str:
    in_code = False
    parts: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith("|") or stripped.startswith("---"):
            continue
        parts.append(stripped)
        if sum(len(item) for item in parts) >= limit:
            break
    text = " ".join(parts).strip()
    return text[:limit].rstrip()


def source_type_for(rel: str) -> str:
    rel_norm = rel.replace("\\", "/")
    if rel_norm.startswith("extracted/chunk_cards/"):
        return "chunk_card"
    if rel_norm.startswith("extracted/chapter_cards/"):
        return "chapter_card"
    if rel_norm.startswith("extracted/volume_summaries/"):
        return "volume_summary"
    if rel_norm.startswith("canon/"):
        return "canon"
    if rel_norm.startswith("bible/"):
        return "bible"
    if rel_norm.startswith("indexes/"):
        return "index"
    if rel_norm.endswith("/branch_config.yaml"):
        return "branch_config"
    if rel_norm.endswith("/divergence_point.yaml"):
        return "divergence_point"
    if "/rewrite/" in rel_norm:
        return "rewrite_artifact"
    if rel_norm.startswith("pending_updates/"):
        return "pending_patch"
    if "/reviews/" in rel_norm:
        return "review"
    if "/chapter_summaries/" in rel_norm or "/summaries/" in rel_norm:
        return "summary"
    return "index"


def branch_for_rel(rel: str) -> str:
    rel_norm = rel.replace("\\", "/")
    parts = rel_norm.split("/")
    if len(parts) >= 2 and parts[0] == "branches":
        return parts[1]
    return "main"


def chapter_for_path(rel: str, metadata: dict[str, object]) -> str:
    for key in ("chapter", "chapter_id"):
        value = str(metadata.get(key, "") or "")
        if value:
            return value
    match = re.search(r"chapter[_-]?(\d+)", rel, flags=re.IGNORECASE)
    if match:
        return f"chapter_{int(match.group(1)):03d}"
    return ""


def volume_for_path(rel: str, metadata: dict[str, object]) -> str:
    value = str(metadata.get("volume", "") or "")
    if value:
        return value
    match = re.search(r"volume[_-]?(\d+)", rel, flags=re.IGNORECASE)
    return match.group(1) if match else ""


def safe_entry_id(source_type: str, rel: str) -> str:
    digest = hashlib.sha1(rel.encode("utf-8")).hexdigest()[:10]
    slug = re.sub(r"[^A-Za-z0-9_]+", "_", rel.replace("\\", "/")).strip("_")
    return f"{source_type}_{slug[:80]}_{digest}"


def listify_metadata(data: dict[str, object], key: str) -> list[str]:
    return parse_list_value(data.get(key, []))


def build_entry(project: Path, path: Path) -> dict[str, object]:
    rel = safe_relative(path, project).replace("\\", "/")
    source_type = source_type_for(rel)
    text = read_text_limited(path)
    frontmatter, body = extract_frontmatter(text)
    metadata = parse_yamlish_metadata(text)
    metadata.update({key: value for key, value in frontmatter.items() if value not in {"", []}})
    title = str(metadata.get("title") or metadata.get("name") or first_heading(body) or path.stem)
    summary = str(metadata.get("summary") or short_markdown_summary(body if body else text))
    if len(summary) > 600:
        summary = summary[:600].rstrip() + "..."
    status = str(metadata.get("status") or ("draft" if source_type in {"pending_patch", "review", "rewrite_artifact"} else "unknown"))
    confidence = str(metadata.get("confidence") or "unknown")
    updated_at = str(metadata.get("updated_at") or metadata.get("generated_at") or metadata.get("created_at") or "")
    source_values = listify_metadata(metadata, "source")
    if not source_values:
        source_values = [rel]
    return {
        "schema_version": SCHEMA_VERSION,
        "entry_id": safe_entry_id(source_type, rel),
        "source_type": source_type,
        "source_file": rel,
        "branch": str(metadata.get("branch") or branch_for_rel(rel)),
        "chapter": chapter_for_path(rel, metadata),
        "volume": volume_for_path(rel, metadata),
        "title": title[:160],
        "summary": summary,
        "keywords": listify_metadata(metadata, "keywords"),
        "characters": listify_metadata(metadata, "characters"),
        "locations": listify_metadata(metadata, "locations"),
        "items": listify_metadata(metadata, "items"),
        "organizations": listify_metadata(metadata, "organizations"),
        "terms": listify_metadata(metadata, "terms"),
        "plot_threads": listify_metadata(metadata, "plot_threads"),
        "foreshadowing": listify_metadata(metadata, "foreshadowing"),
        "timeline_ids": listify_metadata(metadata, "timeline_ids"),
        "status": status,
        "confidence": confidence,
        "source": source_values,
        "updated_at": updated_at,
        "notes": "Retrieval aid only; verify facts in source_file before use.",
    }


def allowed_candidate_paths(project: Path, branch: str, include_branches: bool) -> list[Path]:
    patterns = [
        "extracted/chunk_cards/*.yaml",
        "extracted/chapter_cards/*.yaml",
        "extracted/volume_summaries/*.md",
        "canon/*.yaml",
        "canon/*.md",
        "bible/*.yaml",
        "bible/*.md",
        "indexes/*.yaml",
        "indexes/*.md",
        "pending_updates/*.yaml",
    ]
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(project.glob(pattern))
    branches_dir = project / "branches"
    branches = [branch]
    if include_branches and branches_dir.exists():
        branches = sorted(item.name for item in branches_dir.iterdir() if item.is_dir())
    for name in branches:
        base = branches_dir / name
        paths.extend(base.glob("branch_config.yaml"))
        paths.extend(base.glob("divergence_point.yaml"))
        paths.extend(base.glob("rewrite/*.yaml"))
        paths.extend(base.glob("summaries/*.md"))
        paths.extend(base.glob("chapter_summaries/*.md"))
        paths.extend(base.glob("reviews/*.md"))
    skipped = {
        "indexes/retrieval_index.md",
        "indexes/retrieval_query_report.md",
    }
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        rel = safe_relative(path, project).replace("\\", "/")
        if rel in skipped or rel.startswith("raw_text/") or rel.startswith("imports/source_texts/"):
            continue
        if rel not in seen:
            unique.append(path)
            seen.add(rel)
    return sorted(unique, key=lambda item: safe_relative(item, project).replace("\\", "/"))


def write_jsonl(path: Path, entries: list[dict[str, object]], force: bool) -> None:
    content = "".join(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n" for entry in entries)
    write_text_if_allowed(path, content, force)


def load_index(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        raise FileNotFoundError(f"retrieval index not found: {path}. Run build-retrieval-index.")
    entries: list[dict[str, object]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
        if isinstance(value, dict):
            entries.append(value)
    return entries


def entry_text(entry: dict[str, object]) -> str:
    parts: list[str] = []
    for field in TEXT_FIELDS:
        value = entry.get(field, "")
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
        else:
            parts.append(str(value))
    return normalize(" ".join(parts))


def match_terms(entry: dict[str, object], terms: list[str]) -> list[str]:
    text = entry_text(entry)
    return [term for term in terms if term and term in text]


def score_entry(
    entry: dict[str, object],
    query_terms: list[str],
    branch: str = "",
    chapter: str = "",
    filters: dict[str, list[str]] | None = None,
    source_types: list[str] | None = None,
) -> dict[str, object]:
    filters = filters or {}
    source_type = str(entry.get("source_type", ""))
    if source_types and source_type not in source_types:
        return {}
    if branch and str(entry.get("branch", "")) not in {branch, "main", ""}:
        return {}
    if chapter and str(entry.get("chapter", "")) and str(entry.get("chapter", "")) != str(chapter):
        chapter_match = False
    else:
        chapter_match = bool(chapter and str(entry.get("chapter", "")) == str(chapter))
    matched = match_terms(entry, query_terms)
    entity_matches: list[str] = []
    for key, values in filters.items():
        if not values:
            continue
        entry_values = [normalize(item) for item in parse_list_value(entry.get(key, []))]
        wanted = [normalize(item) for item in values]
        for value in wanted:
            if value and (value in entry_values or any(value in item for item in entry_values)):
                entity_matches.append(f"{key}:{value}")
    if query_terms and not matched and not entity_matches and not chapter_match:
        return {}
    score = 0
    score += len(matched) * 10
    score += len(entity_matches) * 12
    score += SOURCE_TYPE_WEIGHTS.get(source_type, 1)
    score += STATUS_WEIGHTS.get(str(entry.get("status", "unknown")), 0)
    score += CONFIDENCE_WEIGHTS.get(str(entry.get("confidence", "unknown")), 0)
    if branch and str(entry.get("branch", "")) == branch:
        score += 8
    elif branch and str(entry.get("branch", "")) == "main":
        score += 2
    if chapter_match:
        score += 10
    return {
        "entry": entry,
        "score": score,
        "matched_terms": list(dict.fromkeys([*matched, *entity_matches])),
        "reason": "; ".join(
            item
            for item in [
                f"query matches: {', '.join(matched)}" if matched else "",
                f"entity matches: {', '.join(entity_matches)}" if entity_matches else "",
                f"branch match: {branch}" if branch and str(entry.get("branch", "")) == branch else "",
                f"chapter match: {chapter}" if chapter_match else "",
                f"source_type weight: {source_type}",
            ]
            if item
        ),
    }


def query_entries(
    entries: list[dict[str, object]],
    query: str = "",
    branch: str = "",
    chapter: str = "",
    filters: dict[str, list[str]] | None = None,
    source_types: list[str] | None = None,
    top_k: int = 20,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    terms = split_terms(query)
    scored: list[dict[str, object]] = []
    omitted: list[dict[str, object]] = []
    for entry in entries:
        result = score_entry(entry, terms, branch, chapter, filters, source_types)
        if result:
            scored.append(result)
        else:
            omitted.append(entry)
    scored.sort(
        key=lambda item: (
            -int(item["score"]),
            str(item["entry"].get("source_file", "")),
        )
    )
    return scored[: max(top_k, 0)], omitted + [item["entry"] for item in scored[max(top_k, 0) :]]


def selector_lines(results: list[dict[str, object]]) -> list[str]:
    lines: list[str] = []
    seen: set[str] = set()
    for result in results:
        entry = result["entry"]
        source = str(entry.get("source_file", ""))
        if source and source not in seen:
            lines.append(f"- source_file: {source}")
            seen.add(source)
    return lines


def timestamped_report_header(report_type: str, **metadata: object) -> str:
    lines = ["---", f"schema_version: {yaml_quote(SCHEMA_VERSION)}", f"report_type: {yaml_quote(report_type)}"]
    for key, value in metadata.items():
        lines.append(f"{key}: {yaml_quote(value)}")
    lines.append(f"generated_at: {yaml_quote(now_iso())}")
    lines.append("---")
    return "\n".join(lines)
