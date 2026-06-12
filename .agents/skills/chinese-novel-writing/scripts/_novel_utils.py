"""Small standard-library helpers for chinese-novel-writing scripts."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def yaml_quote(value: object) -> str:
    text = "" if value is None else str(value)
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def parse_scalar(value: str) -> object:
    value = value.strip()
    if value in {"", '""', "''"}:
        return ""
    if value == "[]":
        return []
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip('"').strip("'") for item in inner.split(",")]
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value


def format_scalar(value: object) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(yaml_quote(item) for item in value) + "]"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return yaml_quote(value)


def parse_mapping_list(path: Path, key: str) -> list[dict[str, object]]:
    """Parse a simple YAML list of mappings under a top-level key."""
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    records: list[dict[str, object]] = []
    in_section = False
    current: dict[str, object] | None = None
    for line in lines:
        if not in_section:
            if line.strip() == f"{key}:":
                in_section = True
            continue
        if line and not line.startswith(" "):
            break
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            if current:
                records.append(current)
            current = {}
            rest = stripped[2:]
            if ":" in rest:
                k, v = rest.split(":", 1)
                current[k.strip()] = parse_scalar(v)
        elif current is not None and ":" in stripped:
            k, v = stripped.split(":", 1)
            current[k.strip()] = parse_scalar(v)
    if current:
        records.append(current)
    return records


def parse_progress(path: Path) -> dict[str, object]:
    data: dict[str, object] = {
        "schema_version": "",
        "project": {},
        "settings": {},
        "chunks": {},
        "chapters": {},
        "batches": {},
    }
    if not path.exists():
        return data
    section = ""
    entry = ""
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()
        if indent == 0 and ":" in stripped and not stripped.endswith(":"):
            k, v = stripped.split(":", 1)
            data[k.strip()] = parse_scalar(v)
            continue
        if indent == 0 and stripped.endswith(":"):
            section = stripped[:-1]
            entry = ""
            data.setdefault(section, {})
            continue
        if section in {"project", "settings"} and indent == 2 and ":" in stripped:
            k, v = stripped.split(":", 1)
            section_data = data.setdefault(section, {})
            assert isinstance(section_data, dict)
            section_data[k.strip()] = parse_scalar(v)
            continue
        if section in {"chunks", "chapters", "batches"}:
            section_data = data.setdefault(section, {})
            assert isinstance(section_data, dict)
            if indent == 2 and stripped.endswith(":"):
                entry = stripped[:-1]
                section_data.setdefault(entry, {})
            elif indent == 4 and entry and ":" in stripped:
                k, v = stripped.split(":", 1)
                entry_data = section_data.setdefault(entry, {})
                assert isinstance(entry_data, dict)
                entry_data[k.strip()] = parse_scalar(v)
    return data


def write_progress(path: Path, data: dict[str, object]) -> None:
    lines: list[str] = []
    if data.get("schema_version"):
        lines.append(f"schema_version: {format_scalar(data.get('schema_version'))}")
        lines.append("")
    for section in ("project", "settings"):
        lines.append(f"{section}:")
        section_data = data.get(section, {})
        if isinstance(section_data, dict):
            for key, value in section_data.items():
                lines.append(f"  {key}: {format_scalar(value)}")
        lines.append("")
    for section in ("chunks", "chapters", "batches"):
        lines.append(f"{section}:")
        section_data = data.get(section, {})
        if isinstance(section_data, dict) and section_data:
            for entry_id, fields in section_data.items():
                lines.append(f"  {entry_id}:")
                if isinstance(fields, dict):
                    for key, value in fields.items():
                        lines.append(f"    {key}: {format_scalar(value)}")
        else:
            lines.append("  # empty")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def set_top_level_value(path: Path, key: str, value: object) -> None:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    replacement = f"{key}: {format_scalar(value)}"
    for index, line in enumerate(lines):
        if line.startswith(f"{key}:"):
            lines[index] = replacement
            break
    else:
        lines.append(replacement)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def safe_relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)
