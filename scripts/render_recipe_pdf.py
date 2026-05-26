#!/usr/bin/env python3
"""Render a recipe's kitchen section to a printable PDF."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import markdown


KITCHEN_HEADING = "## 厨房执行版"
REVIEW_HEADING = "### Review"
DEFAULT_OUTPUT_DIR = Path("output/pdf")
DEFAULT_TMP_DIR = Path("tmp/pdfs")
DEFAULT_CSS_PATH = Path("assets/print.css")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render the kitchen execution section of a Markdown recipe to PDF."
    )
    parser.add_argument("recipe", type=Path, help="Path to a Markdown recipe file.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for final PDF output.",
    )
    parser.add_argument(
        "--tmp-dir",
        type=Path,
        default=DEFAULT_TMP_DIR,
        help="Directory for intermediate HTML files.",
    )
    parser.add_argument(
        "--css",
        type=Path,
        default=DEFAULT_CSS_PATH,
        help="Print CSS file.",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path.read_text(encoding="utf-8")


def extract_kitchen_section(recipe_markdown: str) -> str:
    start = recipe_markdown.find(KITCHEN_HEADING)
    if start == -1:
        raise ValueError(f"Recipe is missing required heading: {KITCHEN_HEADING}")

    review_start = recipe_markdown.find(REVIEW_HEADING, start)
    if review_start == -1:
        return recipe_markdown[start:].strip()

    return recipe_markdown[start:review_start].strip()


def build_html(kitchen_markdown: str, css_text: str, title: str) -> str:
    body = markdown.markdown(
        kitchen_markdown,
        extensions=["tables", "sane_lists"],
        output_format="html5",
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
{css_text}
  </style>
</head>
<body>
  <main>
{body}
  </main>
</body>
</html>
"""


def find_chrome() -> str:
    for executable in ("google-chrome", "chromium", "chromium-browser"):
        path = shutil.which(executable)
        if path:
            return path
    raise RuntimeError(
        "No Chrome/Chromium executable found. Install google-chrome or chromium to render PDFs."
    )


def render_pdf(chrome: str, html_path: Path, pdf_path: Path) -> None:
    command = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        html_path.as_uri(),
    ]
    completed = subprocess.run(command, check=False, text=True, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(
            "Chrome PDF rendering failed:\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise RuntimeError(f"Chrome did not create a usable PDF: {pdf_path}")


def main() -> None:
    args = parse_args()
    recipe_path = args.recipe
    output_dir = args.output_dir
    tmp_dir = args.tmp_dir
    css_path = args.css

    recipe_markdown = read_text(recipe_path)
    css_text = read_text(css_path)
    kitchen_markdown = extract_kitchen_section(recipe_markdown)
    title = recipe_path.stem
    html = build_html(kitchen_markdown, css_text, title)

    output_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    html_path = (tmp_dir / f"{recipe_path.stem}.html").resolve()
    pdf_path = (output_dir / f"{recipe_path.stem}-kitchen.pdf").resolve()
    html_path.write_text(html, encoding="utf-8")

    render_pdf(find_chrome(), html_path, pdf_path)
    print(pdf_path)


if __name__ == "__main__":
    main()
