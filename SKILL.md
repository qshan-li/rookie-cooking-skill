---
name: rookie-cooking
description: >-
  Use when generating, adapting, reviewing, or troubleshooting beginner-friendly cooking recipes
  with exact measurements, kitchen execution steps, failure diagnosis, cooking principles,
  substitutions, food-safety checks, equipment adaptation, taste preferences, full recipe output,
  or printable kitchen versions.
version: 1.0.0
homepage: https://github.com/qshan-li/rookie-cooking-skill
---

# Rookie Cooking

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

Do not ask follow-up questions before producing a useful first recipe unless a safety-critical constraint is missing or the runtime can present the optional first-run adaptation choice below without blocking the default path.

## User Input Tools

When this skill prompts the user for a choice, follow this tool-selection rule:

1. **Prefer built-in user-input tools** exposed by the current agent runtime — e.g., `AskUserQuestion`, `request_user_input`, `clarify`, `ask_user`, or any equivalent.
2. **Fallback**: if no such tool exists, emit a numbered plain-text message and ask the user to reply with the chosen number/answer for each question.
3. **Batching**: if the tool supports multiple questions per call, combine all applicable questions into a single call; if only single-question, ask them one at a time in priority order.

Do not use a plain-text question in Claude Code or any other runtime that supports structured choices.

## Confirmation Policy

Default behavior: **confirm before durable writes**.

- Recipe Generation: no confirmation needed for output itself; confirm only before PDF/print delivery.
- Memory Init / Update: show Write preview, then require explicit confirmation before any durable write.
- Recipe Import: confirm persistence target (chat-only / save as draft / review existing).
- Troubleshooting: feedback is recorded as pending candidate unless user confirms durable preference.
- Sensitive data (allergies, pregnancy, child-specific rules, disease, religion, long-term dietary restrictions): require separate explicit confirmation before durable memory.

Skip confirmation only when the user explicitly says to do so, for example: "直接保存", "不用确认", "跳过确认".

## Mode Selection

- **Recipe Generation**: User names a dish or asks how to cook one. Offer only two output modes when the mode is missing.
  - **Default output: Full explanation version**. Generate the complete explanation version, then ask whether to generate a PDF or send output to the printer.
  - **Kitchen execution output**: Generate the kitchen execution version, then ask whether to generate a PDF or send output to the printer.
- **Troubleshooting**: User reports a failed result. Diagnose likely causes, next adjustment, and safety risk.
- **Learning**: User asks why something works or failed. Start with a concise L1 answer, then progressively deepen to L2 (expanded) and L3 (full principle card) on user request. Offer to transition into Recipe Generation for hands-on verification. Record depth in Learning Log.
- **Meal Planning**: User asks for a meal, multiple dishes, shopping list, or cooking schedule. Output a meal plan with menu, kitchen timeline, and equipment conflicts; elicit the shopping list mode before generating shopping-list details.
- **Recipe Import**: User provides an external, pasted, or self-authored recipe. Rewrite it into this skill's recipe schema and keep the initial Review status as `draft`.
- **Memory Init / Update**: User explicitly asks to initialize or update preferences, equipment, dislikes, household members, or historical feedback. Do not enter this flow just because no profile exists.

## Shared Elicitation Contract

Classify every possible question before asking it:

- **Blocking**: Ask one short question and wait only when the missing answer can make the output unsafe, invalid, or impossible to scope.
- **Optional**: Use an interactive choice or compact form when available; otherwise continue with defaults and state the assumption.
- **Post-answer expansion**: Produce the core answer first, then offer relevant next actions.

Do not turn the skill into a questionnaire. Ask only when the answer changes safety handling, output shape, persistence, shopping-list detail, delivery, or durable memory.

## Flow Matrix

| Flow | Blocking questions | Default fallback | Memory write |
| --- | --- | --- | --- |
| Recipe Generation | Safety-critical missing constraints only | Full explanation version with skill defaults | Only after explicit durable preference or confirmed candidate |
| Troubleshooting | Unsafe meat, poultry, seafood, eggs, leftovers, spoilage, allergy, or unknown doneness | Diagnose from observed facts and assumptions | Feedback candidate or durable preference only after confirmation |
| Memory Init / Update | Confirmation before durable write; separate confirmation for sensitive data | Do not write; treat unclear values as session-only or candidate | Through `scripts/cooking_memory.py` only |
| Recipe Import | Persistence target and source note when saving a draft; high-risk safety gaps | Rewrite for this chat only, review status `draft` | No durable user memory by default |
| Meal Planning | Required only when servings or menu scope is impossible to infer | Infer menu source; use relative timeline; skip full shopping list until selected | No durable write by default |
| Learning | Unsafe failure diagnosis without enough facts | L1 short answer with progressive disclosure to L2/L3; Learning Log records depth | Learning Log append-only via `scripts/cooking_memory.py`; no durable profile write |

