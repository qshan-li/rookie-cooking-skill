#!/usr/bin/env python3
"""Prepare benchmark recipe PDFs and blank kitchen validation records."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import subprocess
import sys


BENCHMARK_RECIPE_PATHS = (
    Path("recipes/vegetable/fan-qie-chao-dan.md"),
    Path("recipes/meat/qing-jiao-rou-si.md"),
    Path("recipes/soup/zheng-dan-geng.md"),
    Path("recipes/vegetable/qing-chao-xiao-qing-cai.md"),
    Path("recipes/meat/hong-shao-rou.md"),
)

DEFAULT_VALIDATION_DIR = Path("output/validation")


def benchmark_recipes(root: Path) -> list[Path]:
    return [root / recipe for recipe in BENCHMARK_RECIPE_PATHS]


def validation_record_path(output_dir: Path, recipe_path: Path) -> Path:
    return output_dir / f"{recipe_path.stem}-validation.json"


def run_command(command: list[str]) -> None:
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"command failed with exit {completed.returncode}: {' '.join(command)}")


def prepare_benchmark_validation(root: Path, validation_dir: Path, record_date: str) -> None:
    render_script = root / "scripts" / "render_recipe_pdf.py"
    record_script = root / "scripts" / "new_kitchen_validation_record.py"
    validation_dir.mkdir(parents=True, exist_ok=True)

    for recipe in benchmark_recipes(root):
        if not recipe.exists():
            raise FileNotFoundError(f"benchmark recipe not found: {recipe}")

        record_path = validation_record_path(validation_dir, recipe)
        run_command([sys.executable, str(render_script), str(recipe)])
        run_command([sys.executable, str(record_script), str(recipe), str(record_path), "--date", record_date])
        print(record_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render benchmark kitchen PDFs and create blank validation JSON records."
    )
    parser.add_argument("--root", type=Path, default=Path("."), help="Skill repository root.")
    parser.add_argument(
        "--validation-dir",
        type=Path,
        default=DEFAULT_VALIDATION_DIR,
        help="Directory for blank validation JSON records.",
    )
    parser.add_argument("--date", default=date.today().isoformat(), help="Validation record date.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    prepare_benchmark_validation(args.root, args.validation_dir, args.date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
