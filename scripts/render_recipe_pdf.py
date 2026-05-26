#!/usr/bin/env python3
"""Render a recipe's kitchen section to a printable PDF."""

from __future__ import annotations

import argparse
import html as html_lib
import shutil
import subprocess
from pathlib import Path

import markdown


KITCHEN_HEADING = "## 厨房执行版"
REVIEW_HEADING = "### Review"
DEFAULT_ARTIFACT_HOME = Path.home() / ".rookie-cooking"
DEFAULT_OUTPUT_DIR = DEFAULT_ARTIFACT_HOME / "output" / "pdf"
DEFAULT_TMP_DIR = DEFAULT_ARTIFACT_HOME / "tmp" / "pdfs"
DEFAULT_CSS_PATH = Path("assets/print.css")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render the kitchen execution section of a Markdown recipe to PDF."
    )
    parser.add_argument("recipe", type=Path, nargs="?", help="Path to a Markdown recipe file.")
    parser.add_argument(
        "--kitchen-markdown",
        type=Path,
        help="Path to a temporary kitchen execution Markdown file.",
    )
    parser.add_argument(
        "--title",
        help="Recipe title for --kitchen-markdown input.",
    )
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
    parser.add_argument(
        "--print",
        action="store_true",
        help="Send the generated kitchen PDF to the system printer.",
    )
    parser.add_argument(
        "--printer",
        help="Optional printer name passed to lp or lpr.",
    )
    parser.add_argument(
        "--list-printers",
        action="store_true",
        help="List available printer devices and exit.",
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


def recipe_title(recipe_markdown: str) -> str:
    for line in recipe_markdown.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            if title:
                return title
    raise ValueError("Recipe markdown is missing a top-level # heading")


def strip_kitchen_heading(kitchen_markdown: str) -> str:
    lines = kitchen_markdown.splitlines()
    if lines and lines[0].strip() == KITCHEN_HEADING:
        return "\n".join(lines[1:]).strip()
    return kitchen_markdown.strip()


def kitchen_output_stem(stem: str) -> str:
    if stem.endswith("-kitchen"):
        return stem
    return f"{stem}-kitchen"


def build_html(kitchen_markdown: str, css_text: str, title: str) -> str:
    escaped_title = html_lib.escape(title)
    body = markdown.markdown(
        strip_kitchen_heading(kitchen_markdown),
        extensions=["tables", "sane_lists"],
        output_format="html5",
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{escaped_title}</title>
  <style>
{css_text}
  </style>
</head>
<body>
  <main>
<h1>{escaped_title}</h1>
{body}
  </main>
</body>
</html>
"""


def render_source(args: argparse.Namespace) -> tuple[str, str, str]:
    if args.recipe is not None and args.kitchen_markdown is not None:
        raise ValueError("Use either a recipe path or --kitchen-markdown, not both.")

    if args.kitchen_markdown is not None:
        kitchen_markdown = read_text(args.kitchen_markdown)
        if args.title:
            return args.kitchen_markdown.stem, args.title, kitchen_markdown
        try:
            return args.kitchen_markdown.stem, recipe_title(kitchen_markdown), kitchen_markdown
        except ValueError as error:
            raise ValueError(
                "--title is required when --kitchen-markdown has no top-level # heading."
            ) from error

    if args.recipe is None:
        raise ValueError("Recipe path is required unless --kitchen-markdown or --list-printers is used.")

    recipe_markdown = read_text(args.recipe)
    return args.recipe.stem, recipe_title(recipe_markdown), extract_kitchen_section(recipe_markdown)


def find_chrome() -> str:
    for executable in ("google-chrome", "chromium", "chromium-browser"):
        path = shutil.which(executable)
        if path:
            return path
    raise RuntimeError(
        "No Chrome/Chromium executable found. Install google-chrome or chromium to render PDFs."
    )


def list_printers() -> list[str]:
    lpstat_path = shutil.which("lpstat")
    if not lpstat_path:
        raise RuntimeError("No lpstat executable found. Install CUPS tools to list printers.")

    completed = subprocess.run(
        [lpstat_path, "-e"],
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "Printer listing failed:\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


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


def print_pdf(pdf_path: Path, printer: str | None = None) -> None:
    lp_path = shutil.which("lp")
    if lp_path:
        command = [lp_path]
        if printer:
            command.extend(["-d", printer])
        command.append(str(pdf_path))
    else:
        lpr_path = shutil.which("lpr")
        if not lpr_path:
            raise RuntimeError("No lp or lpr executable found. Install a system print command first.")
        command = [lpr_path]
        if printer:
            command.extend(["-P", printer])
        command.append(str(pdf_path))

    completed = subprocess.run(command, check=False, text=True, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(
            "System printing failed:\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )


def main() -> None:
    args = parse_args()
    if args.list_printers:
        for printer in list_printers():
            print(printer)
        return

    output_dir = args.output_dir
    tmp_dir = args.tmp_dir
    css_path = args.css
    kitchen_markdown_path = args.kitchen_markdown

    css_text = read_text(css_path)
    output_stem, title, kitchen_markdown = render_source(args)
    html = build_html(kitchen_markdown, css_text, title)

    output_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    html_path = (tmp_dir / f"{output_stem}.html").resolve()
    pdf_path = (output_dir / f"{kitchen_output_stem(output_stem)}.pdf").resolve()
    html_path.write_text(html, encoding="utf-8")

    render_pdf(find_chrome(), html_path, pdf_path)
    if args.print:
        print_pdf(pdf_path, args.printer)
    if kitchen_markdown_path is not None:
        kitchen_markdown_path.unlink()
    print(pdf_path)


if __name__ == "__main__":
    main()
