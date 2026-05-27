#!/usr/bin/env python3
"""Manage local rookie-cooking user preferences and feedback memory."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import json
import os
from pathlib import Path
import re
import sys
from typing import Any


PROFILE_FILE = "profile.yaml"
FEEDBACK_FILE = "feedback.jsonl"
CANDIDATES_FILE = "memory-candidates.jsonl"
LEARNING_FILE = "learning-log.jsonl"
DEFAULT_MEMORY_DIR = ".rookie-cooking"
ENV_MEMORY_HOME = "ROOKIE_COOKING_HOME"
DRAFTS_DIR = "drafts"
RECIPES_DIR = "recipes"

SENSITIVE_PATH_PARTS = {
    "allergies",
    "health",
    "health_goals",
    "pregnancy",
    "pregnancy_or_child",
    "child",
    "children",
    "religion",
    "religious",
    "disease",
    "medical",
    "sensitive_constraints",
    "long_term_diet",
}


class MemoryDataError(ValueError):
    """Raised when memory data is invalid or an unsafe write is requested."""


def memory_root(env: dict[str, str] | None = None) -> Path:
    values = os.environ if env is None else env
    override = values.get(ENV_MEMORY_HOME)
    if override:
        return Path(override).expanduser()
    return Path.home() / DEFAULT_MEMORY_DIR


def profile_path(root: Path) -> Path:
    return root / PROFILE_FILE


def feedback_path(root: Path) -> Path:
    return root / FEEDBACK_FILE


def candidates_path(root: Path) -> Path:
    return root / CANDIDATES_FILE


def learning_path(root: Path) -> Path:
    return root / LEARNING_FILE


def drafts_dir(root: Path) -> Path:
    return root / DRAFTS_DIR


def user_recipes_dir(root: Path) -> Path:
    return root / RECIPES_DIR


def default_profile() -> dict[str, Any]:
    return {
        "profile_version": 1,
        "updated_at": datetime.now().date().isoformat(),
        "defaults": {"servings": 2},
        "taste": {
            "salt_level": "normal",
            "oil_level": "normal",
            "spice_level": "mild",
            "sweetness": "normal",
            "sourness": "normal",
        },
        "equipment": {
            "stove_type": "unknown",
            "pan_type": "ordinary-wok",
            "has_scale": True,
            "has_thermometer": False,
            "has_oven": "unknown",
            "has_air_fryer": "unknown",
        },
        "dislikes": {
            "ingredients": [],
            "aromatics": [],
        },
        "household_members": [
            {
                "member_id": "self",
                "display_name": "self",
                "role": "primary",
                "taste": {
                    "salt_level": "normal",
                    "oil_level": "normal",
                    "spice_level": "mild",
                },
                "dislikes": {
                    "ingredients": [],
                    "aromatics": [],
                },
                "sensitive_constraints": {
                    "allergies": [],
                    "health_goals": [],
                    "pregnancy_or_child": False,
                },
                "notes": "Default cooking target.",
            }
        ],
        "recipe_preferences": {},
        "feedback_history": [],
        "memory_metadata": {
            "source": "local",
            "confidence": 1.0,
            "write_policy": "explicit-confirmation",
        },
    }


def parse_scalar(raw_value: str) -> Any:
    value = raw_value.strip()
    if value == "":
        return ""
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "None"}:
        return None
    if value[0:1] in {'"', "'"}:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value.strip("\"'")
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def format_scalar(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if value == []:
        return "[]"
    if value == {}:
        return "{}"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def yaml_lines(data: Any, indent: int = 0) -> list[str]:
    space = " " * indent
    if isinstance(data, dict):
        lines: list[str] = []
        for key, value in data.items():
            if isinstance(value, (dict, list)) and value:
                lines.append(f"{space}{key}:")
                lines.extend(yaml_lines(value, indent + 2))
            else:
                lines.append(f"{space}{key}: {format_scalar(value)}")
        return lines
    if isinstance(data, list):
        lines = []
        for item in data:
            if isinstance(item, (dict, list)) and item:
                lines.append(f"{space}-")
                lines.extend(yaml_lines(item, indent + 2))
            else:
                lines.append(f"{space}- {format_scalar(item)}")
        return lines
    return [f"{space}{format_scalar(data)}"]


def dump_yaml(data: dict[str, Any]) -> str:
    return "\n".join(yaml_lines(data)) + "\n"


def prepared_yaml_lines(text: str) -> list[tuple[int, str]]:
    prepared: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        prepared.append((indent, raw_line[indent:].rstrip()))
    return prepared


def parse_yaml_block(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    if index >= len(lines):
        return {}, index

    current_indent, content = lines[index]
    if current_indent < indent:
        return {}, index
    if current_indent > indent:
        raise MemoryDataError(f"Unexpected indentation before: {content}")

    if content == "-" or content.startswith("- "):
        items: list[Any] = []
        while index < len(lines):
            current_indent, content = lines[index]
            if current_indent != indent or not (content == "-" or content.startswith("- ")):
                break
            item_text = "" if content == "-" else content[2:].strip()
            index += 1
            if not item_text:
                item, index = parse_yaml_block(lines, index, indent + 2)
                items.append(item)
                continue

            if ":" in item_text:
                key, raw_value = split_mapping_line(item_text)
                item_dict: dict[str, Any] = {}
                if raw_value:
                    item_dict[key] = parse_scalar(raw_value)
                else:
                    item_dict[key], index = parse_yaml_block(lines, index, indent + 2)
                if index < len(lines) and lines[index][0] > indent:
                    nested, index = parse_yaml_block(lines, index, indent + 2)
                    if isinstance(nested, dict):
                        item_dict.update(nested)
                    else:
                        raise MemoryDataError(f"List item cannot merge nested value: {item_text}")
                items.append(item_dict)
            else:
                items.append(parse_scalar(item_text))
        return items, index

    mapping: dict[str, Any] = {}
    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent != indent or content == "-" or content.startswith("- "):
            break
        key, raw_value = split_mapping_line(content)
        index += 1
        if raw_value:
            mapping[key] = parse_scalar(raw_value)
        elif index < len(lines) and lines[index][0] > indent:
            mapping[key], index = parse_yaml_block(lines, index, indent + 2)
        else:
            mapping[key] = {}
    return mapping, index


def split_mapping_line(content: str) -> tuple[str, str]:
    if ":" not in content:
        raise MemoryDataError(f"Expected key: value line, got: {content}")
    key, raw_value = content.split(":", 1)
    key = key.strip()
    if not key:
        raise MemoryDataError(f"Missing key before colon in line: {content}")
    return key, raw_value.strip()


def load_yaml(text: str) -> dict[str, Any]:
    lines = prepared_yaml_lines(text)
    if not lines:
        return {}
    data, index = parse_yaml_block(lines, 0, lines[0][0])
    if index != len(lines):
        raise MemoryDataError(f"Unable to parse line: {lines[index][1]}")
    if not isinstance(data, dict):
        raise MemoryDataError("Profile root must be a mapping")
    return data


def read_profile(root: Path) -> dict[str, Any]:
    path = profile_path(root)
    try:
        profile = load_yaml(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise MemoryDataError(f"Unable to read profile.yaml: {error}") from error
    except MemoryDataError as error:
        raise MemoryDataError(f"Malformed profile.yaml: {error}") from error
    if not isinstance(profile, dict):
        raise MemoryDataError("Malformed profile.yaml: root must be a mapping")
    return profile


def write_profile(root: Path, profile: dict[str, Any]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    path = profile_path(root)
    tmp_path = root / f"{PROFILE_FILE}.tmp"
    tmp_path.write_text(dump_yaml(profile), encoding="utf-8")
    os.replace(tmp_path, path)


def init_profile(root: Path, overwrite: bool = False) -> dict[str, Any]:
    path = profile_path(root)
    if path.exists() and not overwrite:
        raise MemoryDataError(f"Profile already exists: {path}")
    profile = default_profile()
    write_profile(root, profile)
    return profile


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.exists():
        return [], []
    entries: list[dict[str, Any]] = []
    warnings: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            warnings.append(f"Skipped malformed JSONL line {line_number}")
            continue
        if isinstance(value, dict):
            entries.append(value)
        else:
            warnings.append(f"Skipped non-object JSONL line {line_number}")
    return entries, warnings


def append_jsonl(path: Path, entry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(entry, ensure_ascii=False, sort_keys=True))
        output.write("\n")


def source_value(value: Any, source: str) -> dict[str, Any]:
    return {"value": value, "source": source}


def select_household_members(profile: dict[str, Any], diners: list[str]) -> list[dict[str, Any]]:
    members = profile.get("household_members", [])
    if not isinstance(members, list):
        return []
    diner_set = set(diners or ["self"])
    selected: list[dict[str, Any]] = []
    for member in members:
        if not isinstance(member, dict):
            continue
        member_id = str(member.get("member_id", ""))
        display_name = str(member.get("display_name", ""))
        if member_id in diner_set or display_name in diner_set:
            selected.append(member)
    return selected


def format_adjustment(adjustment: dict[str, Any]) -> str:
    parts = []
    for key, value in adjustment.items():
        if key == "note":
            continue
        parts.append(f"{key}={value}")
    return ", ".join(parts)


def read_memory(root: Path, dish: str, diners: list[str]) -> dict[str, Any]:
    if not profile_path(root).exists():
        return {
            "memory_found": False,
            "applied": {},
            "notices": ["No cooking profile found; using skill defaults."],
        }

    profile = read_profile(root)
    applied: dict[str, Any] = {}
    notices: list[str] = []

    defaults = profile.get("defaults", {})
    if isinstance(defaults, dict) and "servings" in defaults:
        applied["servings"] = source_value(defaults["servings"], "profile.defaults")

    equipment = profile.get("equipment", {})
    if isinstance(equipment, dict):
        applied["equipment"] = {
            key: source_value(value, "profile.equipment") for key, value in equipment.items()
        }

    taste = profile.get("taste", {})
    if isinstance(taste, dict):
        applied["taste"] = {key: source_value(value, "profile.taste") for key, value in taste.items()}

    members = select_household_members(profile, diners)
    if members:
        applied["household_members"] = members

    recipe_preferences = profile.get("recipe_preferences", {})
    if isinstance(recipe_preferences, dict) and dish in recipe_preferences:
        applied["recipe_preferences"] = {
            dish: source_value(recipe_preferences[dish], "profile.recipe_preferences")
        }

    feedback_entries, feedback_warnings = read_jsonl(feedback_path(root))
    notices.extend(feedback_warnings)
    recipe_feedback = []
    for entry in feedback_entries:
        if entry.get("recipe_id") != dish:
            continue
        adjustment = entry.get("suggested_adjustment", {})
        if not isinstance(adjustment, dict):
            adjustment = {}
        status = str(entry.get("status", "pending-confirmation"))
        candidate = entry.get("memory_candidate", {})
        confidence = candidate.get("confidence") if isinstance(candidate, dict) else None
        label = "default" if status in {"confirmed", "confirmed-memory"} else "suggestion"
        recipe_feedback.append(
            {
                "recipe_id": dish,
                "adjustment": format_adjustment(adjustment),
                "source": FEEDBACK_FILE,
                "status": status,
                "confidence": confidence,
                "label": label,
            }
        )
    if recipe_feedback:
        applied["recipe_feedback"] = recipe_feedback

    return {
        "memory_found": True,
        "applied": applied,
        "notices": notices,
    }


def path_is_sensitive(dotted_path: str) -> bool:
    path_parts = {part.lower() for part in dotted_path.replace("-", "_").split(".")}
    return bool(path_parts & SENSITIVE_PATH_PARTS)


def coerce_assignment_value(value: Any) -> Any:
    if isinstance(value, str):
        return parse_scalar(value)
    return value


def set_dotted_value(target: Any, dotted_path: str, value: Any) -> None:
    parts = dotted_path.split(".")
    current = target
    for index, part in enumerate(parts[:-1]):
        next_part = parts[index + 1]
        if part.isdigit():
            if not isinstance(current, list):
                raise MemoryDataError(f"Path segment requires a list: {part}")
            item_index = int(part)
            while len(current) <= item_index:
                current.append({} if not next_part.isdigit() else [])
            current = current[item_index]
            continue

        if not isinstance(current, dict):
            raise MemoryDataError(f"Path segment requires a mapping: {part}")
        if part not in current or current[part] is None:
            current[part] = [] if next_part.isdigit() else {}
        current = current[part]

    final_part = parts[-1]
    if final_part.isdigit():
        if not isinstance(current, list):
            raise MemoryDataError(f"Path segment requires a list: {final_part}")
        item_index = int(final_part)
        while len(current) <= item_index:
            current.append(None)
        current[item_index] = value
        return

    if not isinstance(current, dict):
        raise MemoryDataError(f"Final path segment requires a mapping: {final_part}")
    current[final_part] = value


def update_profile_value(
    root: Path,
    dotted_path: str,
    value: Any,
    confirm_sensitive: bool = False,
) -> dict[str, Any]:
    if path_is_sensitive(dotted_path) and not confirm_sensitive:
        raise MemoryDataError(
            f"Sensitive preference writes require explicit confirmation: {dotted_path}"
        )
    profile = read_profile(root)
    set_dotted_value(profile, dotted_path, coerce_assignment_value(value))
    profile["updated_at"] = datetime.now().date().isoformat()
    write_profile(root, profile)
    return profile


def adjustment_for_issue(issue: str) -> dict[str, Any]:
    if issue == "too_salty":
        return {
            "salt_multiplier": 0.85,
            "note": "Reduce salt first next time, then adjust before serving.",
        }
    if issue == "too_sweet":
        return {
            "sugar_multiplier": 0.85,
            "note": "Reduce sugar first next time, then adjust to taste.",
        }
    if issue == "too_bland":
        return {
            "salt_multiplier": 1.1,
            "note": "Increase seasoning slightly and check taste before serving.",
        }
    if issue == "too_watery":
        return {
            "batch_size_multiplier": 0.8,
            "note": "Cook a smaller batch, drain ingredients better, and add salt later.",
        }
    if issue == "burnt":
        return {
            "heat_level_note": "lower_heat",
            "note": "Lower heat, stir sooner, and add sugar later when relevant.",
        }
    if issue == "undercooked":
        return {
            "cook_time_multiplier": 1.15,
            "note": "Extend cooking time and use smaller cuts for safer doneness.",
        }
    if issue == "meat_dry":
        return {
            "cook_time_multiplier": 0.9,
            "note": "Shorten the final heating stage and check doneness earlier.",
        }
    if issue == "separated":
        return {
            "heat_level_note": "gentler_heat",
            "note": "Use gentler heat and adjust mixing or water ratio.",
        }
    return {
        "adjustment_note": f"Review issue before changing durable preferences: {issue}",
    }


def primary_adjustment_key(adjustment: dict[str, Any]) -> str:
    for key in adjustment:
        if key != "note":
            return key
    return "adjustment_note"


def make_event_id(recipe_id: str, issue: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    return f"{timestamp}-{recipe_id}-{issue}"


def add_feedback(
    root: Path,
    recipe_id: str,
    recipe_name: str,
    issue: str,
    result: str,
    observation: str,
    eaten_by: list[str],
) -> dict[str, Any]:
    adjustment = adjustment_for_issue(issue)
    adjustment_key = primary_adjustment_key(adjustment)
    candidate_id = f"candidate-{make_event_id(recipe_id, issue)}"
    candidate = {
        "candidate_id": candidate_id,
        "scope": "recipe-specific",
        "key": f"recipe_preferences.{recipe_id}.{adjustment_key}",
        "value": adjustment[adjustment_key],
        "confidence": 0.6,
        "source": "observed-feedback",
        "requires_confirmation": True,
        "status": "pending",
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    entry = {
        "entry_id": make_event_id(recipe_id, issue),
        "recipe_id": recipe_id,
        "recipe_name": recipe_name,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "eaten_by": eaten_by,
        "feedback": {
            "result": result,
            "issue": issue,
            "observation": observation,
        },
        "suggested_adjustment": adjustment,
        "memory_candidate": candidate,
        "status": "pending-confirmation",
    }
    append_jsonl(feedback_path(root), entry)
    append_jsonl(candidates_path(root), candidate)
    return entry


def latest_candidates(root: Path) -> dict[str, dict[str, Any]]:
    entries, _warnings = read_jsonl(candidates_path(root))
    latest: dict[str, dict[str, Any]] = {}
    for entry in entries:
        candidate_id = entry.get("candidate_id")
        if candidate_id:
            latest[str(candidate_id)] = entry
    return latest


def list_candidates(root: Path) -> list[dict[str, Any]]:
    return list(latest_candidates(root).values())


def candidate_for_id(root: Path, candidate_id: str) -> dict[str, Any]:
    candidates = latest_candidates(root)
    candidate = candidates.get(candidate_id)
    if candidate is None:
        raise MemoryDataError(f"Unknown memory candidate: {candidate_id}")
    return candidate


def confirm_candidate(root: Path, candidate_id: str) -> dict[str, Any]:
    candidate = candidate_for_id(root, candidate_id)
    if candidate.get("status") == "rejected":
        raise MemoryDataError(f"Cannot confirm rejected memory candidate: {candidate_id}")
    update_profile_value(
        root,
        str(candidate["key"]),
        candidate.get("value"),
        confirm_sensitive=True,
    )
    confirmed = deepcopy(candidate)
    confirmed["status"] = "confirmed"
    confirmed["confirmed_at"] = datetime.now().isoformat(timespec="seconds")
    append_jsonl(candidates_path(root), confirmed)
    return confirmed


def reject_candidate(root: Path, candidate_id: str) -> dict[str, Any]:
    candidate = candidate_for_id(root, candidate_id)
    rejected = deepcopy(candidate)
    rejected["status"] = "rejected"
    rejected["rejected_at"] = datetime.now().isoformat(timespec="seconds")
    append_jsonl(candidates_path(root), rejected)
    return rejected


def delete_memory(root: Path, target: str) -> dict[str, Any]:
    if target in {"profile", PROFILE_FILE}:
        profile_path(root).unlink(missing_ok=True)
        return {"deleted": PROFILE_FILE}
    if target in {"feedback", FEEDBACK_FILE}:
        feedback_path(root).unlink(missing_ok=True)
        return {"deleted": FEEDBACK_FILE}
    if target in {"candidates", CANDIDATES_FILE}:
        candidates_path(root).unlink(missing_ok=True)
        return {"deleted": CANDIDATES_FILE}
    if target in {"learning", "learning-log", LEARNING_FILE}:
        learning_path(root).unlink(missing_ok=True)
        return {"deleted": LEARNING_FILE}
    if target in latest_candidates(root):
        rejected = reject_candidate(root, target)
        return {"deleted": target, "status": rejected["status"]}
    profile = read_profile(root)
    remove_dotted_value(profile, target)
    write_profile(root, profile)
    return {"deleted": target}


def remove_dotted_value(target: Any, dotted_path: str) -> None:
    parts = dotted_path.split(".")
    current = target
    for part in parts[:-1]:
        if part.isdigit():
            current = current[int(part)]
        else:
            current = current[part]
    final_part = parts[-1]
    if final_part.isdigit():
        del current[int(final_part)]
    else:
        del current[final_part]


def ignore_once(dish: str) -> dict[str, Any]:
    return {"ignored_once": dish}


VALID_LEVELS = {"L1", "L2", "L3"}


def append_learning(root: Path, principle_id: str, level: str) -> dict[str, Any]:
    if level not in VALID_LEVELS:
        raise MemoryDataError(f"Invalid learning level: {level}. Must be one of {VALID_LEVELS}")
    entry = {
        "principle_id": principle_id,
        "level": level,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    append_jsonl(learning_path(root), entry)
    return entry


def query_learning(root: Path, principle_id: str) -> dict[str, Any]:
    entries, warnings = read_jsonl(learning_path(root))
    matches = [e for e in entries if e.get("principle_id") == principle_id]
    if not matches:
        return {"principle_id": principle_id, "found": False, "levels": [], "warnings": warnings}
    levels = [e.get("level") for e in matches if e.get("level") in VALID_LEVELS]
    latest = matches[-1]
    return {
        "principle_id": principle_id,
        "found": True,
        "levels": levels,
        "latest_level": latest.get("level"),
        "latest_timestamp": latest.get("timestamp"),
        "count": len(matches),
        "warnings": warnings,
    }


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def list_drafts(root: Path) -> dict[str, Any]:
    drafts_path = drafts_dir(root)
    if not drafts_path.exists():
        return {"drafts": [], "count": 0}
    drafts = []
    for path in sorted(drafts_path.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        status_match = re.search(r"status:\s*(\S+)", text)
        source_match = re.search(r"source:\s*(\S+)", text)
        name_match = re.search(r"name:\s*(\S+)", text)
        drafts.append({
            "filename": path.name,
            "name": name_match.group(1) if name_match else path.stem,
            "status": status_match.group(1) if status_match else "unknown",
            "source": source_match.group(1) if source_match else "unknown",
        })
    return {"drafts": drafts, "count": len(drafts)}


def list_user_recipes(root: Path) -> dict[str, Any]:
    recipes_path = user_recipes_dir(root)
    if not recipes_path.exists():
        return {"recipes": [], "count": 0}
    recipes = []
    for path in sorted(recipes_path.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        status_match = re.search(r"status:\s*(\S+)", text)
        source_match = re.search(r"source:\s*(\S+)", text)
        name_match = re.search(r"name:\s*(\S+)", text)
        recipes.append({
            "filename": path.name,
            "name": name_match.group(1) if name_match else path.stem,
            "status": status_match.group(1) if status_match else "unknown",
            "source": source_match.group(1) if source_match else "unknown",
        })
    return {"recipes": recipes, "count": len(recipes)}


def promote_draft(root: Path, filename: str) -> dict[str, Any]:
    src = drafts_dir(root) / filename
    if not src.exists():
        raise MemoryDataError(f"Draft not found: {src}")

    text = src.read_text(encoding="utf-8")

    # Update status from draft to passed
    if "status: draft" in text:
        text = text.replace("status: draft", "status: passed", 1)
    elif "status: passed" in text:
        pass  # Already passed, just move
    else:
        raise MemoryDataError(f"Cannot find 'status: draft' in {filename}")

    # Write to user recipes dir
    dst_dir = user_recipes_dir(root)
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / filename
    if dst.exists():
        raise MemoryDataError(f"Target already exists: {dst}")

    dst.write_text(text, encoding="utf-8")
    src.unlink()

    return {
        "promoted": filename,
        "from": str(src),
        "to": str(dst),
        "new_status": "passed",
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage local rookie cooking memory.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    read_parser = subparsers.add_parser("read", help="Read relevant cooking memory.")
    read_parser.add_argument("--dish", required=True)
    read_parser.add_argument("--diners", nargs="*", default=["self"])

    init_parser = subparsers.add_parser("init-profile", help="Create a default profile.")
    init_parser.add_argument("--force", action="store_true")

    subparsers.add_parser("view", help="Print the current profile.")

    update_parser = subparsers.add_parser("update-profile", help="Set a profile value.")
    update_parser.add_argument("--set", dest="assignments", action="append", required=True)
    update_parser.add_argument("--confirm-sensitive", action="store_true")

    feedback_parser = subparsers.add_parser("add-feedback", help="Add recipe feedback.")
    feedback_parser.add_argument("--recipe", required=True)
    feedback_parser.add_argument("--recipe-name", default="")
    feedback_parser.add_argument("--issue", required=True)
    feedback_parser.add_argument("--result", default="edible")
    feedback_parser.add_argument("--observation", default="")
    feedback_parser.add_argument("--diners", nargs="*", default=["self"])

    subparsers.add_parser("list-candidates", help="List memory candidates.")

    confirm_parser = subparsers.add_parser("confirm-candidate", help="Confirm a memory candidate.")
    confirm_parser.add_argument("candidate_id")

    reject_parser = subparsers.add_parser("reject-candidate", help="Reject a memory candidate.")
    reject_parser.add_argument("candidate_id")

    delete_parser = subparsers.add_parser("delete", help="Delete a memory file, path, or candidate.")
    delete_parser.add_argument("target")

    ignore_parser = subparsers.add_parser("ignore-once", help="Ignore dish memory for one response.")
    ignore_parser.add_argument("--dish", required=True)

    append_learning_parser = subparsers.add_parser("append-learning", help="Record a learning interaction.")
    append_learning_parser.add_argument("--principle", required=True, help="Principle ID (e.g. maillard).")
    append_learning_parser.add_argument("--level", required=True, choices=["L1", "L2", "L3"], help="Explanation depth level.")

    query_learning_parser = subparsers.add_parser("query-learning", help="Query learning history for a principle.")
    query_learning_parser.add_argument("--principle", required=True, help="Principle ID (e.g. maillard).")

    subparsers.add_parser("list-drafts", help="List draft recipes in ~/.rookie-cooking/drafts/.")

    subparsers.add_parser("list-user-recipes", help="List passed/validated recipes in ~/.rookie-cooking/recipes/.")

    promote_parser = subparsers.add_parser("promote-draft", help="Move a draft recipe to passed status.")
    promote_parser.add_argument("filename", help="Draft filename (e.g. ma-po-dou-fu.md).")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = memory_root()
    try:
        if args.command == "read":
            print_json(read_memory(root, args.dish, args.diners))
        elif args.command == "init-profile":
            print_json(init_profile(root, overwrite=args.force))
        elif args.command == "view":
            print_json(read_profile(root))
        elif args.command == "update-profile":
            profile: dict[str, Any] | None = None
            for assignment in args.assignments:
                if "=" not in assignment:
                    raise MemoryDataError(f"Expected --set path=value, got: {assignment}")
                dotted_path, value = assignment.split("=", 1)
                profile = update_profile_value(
                    root,
                    dotted_path,
                    value,
                    confirm_sensitive=args.confirm_sensitive,
                )
            print_json(profile)
        elif args.command == "add-feedback":
            print_json(
                add_feedback(
                    root,
                    recipe_id=args.recipe,
                    recipe_name=args.recipe_name or args.recipe,
                    issue=args.issue,
                    result=args.result,
                    observation=args.observation,
                    eaten_by=args.diners,
                )
            )
        elif args.command == "list-candidates":
            print_json(list_candidates(root))
        elif args.command == "confirm-candidate":
            print_json(confirm_candidate(root, args.candidate_id))
        elif args.command == "reject-candidate":
            print_json(reject_candidate(root, args.candidate_id))
        elif args.command == "delete":
            print_json(delete_memory(root, args.target))
        elif args.command == "ignore-once":
            print_json(ignore_once(args.dish))
        elif args.command == "append-learning":
            print_json(append_learning(root, args.principle, args.level))
        elif args.command == "query-learning":
            print_json(query_learning(root, args.principle))
        elif args.command == "list-drafts":
            print_json(list_drafts(root))
        elif args.command == "list-user-recipes":
            print_json(list_user_recipes(root))
        elif args.command == "promote-draft":
            print_json(promote_draft(root, args.filename))
        else:
            raise MemoryDataError(f"Unknown command: {args.command}")
    except MemoryDataError as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