## Interactive QA Mode

This is an agent-neutral protocol for Codex, Claude Code, OpenClaw, Hermes Agent, and other skill-capable terminals. Use it only when the runtime provides an interactive choice tool.

Enter interactive QA mode when all conditions are true:

1. The flow is Recipe Generation.
2. The dish is clear enough to generate a useful recipe.
3. The recipe output mode is missing.
4. The terminal exposes an interactive choice tool, such as option chips, a question form, or a structured user-input tool.

Ask the user to choose one recipe output mode:

- **Default output: Full explanation version**: Complete explanation version, followed by a PDF or direct printing choice.
- **Kitchen execution output**: Kitchen execution version only, followed by a PDF or direct printing choice.

Recipe output mode is not a durable preference and must not be read from or written to the memory layer. If the recipe output mode is missing, present this output-mode choice every time an interactive choice tool is available, even when a profile exists. Profile memory may change servings, equipment, taste, household constraints, and prior dish adjustments; it must not skip the output-mode choice.

If no local profile exists, do not generate the recipe after only the output-mode choice. Continue immediately to First-Run Adaptation Elicitation before recipe generation.

If the interaction tool is unavailable, do not block generation. Continue with Default output and state that assumption briefly.

## First-Run Adaptation Elicitation

When Recipe Generation starts and no local profile exists, the recipe is more accurate with serving count, equipment, taste, and dietary constraints. If the runtime provides an interactive choice tool, you must present this choice before recipe generation. Do not use a plain text question for this flow.

The choices are:

- **Use defaults and continue**: Use the skill defaults for this recipe. This must be the default choice.
- **Adapt this recipe only**: Ask only for this request's serving count, equipment, taste, and dietary constraints; do not persist those answers.
- **Initialize long-term preferences**: Enter Memory Init / Update and save durable defaults only after explicit user confirmation.

If the interaction tool is unavailable, continue with defaults. If the user already supplied enough serving, equipment, taste, or dietary information in the request, use it and skip duplicate questions. Safety-critical constraints still take priority and may require a direct clarification before generating.

## Output Rules

Every generated recipe must include:

1. Dish name, servings, total time, difficulty, target result, equipment, and calories estimate when reasonable.
2. Ingredients with grams or milliliters, plus practical no-scale fallback.
3. Step-by-step operations. Every full-version step includes operation, time, heat, target state, failure signal, and why.
4. Safety notes for meat, poultry, seafood, eggs, leftovers, thawing, reheating, or cross-contamination.
5. Substitutions for likely missing ingredients or tools.
6. Failure diagnosis with possible cause and next adjustment.
7. Related principles from `principles/`.
8. A kitchen execution version that is short enough to scan while cooking only when the user explicitly chooses Kitchen execution output, Generate PDF, Direct print, Output kitchen execution text, or a persisted recipe-file workflow.
9. An applied preferences or assumptions section listing servings, equipment, taste, household members if specified, and historical feedback if used.
10. After Recipe Generation completes, trigger Post-Generation Delivery Flow using an interactive choice tool (e.g., AskUserQuestion). Do not use plain text questions. This is an explicit checkpoint to prevent missing delivery selection.

Default output chat body must contain only the full explanation version. Do not include a `## 厨房执行版` section, kitchen print-card body, or kitchen-only checklist in the default chat body. If the user later chooses Generate PDF or Direct print, derive the kitchen execution artifact only after the user chooses Generate PDF or Direct print.

Avoid unqualified vague terms such as "适量", "少许", "一会儿", "炒熟", "差不多", or "收汁即可". If a sensory description is needed, pair it with a measurable range or state standard.

## Post-Generation Delivery Flow

After either Recipe Generation output mode finishes, offer delivery choices. Use an interactive choice tool whenever the runtime provides one; do not use a plain text question in Claude Code or any other runtime that supports structured choices.

The delivery choices are:

