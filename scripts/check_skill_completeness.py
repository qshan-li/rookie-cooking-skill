#!/usr/bin/env python3
"""Check rookie-cooking-skill structure, recipe quality gates, and validation status."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys


BENCHMARK_RECIPE_FILENAMES = {
    "tomato-egg.md",
    "qingjiao-rousi.md",
    "steamed-egg.md",
    "stir-fried-greens.md",
    "hongshaorou.md",
}

BANNED_UNQUALIFIED_TERMS = (
    "适量",
    "少许",
    "一会儿",
    "差不多熟了",
    "炒熟",
    "收汁即可",
)

REQUIRED_RECIPE_SNIPPETS = (
    "## 完整解释版",
    "## 厨房执行版",
    "| 步骤 | 操作 | 时间 | 火力 | 目标状态 | 失败信号 | 为什么 |",
    "### 食品安全",
)

REQUIRED_VALIDATION_FIELDS = (
    "- 操作者：",
    "- 环境：",
    "- 实际份量：",
    "- 实际克数：",
    "- 实际时间：",
    "- 火力记录：",
    "- 状态判断：",
    "- 失败点：",
    "- 修正建议：",
    "- 结论：",
)

PRINCIPLE_ID_PATTERN = re.compile(r"`(?:protein-denaturation|maillard|starch-gelatinization|velveting|salt-water-migration|seasoning-balance|blanching|oil-temperature-smoke-point|wok-heat|food-safety-temperature)`")
STATUS_PATTERN = re.compile(r"状态：`([^`]+)`")


@dataclass(frozen=True)
class CheckResult:
    errors: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def recipe_paths(root: Path) -> list[Path]:
    recipes_root = root / "recipes"
    return sorted(recipes_root.glob("*/*.md"))


def first_heading(markdown_text: str) -> str:
    for line in markdown_text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def review_status(markdown_text: str) -> str | None:
    match = STATUS_PATTERN.search(markdown_text)
    if not match:
        return None
    return match.group(1)


def validate_kitchen_validation_status(markdown_text: str, path: Path) -> list[str]:
    status = review_status(markdown_text)
    if status != "validated":
        return []

    errors: list[str] = []
    if "## 厨房实测记录" not in markdown_text:
        errors.append("validated status requires ## 厨房实测记录")
        return errors

    if "### 实测 " not in markdown_text:
        errors.append("validated status requires at least one ### 实测 record")

    for field in REQUIRED_VALIDATION_FIELDS:
        if field not in markdown_text:
            errors.append(f"validated status missing field {field}")

    if "`validated-candidate`" not in markdown_text:
        errors.append("validated status requires conclusion `validated-candidate`")

    return errors


def validate_recipe(markdown_text: str, path: Path, source_notes: str) -> list[str]:
    errors: list[str] = []
    for snippet in REQUIRED_RECIPE_SNIPPETS:
        if snippet not in markdown_text:
            errors.append(f"missing required snippet: {snippet}")

    status = review_status(markdown_text)
    if status not in {"passed", "validated"}:
        errors.append("missing review status `passed` or `validated`")

    if not PRINCIPLE_ID_PATTERN.search(markdown_text):
        errors.append("missing known principle card reference")

    for term in BANNED_UNQUALIFIED_TERMS:
        if term in markdown_text:
            errors.append(f"contains banned unqualified term: {term}")

    heading = first_heading(markdown_text)
    if not heading:
        errors.append("missing top-level recipe heading")
    elif heading not in source_notes:
        errors.append(f"missing source note for recipe heading: {heading}")

    errors.extend(validate_kitchen_validation_status(markdown_text, path))
    return errors


def check_repository(root: Path, required_benchmark_validations: int = 0) -> CheckResult:
    errors: list[str] = []
    source_notes_path = root / "references" / "source-notes.md"
    if not source_notes_path.exists():
        return CheckResult(errors=["missing references/source-notes.md"])

    source_notes = source_notes_path.read_text(encoding="utf-8")
    recipes = recipe_paths(root)
    if not recipes:
        errors.append("no recipe files found under recipes/*/*.md")

    benchmark_validated = 0
    for path in recipes:
        markdown_text = path.read_text(encoding="utf-8")
        recipe_errors = validate_recipe(markdown_text, path.relative_to(root), source_notes)
        for error in recipe_errors:
            errors.append(f"{path.relative_to(root)}: {error}")
        if path.name in BENCHMARK_RECIPE_FILENAMES and review_status(markdown_text) == "validated":
            benchmark_validated += 1

    if required_benchmark_validations and benchmark_validated < required_benchmark_validations:
        errors.append(
            f"benchmark_validated={benchmark_validated} required={required_benchmark_validations}"
        )

    return CheckResult(errors=errors)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check rookie cooking skill completeness gates.")
    parser.add_argument("--root", type=Path, default=Path("."), help="Skill repository root.")
    parser.add_argument(
        "--require-benchmark-validations",
        type=int,
        default=0,
        help="Require at least this many benchmark recipes to be marked validated.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = check_repository(args.root, args.require_benchmark_validations)
    if result.ok:
        print("OK")
        return 0

    for error in result.errors:
        print(error, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
