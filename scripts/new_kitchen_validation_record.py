#!/usr/bin/env python3
"""Create a blank JSON kitchen validation record for a recipe."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
from typing import Any


BLANK_FIELDS = {
    "cook": "",
    "environment": "",
    "servings": "",
    "ingredient_weights": "",
    "step_times": "",
    "heat_notes": "",
    "state_checks": "",
    "failure_points": "",
    "changes": "",
}


def recipe_title(recipe_markdown: str) -> str:
    for line in recipe_markdown.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            if title:
                return title
    raise ValueError("recipe markdown is missing a top-level # heading")


def build_record(recipe_markdown: str, *, date: str) -> dict[str, Any]:
    return {
        "recipe": recipe_title(recipe_markdown),
        "date": date,
        **BLANK_FIELDS,
        "conclusion": "keep-passed",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a blank kitchen validation JSON record.")
    parser.add_argument("recipe", type=Path, help="Recipe Markdown file.")
    parser.add_argument("output", type=Path, help="Output JSON path.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Validation date.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    recipe_markdown = args.recipe.read_text(encoding="utf-8")
    record = build_record(recipe_markdown, date=args.date)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