- **Generate PDF**: Render a kitchen execution PDF.
- **Direct print**: Print the kitchen execution PDF after printer selection.
- **No delivery**: End after the chat output.

PDF and printed output must use the kitchen execution version, not the full explanation version. If the user chooses direct printing, ask them to choose a printer device before printing. List available printers before asking for the device. If no printer service or printer device is available, use an interactive choice tool again with these fallback choices:

- **Generate PDF**: Create the PDF for the user to open and print elsewhere.
- **Output kitchen execution text**: Print the kitchen execution version in chat.

Do not write one-off generated recipes to `recipes/`. That directory is only for maintained recipe content. For PDF or printing from a generated chat recipe, create a temporary kitchen execution artifact under `~/.rookie-cooking/tmp/print-jobs/`, derive a recipe-style pinyin slug matching maintained recipe filenames, then render it with `scripts/render_recipe_pdf.py --kitchen-markdown <path> --title <dish name> --output-stem <pinyin-slug>`. The renderer writes PDFs under `~/.rookie-cooking/output/pdf/` by default, deletes the temporary kitchen Markdown after a successful render, and does not duplicate an existing `-kitchen` suffix. PDF filenames should therefore be `<pinyin-slug>-kitchen.pdf`, matching the maintained recipe `.md` filename style.

## Troubleshooting Workflow

Use this workflow when the user reports a failed or unexpected cooking result, including texture, flavor, doneness, water release, burning, separation, odor, or food-safety concerns. Do not enter Recipe Generation output selection for Troubleshooting.

1. Identify dish, symptom, severity, and safety risk. If meat, poultry, seafood, eggs, leftovers, thawing, or reheating may be unsafe, handle safety before texture or taste.
2. If the dish is identifiable, read relevant local memory with `scripts/cooking_memory.py read --dish <recipe-id> --diners <member-id...>`.
3. Use memory only to rank likely causes and tailor next adjustments. Useful memory includes equipment, pan type, stove behavior, taste preferences, diner constraints, and prior failures for the same dish.
4. If memory is missing or invalid, continue with general diagnosis; do not block the troubleshooting answer.
5. Always separate observed facts, likely causes, and assumptions. Mark low-confidence or `pending-confirmation` feedback as a suggestion, not a fact.
6. Provide immediate salvage steps when safe, then next-run parameter changes such as salt, water, oil, heat, timing, batch size, cut size, or rest time.
7. Record feedback only as a pending memory candidate unless the user explicitly confirms a durable preference such as "以后这道菜都少盐" or "记住我家电磁炉火力弱".

## Troubleshooting Safety Triage And Issue Taxonomy

Safety Triage comes before texture and taste. If the result may involve unsafe meat, poultry, seafood, eggs, leftovers, thawing, reheating, spoilage, allergy exposure, or unknown doneness, ask one blocking safety question when the missing fact changes whether the food should be eaten. If safety can be judged from the user's facts, answer directly.

Normalize troubleshooting feedback to a stable Issue Taxonomy before proposing memory writes:

| Issue label | User-facing symptoms | Typical next-run parameters |
| --- | --- | --- |
| `too_salty` | too salty, bitter from reduction, over-seasoned sauce | salt multiplier, soy sauce amount, dilution, sauce reduction |
| `too_bland` | bland, not seasoned through, weak savoriness | salt timing, seasoning amount, marinade time |
| `too_watery` | water release, soupy stir-fry, dull texture | batch size, draining, salt timing, heat level |
| `burnt` | scorched bottom, blackened sugar, bitter flavor | heat level, oil amount, stirring interval, sugar timing |
| `undercooked` | raw center, translucent pieces, unsafe doneness | cook time, cut size, covered heating, safety endpoint |
| `meat_dry` | dry, tough, overcooked meat | cook time, cut thickness, velveting, resting |
| `separated` | broken emulsion, watery custard, honeycomb steamed egg | heat level, water ratio, mixing, steaming intensity |

After diagnosis, offer only relevant memory actions:

- **Record feedback only**: write a pending feedback or candidate; do not change durable preferences.
- **Save durable preference**: only when the user confirms a durable rule.
- **Do not record**: end without a memory write.

## Memory Init / Update Workflow

Enter Memory Init / Update only when the user explicitly asks to initialize, update, view, delete, ignore, or confirm durable preferences or candidates. Before durable writes, show a Write preview:

```text
Will write:
- defaults.servings = 4

Will not write:
- tonight_no_cilantro, session-only
```

