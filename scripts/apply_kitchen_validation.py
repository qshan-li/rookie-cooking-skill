#!/usr/bin/env python3
"""Append a real kitchen validation record to a recipe."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Mapping


REQUIRED_FIELDS = (
    "date",
    "cook",
    "environment",
    "servings",
    "ingredient_weights",
    "step_times",
    "heat_notes",
    "state_checks",
    "failure_points",
    "changes",
    "conclusion",
)

CONCLUSION_VALUES = {"keep-passed", "revise-needed", "validated-candidate"}
STATUS_PATTERN = re.compile(r"状态：`(?:draft|passed|validated)`")


def validate_record(record: Mapping[str, object]) -> None:
    missing = [field for field in REQUIRED_FIELDS if not str(record.get(field, "")).strip()]
    if missing:
        raise ValueError(f"validation record missing fields: {', '.join(missing)}")

    conclusion = str(record["conclusion"])
    if conclusion not in CONCLUSION_VALUES:
        allowed = ", ".join(sorted(CONCLUSION_VALUES))
        raise ValueError(f"invalid conclusion {conclusion!r}; expected one of: {allowed}")


def format_record(record: Mapping[str, object]) -> str:
    validate_record(record)
    return f"""### 实测 {record["date"]}

- 操作者：{record["cook"]}
- 环境：{record["environment"]}
- 实际份量：{record["servings"]}
- 实际克数：{record["ingredient_weights"]}
- 实际时间：{record["step_times"]}
- 火力记录：{record["heat_notes"]}
- 状态判断：{record["state_checks"]}
- 失败点：{record["failure_points"]}
- 修正建议：{record["changes"]}
- 结论：`{record["conclusion"]}`
"""


def set_validated_status(recipe_markdown: str) -> str:
    if not STATUS_PATTERN.search(recipe_markdown):
        raise ValueError("recipe is missing review status")
    return STATUS_PATTERN.sub("状态：`validated`", recipe_markdown, count=1)


def append_validation_record(recipe_markdown: str, rendered_record: str) -> str:
    recipe_markdown = recipe_markdown.rstrip()
    if "## 厨房实测记录" in recipe_markdown:
        return f"{recipe_markdown}\n\n{rendered_record.strip()}\n"
    return f"{recipe_markdown}\n\n## 厨房实测记录\n\n{rendered_record.strip()}\n"


def apply_record(
    recipe_markdown: str,
    record: Mapping[str, object],
    *,
    mark_validated: bool,
) -> str:
    validate_record(record)
    if mark_validated and record["conclusion"] != "validated-candidate":
        raise ValueError("mark_validated requires conclusion `validated-candidate`")

    updated = append_validation_record(recipe_markdown, format_record(record))
    if mark_validated:
        updated = set_validated_status(updated)
    return updated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply a kitchen validation JSON record to a recipe.")
    parser.add_argument("recipe", type=Path, help="Recipe Markdown file to update.")
    parser.add_argument("record", type=Path, help="JSON validation record.")
    parser.add_argument(
        "--mark-validated",
        action="store_true",
        help="Set review status to validated. Requires conclusion validated-candidate.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    recipe_markdown = args.recipe.read_text(encoding="utf-8")
    record = json.loads(args.record.read_text(encoding="utf-8"))
    updated = apply_record(recipe_markdown, record, mark_validated=args.mark_validated)
    args.recipe.write_text(updated, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
