#!/usr/bin/env python3
"""Check rookie-cooking-skill structure, recipe quality gates, and validation status."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys


BENCHMARK_RECIPE_FILENAMES = {
    "fan-qie-chao-dan.md",
    "qing-jiao-rou-si.md",
    "zheng-dan-geng.md",
    "qing-chao-xiao-qing-cai.md",
    "hong-shao-rou.md",
}

MIN_RECIPE_COUNT = 20
MIN_PRINCIPLE_COUNT = 10

REQUIRED_STRUCTURE_PATHS = (
    "SKILL.md",
    "agents/openai.yaml",
    "docs/howtocook-migration-manifest.md",
    "templates/recipe-full.md",
    "templates/recipe-kitchen.md",
    "templates/principle-card.md",
    "templates/failure-diagnosis.md",
    "templates/recipe-review-checklist.md",
    "templates/meal-plan.md",
    "templates/recipe-changelog.md",
    "templates/imported-recipe-review.md",
    "references/defaults.md",
    "references/heat-levels.md",
    "references/unit-conversion.md",
    "references/equipment-profiles.md",
    "references/scaling-rules.md",
    "references/food-safety-rules.md",
    "references/cooking-memory-layer.md",
    "references/user-profile.example.yaml",
    "references/feedback-log.example.yaml",
    "references/memory-merge-rules.md",
    "references/meal-planning-rules.md",
    "references/recipe-versioning.md",
    "references/recipe-import-rules.md",
    "references/source-notes.md",
    "scripts/cooking_memory.py",
    "scripts/run_agent_skill_qa.py",
    "scripts/sync_skill_install.py",
    "scripts/render_recipe_pdf.py",
    "assets/print.css",
)

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

APPLIED_PREFERENCE_SNIPPETS = (
    "已使用偏好 / 假设",
    "本次使用的偏好 / 假设",
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

PRINCIPLE_ID_PATTERN = re.compile(r"`[a-z][a-z0-9-]*`")
STATUS_PATTERN = re.compile(r"状态：`([^`]+)`")
HOWTOCOOK_SOURCE_MARKER = "Anduin2017/HowToCook"


@dataclass(frozen=True)
class CheckResult:
    errors: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def recipe_paths(root: Path) -> list[Path]:
    recipes_root = root / "recipes"
    return sorted(recipes_root.glob("*/*.md"))


def principle_paths(root: Path) -> list[Path]:
    principles_root = root / "principles"
    return sorted(principles_root.glob("*.md"))


def validate_structure(root: Path) -> list[str]:
    errors: list[str] = []
    for path in REQUIRED_STRUCTURE_PATHS:
        if not (root / path).exists():
            errors.append(f"missing required path: {path}")
    return errors


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


def has_howtocook_source(markdown_text: str) -> bool:
    return HOWTOCOOK_SOURCE_MARKER in markdown_text


def validate_migration_manifest(markdown_text: str, howtocook_recipe_paths: list[Path]) -> list[str]:
    errors: list[str] = []
    if "source-needs-normalization" in markdown_text:
        errors.append("migration manifest contains unresolved source status: source-needs-normalization")

    for path in howtocook_recipe_paths:
        target = path.as_posix()
        if target not in markdown_text:
            errors.append(f"migration manifest missing target: {target}")
    return errors


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

    if not any(snippet in markdown_text for snippet in APPLIED_PREFERENCE_SNIPPETS):
        errors.append("missing applied preferences or assumptions")

    status = review_status(markdown_text)
    if status not in {"draft", "passed", "validated"}:
        errors.append("missing review status `draft`, `passed`, or `validated`")
    elif status == "draft" and has_howtocook_source(markdown_text):
        errors.append("HowToCook source recipes must be `passed` or `validated`")

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
    errors.extend(validate_structure(root))

    source_notes_path = root / "references" / "source-notes.md"
    if not source_notes_path.exists():
        source_notes = ""
    else:
        source_notes = source_notes_path.read_text(encoding="utf-8")

    principles = principle_paths(root)
    if len(principles) < MIN_PRINCIPLE_COUNT:
        errors.append(f"principle_count={len(principles)} required={MIN_PRINCIPLE_COUNT}")

    recipes = recipe_paths(root)
    if not recipes:
        errors.append("no recipe files found under recipes/*/*.md")
    elif len(recipes) < MIN_RECIPE_COUNT:
        errors.append(f"recipe_count={len(recipes)} required={MIN_RECIPE_COUNT}")

    benchmark_validated = 0
    howtocook_recipe_paths: list[Path] = []
    for path in recipes:
        markdown_text = path.read_text(encoding="utf-8")
        relative_path = path.relative_to(root)
        recipe_errors = validate_recipe(markdown_text, relative_path, source_notes)
        for error in recipe_errors:
            errors.append(f"{relative_path}: {error}")
        if has_howtocook_source(markdown_text):
            howtocook_recipe_paths.append(relative_path)
        if path.name in BENCHMARK_RECIPE_FILENAMES and review_status(markdown_text) == "validated":
            benchmark_validated += 1

    migration_manifest_path = root / "docs" / "howtocook-migration-manifest.md"
    if migration_manifest_path.exists():
        migration_manifest = migration_manifest_path.read_text(encoding="utf-8")
        errors.extend(validate_migration_manifest(migration_manifest, howtocook_recipe_paths))

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