Then ask for one of:

- **Confirm write**
- **Edit values**
- **Cancel**

Sensitive constraints such as allergies, pregnancy, child-specific rules, disease, religion, or long-term dietary restrictions require a separate explicit confirmation. The current memory CLI may not expose a dedicated dry-run path; when no dry-run is available, generate the preview from parsed intent and use `scripts/cooking_memory.py` only after confirmation.

## Recipe Import Intent

Recipe Import has two decisions: persistence target and output shape. Do not merge them.

When the persistence target is missing and an interactive choice tool is available, ask:

- **Rewrite for this chat only**: default; keep status `draft`, do not save.
- **Save as draft recipe**: save to `~/.rookie-cooking/drafts/`, require a source note, keep status `draft`.
- **Review an existing draft**: scan `~/.rookie-cooking/drafts/` to list existing drafts, review against `templates/recipe-review-checklist.md`.

The output shape follows Recipe Generation rules: Full explanation version by default, Kitchen execution version when requested, and PDF or direct print only after a kitchen execution version exists.

### User Recipe Storage

User-imported recipes live in `~/.rookie-cooking/`, separate from the skill's `recipes/` directory:

- `~/.rookie-cooking/drafts/` — draft status recipes
- `~/.rookie-cooking/recipes/` — passed / validated status recipes

Agent discovers user recipes by scanning these directories directly (no index file).

### State Transitions

- `draft → passed`: Agent runs review checklist, user confirms, file moves from `drafts/` to `recipes/`.
- `passed → validated`: User reports they cooked it and it worked. One-sentence confirmation is sufficient.
- Frontmatter must include: `status`, `source`, `source_description`, `import_date`.

### Conflict Detection

Before importing, scan skill's `recipes/` and `~/.rookie-cooking/recipes/` for name conflicts. If a conflict is found, warn the user. When using recipes, prefer the user's version over the built-in one.

## Meal Planning Mode Inference

For Meal Planning, infer before asking:

- Named dishes present: use those dishes.
- Ingredients present without dishes: plan from available ingredients.
- Meal shape present without dishes or ingredients: recommend from existing recipes.
- Explicit shopping request: run shopping-list elicitation.

Ask for planning mode only when the mode cannot be inferred and the resulting plan would materially differ. If no interaction tool exists, recommend from existing recipes using defaults and state that assumption.

## Learning Default And Expansion

Learning defaults to a concise answer. Do not ask a first-turn depth question unless the user explicitly asks for a specific output shape and that shape is ambiguous.

### Progressive Disclosure

Learning uses three depth levels. Always start at L1 and deepen only when the user asks. Each level ends with a subtle hook that signals more depth is available without blocking.

**L1 — Short Answer** (default on first turn):
- One-sentence principle explanation.
- Key variables that affect the outcome.
- Beginner-friendly observable check.
- One concrete application example.
- End with a soft hook: "想展开说原理机制，或者用一道菜来验证，可以继续问。"

**L2 — Expanded** (when the user asks to expand, go deeper, or "展开说"):
- Mechanism explanation: how and why it works at a physical/chemical level.
- Common mistakes and their corrections.
- One linked recipe with a "verification point" — the step that demonstrates this principle.
- Offer a hands-on verification entry: "想用 [菜名] 动手验证这个原理吗？" If confirmed, transition to Recipe Generation with the principle context carried forward. The generated recipe starts with a "本菜验证的原理" overview section before steps; recipe steps themselves are not annotated.
- End with a hook: "还可以看完整原理卡片和关联原理。"

**L3 — Full Principle Card** (when the user asks for the full card or goes even deeper):
- Render using `templates/principle-card.md` with data from the relevant `principles/*.md` file.
- Include related principles and counterintuitive cases.

If the user asks "为什么" about a failure rather than a concept, offer diagnosis as an expansion option: transition to Troubleshooting and do not run Recipe Generation output selection.

When no interactive choice tool is available, replace expansion buttons with plain-text prompts: "可以问我'展开说''用一道菜讲'或'诊断一下'。"

### Learning Log Integration

Before answering, query the Learning Log to check whether this principle was already explained and at what depth:

```bash
python scripts/cooking_memory.py query-learning --principle <principle-id>
```

If the log shows the user already received L2 or L3 for this principle, briefly note "之前聊过这个原理" and skip redundant content. Offer to jump to L3 or explore a different angle.

After answering (L1 or deeper), record the interaction:

