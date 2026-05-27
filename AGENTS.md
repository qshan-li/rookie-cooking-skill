# Repository Guidelines

## Project Structure & Module Organization

This is a documentation-first cooking skill repository. Core skill instructions live in `SKILL.md`, with agent configuration in `agents/openai.yaml`. Requirements and planning documents are in `docs/`. Reusable recipe and review formats live in `templates/`. Recipe content is grouped by dish type under `recipes/`, for example `recipes/vegetable/fan-qie-chao-dan.md`. Cooking principles belong in `principles/`, shared lookup material in `references/`, styling assets in `assets/`, validation utilities in `scripts/`, IPP network printing in `scripts/printer.py`, and automated checks in `tests/`.

## Build, Test, and Development Commands

No package manager or build system is required at the moment. Use Python directly:

- `python scripts/runtime_harness.py doctor` records the local Python command and Python-dependent capabilities in `~/.rookie-cooking/runtime.json`.
- `python -m unittest discover -s tests` runs the full test suite.
- `python scripts/check_skill_completeness.py` validates required skill structure, principle counts, recipe counts, source notes, and kitchen validation status.
- `python scripts/render_recipe_pdf.py <recipe.md>` renders a recipe using `assets/print.css` when PDF output is needed.
- `python scripts/render_recipe_pdf.py --test-printer <ip>` tests connectivity to a network printer.
- `python scripts/render_recipe_pdf.py --set-default <ip>` sets the default printer in config.

Run commands from the repository root so relative paths resolve correctly.

## Coding Style & Naming Conventions

Keep changes small and specific to the current task. Markdown should be concise, actionable, and implementation-oriented. Use kebab-case for content filenames, such as `qing-zheng-lu-yu.md` or `protein-denaturation.md`. Keep recipe files aligned with `templates/recipe-full.md` and include explicit measurements, timing, heat level, target state, failure signals, and review status. Python scripts should use standard-library style, clear function names, `pathlib.Path` for paths, and explicit errors rather than silent fallbacks.

## Testing Guidelines

Tests use Python `unittest` and live in `tests/` with names like `test_check_skill_completeness.py`. Add tests when changing validation behavior, script inputs or outputs, required repository structure, or recipe status rules. Prefer focused tests that create temporary fixture directories instead of mutating real recipe content. Before finishing, run `python -m unittest discover -s tests`.

## Commit & Pull Request Guidelines

Recent history uses short imperative commit subjects, for example `Enforce skill structure gate` and `Relax kitchen validation acceptance`. Keep each commit to one logical change and avoid unrelated formatting churn. Pull requests should include a brief problem statement, a summary of changed files or rules, validation commands run, and any content-quality tradeoffs. Link related issues when available. Include generated PDFs or screenshots only when reviewing rendered recipe output.

## Content Quality Rules

Preserve the separation between recipes, principles, references, and templates. Do not bury general cooking theory inside a single recipe when it belongs in `principles/` or `references/`. Every new recipe should be executable by a kitchen rookie: avoid vague instructions like “适量”, “大火”, or “炒熟” unless they are paired with concrete measurements, equipment assumptions, and observable state checks.
