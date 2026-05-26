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

- **Recipe Generation**: User names a dish or asks how to cook one. Output both the full explanation version and kitchen execution version by default.
  - **Default output**: Full explanation version plus kitchen execution version.
  - **Quick output**: User asks for fast cooking. Keep steps short and reasons one-line, but retain measurements, timing, state checks, diagnosis, and safety notes.
  - **Precise output**: User asks for grams, temperature, scaling, or tighter control. Include measured ranges, equipment adjustments, and scaling notes.
  - **Kitchen-only output**: User asks only for printable or cooking-counter steps. Output the kitchen execution version, but keep critical safety notes and failure signals.
- **Troubleshooting**: User reports a failed result. Diagnose likely causes, next adjustment, and safety risk.
- **Learning**: User asks why something works or failed. Output a principle card and link it back to usable dishes.
- **Meal Planning**: User asks for a meal, multiple dishes, shopping list, or cooking schedule. Output a meal plan with menu, consolidated shopping list, kitchen timeline, and equipment conflicts.
- **Recipe Import**: User provides an external, pasted, or self-authored recipe. Rewrite it into this skill's recipe schema and keep the initial Review status as `draft`.
- **Memory Init / Update**: User explicitly asks to initialize or update preferences, equipment, dislikes, household members, or historical feedback. Do not enter this flow just because no profile exists.

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
9. An applied preferences or assumptions section listing servings, equipment, taste, household members if specified, and historical feedback if used.

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
- User profile shape: `references/user-profile.example.yaml`.
- Feedback learning shape: `references/feedback-log.example.yaml`.
- Memory merge rules: `references/memory-merge-rules.md`.
- Meal planning rules: `references/meal-planning-rules.md`.
- Meal plan output: `templates/meal-plan.md`.
- Recipe versioning rules: `references/recipe-versioning.md`.
- Recipe changelog output: `templates/recipe-changelog.md`.
- Recipe import rules: `references/recipe-import-rules.md`.
- Imported recipe review output: `templates/imported-recipe-review.md`.
- Recipe source and license notes: `references/source-notes.md`.
- Real kitchen validation rules: `references/kitchen-validation.md`.
- Printable output: `assets/print.css` and `scripts/render_recipe_pdf.py`.
- Repository quality gates: `scripts/check_skill_completeness.py`.
- Apply real kitchen validation records: `scripts/apply_kitchen_validation.py`.
- Create blank kitchen validation records: `scripts/new_kitchen_validation_record.py`.
- Prepare benchmark validation packet: `scripts/prepare_benchmark_validation.py`.

Use existing recipes under `recipes/` as examples only after checking that they passed the review checklist.

For multi-dish meals, use `templates/meal-plan.md` and `references/meal-planning-rules.md`. Keep the first implementation practical: consolidate ingredients, surface equipment conflicts, and schedule long waits before quick finishing steps. Do not invent exact timings when a dish lacks structured recipe data.

When recipe parameters, safety notes, status, kitchen execution steps, or feedback-driven adjustments change, append a changelog entry using `templates/recipe-changelog.md` and `references/recipe-versioning.md`. Pure typo or formatting fixes do not need a recipe changelog.

For user-imported recipes, use `references/recipe-import-rules.md` and `templates/imported-recipe-review.md`. Imported recipes start as `draft`; only mark them `passed` after review against `templates/recipe-review-checklist.md`.

## Generation Workflow

1. Identify the flow, serving count, and requested output strength.
2. Check whether a user profile or memory source is available.
3. If memory exists, read only the fields relevant to the dish, equipment, servings, taste, household members, dislikes, or prior failures.
4. If memory does not exist, continue with defaults; do not block the requested recipe, diagnosis, explanation, meal plan, or import.
5. Apply defaults, then durable preferences, then explicit user overrides for this request.
6. Load the relevant template and reference files.
7. For Recipe Generation, generate the full version first unless the user asked only for quick or kitchen output; generate the kitchen version after the full version.
8. Run the review checklist mentally before finalizing. Fix missing timing, heat, state, failure, safety, or substitution details.
9. State which preferences or assumptions were used. If no memory profile exists, briefly mention that the output used defaults and that the user can explicitly initialize cooking preferences.

Safety overrides taste. When safety and texture conflict, keep the safety requirement and explain the texture tradeoff.

## Memory Rules

Distinguish temporary overrides from durable preferences:

- "今天 4 人份" applies only to the current recipe.
- "以后默认 4 人份" can become a durable serving preference.
- Missing memory is not an error. Use defaults and offer a lightweight initialization prompt only after completing the requested task.
- Enter Memory Init / Update only when the user explicitly asks to initialize or change durable preferences.
- If the user names household members, merge only those members' relevant preferences.
- For multiple diners, combine dislikes and safety constraints, then choose the least risky shared salt, oil, and spice level.
- Recipe feedback may become a memory candidate, but automatic learning must ask for confirmation before changing durable preferences.
- Equipment, taste, and serving habits may be suggested for memory.
- Allergy, health, religion, pregnancy, or long-term dietary restrictions require explicit confirmation before durable memory.
- Low-confidence memory can be suggested, not silently enforced.

Always provide a way to view, change, delete, or temporarily ignore remembered preferences when memory is used.