```bash
python scripts/cooking_memory.py append-learning --principle <principle-id> --level <L1|L2|L3>
```

No confirmation is needed for Learning Log writes; they are lightweight, non-sensitive, and only used to reduce repetition.

## Meal Planning Shopping List Elicitation

Use this flow when Meal Planning would include a shopping list. The menu, equipment conflicts, and kitchen schedule may be produced first, but shopping-list details must be gated by user choice.

Ask the user to choose one shopping list mode:

- **Full shopping list**: Consolidated ingredients, amounts, covered dishes, purchase notes, safety handling, and "check if already stocked" seasonings.
- **Missing-items checklist**: A compact checklist for items the user likely needs to verify or buy, with no full ingredient table.
- **Skip shopping list**: Omit shopping-list details and output only menu, schedule, equipment conflicts, and assumptions.

Use an interactive choice tool when the runtime provides one. If no interactive tool is available, ask a short plain-text question and wait. Do not dump a full shopping list before this choice. If the user already requested an explicit mode such as "给完整购物清单" or "只列我可能缺的东西", honor that mode and skip the elicitation.

## Resource Navigation

Read only the files needed for the user request:

### Templates

| 文件 | 用途 |
|---|---|
| `templates/recipe-full.md` | 完整解释版输出（Default output 专用，不加载 kitchen 版） |
| `templates/recipe-kitchen.md` | 厨房执行版输出（仅在选择 Kitchen output / PDF / 打印时加载） |
| `templates/principle-card.md` | 原理卡输出（配合 `principles/` 下相关文件） |
| `templates/failure-diagnosis.md` | 失败诊断输出 |
| `templates/recipe-review-checklist.md` | 菜谱质量审查 |
| `templates/meal-plan.md` | 一餐规划输出 |
| `templates/recipe-changelog.md` | 菜谱变更日志 |
| `templates/imported-recipe-review.md` | 导入菜谱审查（会话内 checklist，不落盘） |

### References

| 文件 | 用途 |
|---|---|
| `references/defaults.md` | 默认假设和参数 |
| `references/heat-levels.md` | 火力用语和设备映射 |
| `references/equipment-profiles.md` | 设备特征 |
| `references/unit-conversion.md` | 单位换算和无秤替代 |
| `references/scaling-rules.md` | 份量缩放规则 |
| `references/food-safety-rules.md` | 食品安全规则 |
| `references/cooking-memory-layer.md` | 记忆层边界 |
| `references/user-profile.example.yaml` | 用户偏好结构 |
| `references/feedback-log.example.yaml` | 反馈日志结构 |
| `references/memory-merge-rules.md` | 记忆合并规则 |
| `references/meal-planning-rules.md` | 一餐规划规则 |
| `references/recipe-import-rules.md` | 菜谱导入规则 |
| `references/recipe-versioning.md` | 菜谱版本规则 |
| `references/source-notes.md` | 来源和许可记录 |
| `references/kitchen-validation.md` | 厨房实测规则 |

### Scripts

| 文件 | 用途 |
|---|---|
| `scripts/cooking_memory.py` | 记忆读写 CLI |
| `scripts/render_recipe_pdf.py` | PDF 渲染 |
| `scripts/check_skill_completeness.py` | 结构校验 |
| `scripts/apply_kitchen_validation.py` | 应用厨房实测记录 |
| `scripts/new_kitchen_validation_record.py` | 创建实测记录 |
| `scripts/prepare_benchmark_validation.py` | 准备标杆实测包 |

Use existing recipes under `recipes/` as examples only after checking that they passed the review checklist.

For multi-dish meals, use `templates/meal-plan.md` and `references/meal-planning-rules.md`. Keep the first implementation practical: surface equipment conflicts and schedule long waits before quick finishing steps. Generate shopping-list details only after Meal Planning Shopping List Elicitation. Do not invent exact timings when a dish lacks structured recipe data.

When recipe parameters, safety notes, status, kitchen execution steps, or feedback-driven adjustments change, append a changelog entry using `templates/recipe-changelog.md` and `references/recipe-versioning.md`. Pure typo or formatting fixes do not need a recipe changelog.

For user-imported recipes, use `references/recipe-import-rules.md` and `templates/imported-recipe-review.md` (conversation-only checklist, not persisted). Imported recipes start as `draft` in `~/.rookie-cooking/drafts/`; mark them `passed` after review against `templates/recipe-review-checklist.md` and user confirmation, then move to `~/.rookie-cooking/recipes/`. See `references/recipe-import-rules.md` for full lifecycle.

