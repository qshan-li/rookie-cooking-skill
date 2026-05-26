---
name: rookie-cooking-skill
description: Use when generating, adapting, reviewing, or troubleshooting beginner-friendly cooking recipes with exact measurements, kitchen execution steps, failure diagnosis, cooking principles, substitutions, food-safety checks, equipment adaptation, taste preferences, full recipe output, or printable kitchen versions.
---

# Rookie Cooking Skill

Turn vague cooking instructions into executable kitchen documents for beginners. Prefer quantified parameters, visible state checks, and failure diagnosis over generic recipe prose.

## Default Assumptions

Use these defaults when the user only names a dish:

- 2 servings.
- Home gas stove or induction cooktop.
- Ordinary wok or frying pan.
- No kitchen thermometer.
- Phone timer available.
- Kitchen scale available; also provide no-scale fallback checks.
- Normal salt tolerance unless the user says otherwise.

Do not ask follow-up questions before producing a useful first recipe unless a safety-critical constraint is missing.

## Mode Selection

- **Target mode**: User names a dish. Output both the full explanation version and kitchen execution version.
- **Quick mode**: User asks for fast cooking. Keep steps short, keep one-line reasons, retain state checks and diagnosis.
- **Precise mode**: User asks for grams, temperature, scaling, or tighter control. Include measured ranges and equipment adjustments.
- **Learning mode**: User asks why something works or failed. Output a principle card and link it back to usable dishes.
- **Troubleshooting mode**: User reports a failed result. Diagnose likely causes, next adjustment, and safety risk.

## Output Rules

Every generated recipe must include:

1. Dish name, servings, total time, difficulty, target result, equipment, and calories estimate when reasonable.
2. Ingredients with grams or milliliters, plus practical no-scale fallback.
3. Step-by-step operations. Every full-version step includes operation, time, heat, target state, failure signal, and why.
4. Safety notes for meat, poultry, seafood, eggs, leftovers, thawing, reheating, or cross-contamination.
5. Substitutions for likely missing ingredients or tools.
6. Failure diagnosis with possible cause and next adjustment.
7. Related principles from `principles/`.
8. A kitchen execution version that is short enough to scan while cooking.

Avoid unqualified vague terms such as "适量", "少许", "一会儿", "炒熟", "差不多", or "收汁即可". If a sensory description is needed, pair it with a measurable range or state standard.

## Resource Navigation

Read only the files needed for the user request:

- Full recipe output: `templates/recipe-full.md`.
- Kitchen execution output: `templates/recipe-kitchen.md`.
- Principle explanation: `templates/principle-card.md` and relevant files in `principles/`.
- Failure diagnosis: `templates/failure-diagnosis.md`.
- Recipe quality review: `templates/recipe-review-checklist.md`.
- Defaults and assumptions: `references/defaults.md`.
- Heat wording and equipment mapping: `references/heat-levels.md` and `references/equipment-profiles.md`.
- Unit conversion and no-scale fallback: `references/unit-conversion.md`.
- Serving changes: `references/scaling-rules.md`.
- Food safety: `references/food-safety-rules.md`.
- User preferences and memory boundaries: `references/cooking-memory-layer.md`.
- Recipe source and license notes: `references/source-notes.md`.
- Real kitchen validation rules: `references/kitchen-validation.md`.
- Printable output: `assets/print.css` and `scripts/render_recipe_pdf.py`.
- Repository quality gates: `scripts/check_skill_completeness.py`.
- Apply real kitchen validation records: `scripts/apply_kitchen_validation.py`.
- Create blank kitchen validation records: `scripts/new_kitchen_validation_record.py`.
- Prepare benchmark validation packet: `scripts/prepare_benchmark_validation.py`.

Use existing recipes under `recipes/` as examples only after checking that they passed the review checklist.

## Generation Workflow

1. Identify the mode and serving count.
2. Read relevant memory only when the user request benefits from preferences, equipment, dislikes, or prior failures.
3. Apply defaults, then apply explicit user overrides for this request.
4. Load the relevant template and reference files.
5. Generate the full version first unless the user asked only for quick or kitchen output.
6. Generate the kitchen version after the full version.
7. Run the review checklist mentally before finalizing. Fix missing timing, heat, state, failure, safety, or substitution details.
8. State which preferences or assumptions were used.

Safety overrides taste. When safety and texture conflict, keep the safety requirement and explain the texture tradeoff.

## Memory Rules

Distinguish temporary overrides from durable preferences:

- "今天 4 人份" applies only to the current recipe.
- "以后默认 4 人份" can become a durable serving preference.
- Equipment, taste, and serving habits may be suggested for memory.
- Allergy, health, religion, pregnancy, or long-term dietary restrictions require explicit confirmation before durable memory.
- Low-confidence memory can be suggested, not silently enforced.

Always provide a way to view, change, delete, or temporarily ignore remembered preferences when memory is used.