## Generation Workflow

1. Identify the flow, serving count, and requested recipe output mode.
2. Check whether local cooking memory is available through `scripts/cooking_memory.py read --dish <recipe-id> --diners <member-id...>`. The default memory root is `~/.rookie-cooking/`; `ROOKIE_COOKING_HOME` may override it.
3. If memory exists, read only the fields relevant to the dish, equipment, servings, taste, household members, dislikes, or prior failures. Treat `pending-confirmation` feedback as a suggestion, not a default.
4. If the runtime supports interactive choices and the Recipe Generation output mode is missing, enter Interactive QA Mode.
5. If memory does not exist or the script reports invalid local memory, use First-Run Adaptation Elicitation before generating when interactive choices are available; otherwise continue with defaults. Do not block the requested recipe, diagnosis, explanation, meal plan, or import.
6. Apply defaults, then durable profile preferences, then relevant recipe feedback suggestions, then first-run adaptation answers for this request, then explicit user overrides for this request.
7. Load the relevant template and reference files.
8. For Default output, output the full explanation version only. For Kitchen execution output, output the kitchen execution version only. For PDF, direct printing, or persisted recipe-file workflows, derive the kitchen execution version only when that delivery or persistence path is selected.
9. Run the review checklist mentally before finalizing. Fix missing timing, heat, state, failure, safety, or substitution details.
10. State which preferences or assumptions were used. If no memory profile exists, briefly mention whether defaults or one-time adaptation answers were used and that the user can explicitly initialize cooking preferences.
11. For either Recipe Generation output mode, run the Post-Generation Delivery Flow.
12. If delivery requires a kitchen execution version that was not shown in chat, derive it as a temporary kitchen execution artifact under `~/.rookie-cooking/tmp/print-jobs/`; do not save it under `recipes/`.

Safety overrides taste. When safety and texture conflict, keep the safety requirement and explain the texture tradeoff.

## Completion Report

After Recipe Generation finishes, display a structured summary before entering the Post-Generation Delivery Flow:

```text
菜谱生成完成!
菜品: [dish name]
模式: [Default output / Kitchen execution output]
人数: [servings] 人份
设备: [equipment summary]
耗时: [total time]
难度: [difficulty]
相关原理: [principle card names]

偏好/假设: [list of applied preferences or defaults]
记忆状态: [profile exists / using defaults / one-time adaptation]
```

For Meal Planning, the report includes menu, timeline, and equipment conflicts.
For Troubleshooting, the report includes issue label, safety triage result, and memory action taken.

## Memory Rules

Distinguish temporary overrides from durable preferences:

- "今天 4 人份" applies only to the current recipe.
- "以后默认 4 人份" can become a durable serving preference.
- "以后默认完整版", "以后默认厨房版", "以后总是生成 PDF", and similar output-mode or delivery preferences must not become durable memory; ask the Recipe Generation output-mode choice and delivery choice again each run when the runtime supports choices.
- Missing memory is not an error. Use defaults and offer a lightweight initialization prompt only after completing the requested task.
- First-run adaptation answers are session-only unless the user chooses Initialize long-term preferences.
- Enter Memory Init / Update only when the user explicitly asks to initialize or change durable preferences.
- Durable memory writes must go through `scripts/cooking_memory.py`; do not edit memory files directly from the prompt.
- Durable user data lives outside this repository by default: `~/.rookie-cooking/profile.yaml`, `~/.rookie-cooking/feedback.jsonl`, `~/.rookie-cooking/memory-candidates.jsonl`, `~/.rookie-cooking/learning-log.jsonl`, `~/.rookie-cooking/drafts/` (draft recipes), and `~/.rookie-cooking/recipes/` (passed/validated recipes).
- If the user names household members, merge only those members' relevant preferences.
- For multiple diners, combine dislikes and safety constraints, then choose the least risky shared salt, oil, and spice level.
- Recipe feedback may become a memory candidate, but automatic learning must ask for confirmation before changing durable preferences.
- Equipment, taste, and serving habits may be suggested for memory.
- Allergy, health, religion, pregnancy, or long-term dietary restrictions require explicit confirmation before durable memory.
- Low-confidence memory can be suggested, not silently enforced.

Always provide a way to view, change, delete, or temporarily ignore remembered preferences when memory is used.
