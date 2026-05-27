# Cooking Flow Elicitation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the cooking flow elicitation contract across skill instructions, references, templates, QA harness, and tests.

**Architecture:** Keep this as a documentation-first skill change. Encode behavior in `SKILL.md`, supporting references, templates, README, and the existing QA harness rather than adding a separate flow engine. Add focused tests that assert stable prompt contracts and QA evaluation behavior.

**Tech Stack:** Markdown prompt/reference files, Python standard library, `unittest`.

---

## File Structure

- Modify `SKILL.md`: shared elicitation contract, flow matrix, and flow-specific rules.
- Modify `references/cooking-memory-layer.md`: memory init/update wizard, write preview, feedback confirmation, dry-run caveat.
- Modify `references/recipe-import-rules.md`: import persistence target and output shape split.
- Modify `references/meal-planning-rules.md`: planning mode inference before asking.
- Modify `templates/failure-diagnosis.md`: safety triage, issue label, and memory action fields.
- Modify `templates/imported-recipe-review.md`: import intent, output shape, open risks.
- Modify `templates/principle-card.md`: short-answer projection and expansion choices.
- Modify `README.md`: user-facing examples for six flows.
- Modify `docs/interactive-qa-agent-test-plan.md`: extend QA matrix beyond Recipe Generation.
- Modify `scripts/cooking_memory.py`: extend issue adjustment mapping for the troubleshooting taxonomy if tests require it.
- Modify `scripts/run_agent_skill_qa.py`: add Memory Init / Update case and stricter flow evaluators.
- Modify `tests/test_interactive_qa_mode_docs.py`: prompt/reference/template contract tests.
- Modify `tests/test_cooking_memory.py`: issue taxonomy memory tests.
- Modify `tests/test_run_agent_skill_qa.py`: QA harness evaluator tests.

Do not modify maintained recipe files under `recipes/`.

## Task 1: Prompt Contract Tests

**Files:**
- Modify: `tests/test_interactive_qa_mode_docs.py`

- [ ] **Step 1: Add failing tests for shared contract and flow-specific docs**

Add tests that assert these strings exist after implementation:

```python
    def test_skill_defines_shared_elicitation_contract(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("## Shared Elicitation Contract", skill)
        self.assertIn("Blocking", skill)
        self.assertIn("Optional", skill)
        self.assertIn("Post-answer expansion", skill)
        self.assertIn("Flow Matrix", skill)

    def test_troubleshooting_defines_safety_triage_issue_taxonomy_and_memory_choice(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        diagnosis_template = (ROOT / "templates" / "failure-diagnosis.md").read_text(encoding="utf-8")

        self.assertIn("Safety Triage", skill)
        self.assertIn("Issue Taxonomy", skill)
        self.assertIn("too_watery", skill)
        self.assertIn("Record feedback only", skill)
        self.assertIn("Save durable preference", skill)
        self.assertIn("## 安全分诊", diagnosis_template)
        self.assertIn("## 反馈归档", diagnosis_template)

    def test_memory_init_update_requires_write_preview(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        memory = (ROOT / "references" / "cooking-memory-layer.md").read_text(encoding="utf-8")

        self.assertIn("## Memory Init / Update Workflow", skill)
        self.assertIn("Write preview", skill)
        self.assertIn("Confirm write", skill)
        self.assertIn("Edit values", skill)
        self.assertIn("Cancel", skill)
        self.assertIn("写入预览", memory)
        self.assertIn("dry-run", memory)

    def test_import_meal_learning_contracts_are_documented(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        import_rules = (ROOT / "references" / "recipe-import-rules.md").read_text(encoding="utf-8")
        meal_rules = (ROOT / "references" / "meal-planning-rules.md").read_text(encoding="utf-8")
        principle_template = (ROOT / "templates" / "principle-card.md").read_text(encoding="utf-8")
        import_template = (ROOT / "templates" / "imported-recipe-review.md").read_text(encoding="utf-8")

        self.assertIn("## Recipe Import Intent", skill)
        self.assertIn("persistence target", skill)
        self.assertIn("output shape", skill)
        self.assertIn("持久化目标", import_rules)
        self.assertIn("输出形态", import_rules)
        self.assertIn("导入意图", import_template)
        self.assertIn("## Meal Planning Mode Inference", skill)
        self.assertIn("先推断", meal_rules)
        self.assertIn("## Learning Default And Expansion", skill)
        self.assertIn("默认先短答", principle_template)
```

- [ ] **Step 2: Run tests and verify red**

Run:

```bash
python -m unittest tests.test_interactive_qa_mode_docs
```

Expected: FAIL because `SKILL.md`, references, and templates do not yet contain the new contract wording.

## Task 2: Memory Issue Taxonomy Tests

**Files:**
- Modify: `tests/test_cooking_memory.py`

- [ ] **Step 1: Add failing tests for issue mappings**

Add tests:

```python
    def test_adjustment_for_issue_supports_flow_taxonomy(self):
        memory = load_memory_module()

        watery = memory.adjustment_for_issue("too_watery")
        burnt = memory.adjustment_for_issue("burnt")
        undercooked = memory.adjustment_for_issue("undercooked")
        separated = memory.adjustment_for_issue("separated")

        self.assertIn("batch_size_multiplier", watery)
        self.assertIn("heat_level_note", burnt)
        self.assertIn("cook_time_multiplier", undercooked)
        self.assertIn("heat_level_note", separated)

    def test_add_feedback_uses_taxonomy_adjustment_key_for_watery_issue(self):
        memory = load_memory_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            memory.init_profile(root)

            feedback = memory.add_feedback(
                root,
                recipe_id="stir-fried-greens",
                recipe_name="清炒小青菜",
                issue="too_watery",
                result="edible",
                observation="锅底很多水。",
                eaten_by=["self"],
            )

        candidate = feedback["memory_candidate"]
        self.assertEqual("recipe_preferences.stir-fried-greens.batch_size_multiplier", candidate["key"])
        self.assertEqual(0.8, candidate["value"])
```

- [ ] **Step 2: Run tests and verify red**

Run:

```bash
python -m unittest tests.test_cooking_memory
```

Expected: FAIL because `adjustment_for_issue()` does not yet support the new labels.

## Task 3: QA Harness Tests

**Files:**
- Modify: `tests/test_run_agent_skill_qa.py`

- [ ] **Step 1: Add failing tests for new evaluators**

Add tests:

```python
    def test_troubleshooting_case_requires_safety_and_memory_action(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["E"],
            "## 安全判断\n没有肉蛋海鲜风险。\n## 可能原因\n蒸汽太猛。\n## 下次调整\n改小火。\n## 记忆处理\nRecord feedback only / Save durable preference / Do not record",
        )

        self.assertEqual("pass", result.status)

    def test_troubleshooting_case_rejects_missing_safety_judgment(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["E"],
            "## 可能原因\n蒸汽太猛。\n## 下次调整\n改小火。",
        )

        self.assertEqual("fail", result.status)

    def test_learning_case_accepts_short_answer_with_expansion(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["F"],
            "一句话解释：锅温低会让水分来不及蒸发。\n关键变量：锅温、批量。\n可继续：Full principle card / Explain through one dish / Diagnose my failed result",
        )

        self.assertEqual("pass", result.status)

    def test_memory_init_case_requires_write_preview(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["I"],
            "Write preview\nWill write:\n- defaults.servings = 4\nConfirm write / Edit values / Cancel",
        )

        self.assertEqual("pass", result.status)
```

- [ ] **Step 2: Run tests and verify red**

Run:

```bash
python -m unittest tests.test_run_agent_skill_qa
```

Expected: FAIL because case `I` and stricter evaluators do not exist yet.

## Task 4: Documentation And Template Implementation

**Files:**
- Modify: `SKILL.md`
- Modify: `references/cooking-memory-layer.md`
- Modify: `references/recipe-import-rules.md`
- Modify: `references/meal-planning-rules.md`
- Modify: `templates/failure-diagnosis.md`
- Modify: `templates/imported-recipe-review.md`
- Modify: `templates/principle-card.md`
- Modify: `README.md`
- Modify: `docs/interactive-qa-agent-test-plan.md`

- [ ] **Step 1: Update `SKILL.md`**

Add these sections after `Mode Selection` and before existing `Interactive QA Mode`:

```markdown
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
| Learning | Unsafe failure diagnosis without enough facts | Short explanation plus one practical link | No durable write by default |
```

Also add flow-specific sections named exactly:

- `## Troubleshooting Safety Triage And Issue Taxonomy`
- `## Memory Init / Update Workflow`
- `## Recipe Import Intent`
- `## Meal Planning Mode Inference`
- `## Learning Default And Expansion`

Use wording from the spec and keep existing Recipe Generation behavior intact.

- [ ] **Step 2: Update references and templates**

Add stable wording required by tests:

- `references/cooking-memory-layer.md`: `写入预览`, `dry-run`, `Confirm write`, `Edit values`, `Cancel`.
- `references/recipe-import-rules.md`: `持久化目标`, `输出形态`, `draft`.
- `references/meal-planning-rules.md`: `先推断`, `完整购物清单`, `缺货检查清单`, `跳过购物清单`.
- `templates/failure-diagnosis.md`: `## 安全分诊`, `## 反馈归档`, `{{issue_label}}`.
- `templates/imported-recipe-review.md`: `导入意图`, `输出形态`, `持久化目标`.
- `templates/principle-card.md`: `默认先短答`, `展开选项`.

- [ ] **Step 3: Update README and QA plan**

Document the six-flow contract in `README.md`, then extend `docs/interactive-qa-agent-test-plan.md` with Memory Init / Update case `I` and stricter expectations for Troubleshooting, Learning, Meal Planning, and Recipe Import.

- [ ] **Step 4: Run prompt contract tests**

Run:

```bash
python -m unittest tests.test_interactive_qa_mode_docs
```

Expected: PASS.

## Task 5: Memory CLI Implementation

**Files:**
- Modify: `scripts/cooking_memory.py`

- [ ] **Step 1: Extend `adjustment_for_issue()` minimally**

Add mappings:

```python
    if issue == "too_watery":
        return {
            "batch_size_multiplier": 0.8,
            "note": "Cook a smaller batch, drain ingredients better, and add salt later.",
        }
    if issue == "too_bland":
        return {
            "salt_multiplier": 1.1,
            "note": "Increase seasoning slightly and check taste before serving.",
        }
    if issue == "burnt":
        return {
            "heat_level_note": "lower_heat",
            "note": "Lower heat, stir sooner, and add sugar later when relevant.",
        }
    if issue == "undercooked":
        return {
            "cook_time_multiplier": 1.15,
            "note": "Extend cooking time and use smaller cuts for safer doneness.",
        }
    if issue == "separated":
        return {
            "heat_level_note": "gentler_heat",
            "note": "Use gentler heat and adjust mixing or water ratio.",
        }
```

- [ ] **Step 2: Run memory tests**

Run:

```bash
python -m unittest tests.test_cooking_memory
```

Expected: PASS.

## Task 6: QA Harness Implementation

**Files:**
- Modify: `scripts/run_agent_skill_qa.py`

- [ ] **Step 1: Add case `I`**

Add:

```python
    "I": TestCase(
        "I",
        "Memory Init / Update",
        "Use $rookie-cooking 以后默认 4 人份。",
        "Memory update should show a write preview and require confirmation.",
    ),
```

- [ ] **Step 2: Add helper checks**

Add helpers:

```python
def has_safety_judgment(text: str) -> bool:
    return has_any(text, ("安全判断", "安全分诊", "Safety Triage", "safety judgment"))


def has_memory_action(text: str) -> bool:
    return has_any(text, ("Record feedback only", "Save durable preference", "Do not record", "记录反馈", "保存长期偏好", "不要记录"))


def has_learning_expansion(text: str) -> bool:
    return has_any(text, ("Full principle card", "Explain through one dish", "Diagnose my failed result", "完整原理卡", "结合一道菜", "诊断"))


def has_write_preview(text: str) -> bool:
    return has_any(text, ("Write preview", "写入预览", "Will write")) and has_any(text, ("Confirm write", "Edit values", "Cancel", "确认写入", "编辑", "取消"))
```

- [ ] **Step 3: Tighten `evaluate_output()`**

Update case `E` to require safety judgment, likely cause/adjustment, and memory action. Update case `F` to accept short explanation plus expansion and reject Recipe Generation QA. Add case `I` requiring write preview.

- [ ] **Step 4: Run QA harness tests**

Run:

```bash
python -m unittest tests.test_run_agent_skill_qa
```

Expected: PASS.

## Task 7: Full Verification

**Files:**
- Verify all touched files.

- [ ] Run:

```bash
python -m unittest discover -s tests
```

Expected: all tests pass.

- [ ] Run:

```bash
python scripts/check_skill_completeness.py
```

Expected: `OK`.

- [ ] Run:

```bash
git diff --check -- SKILL.md README.md references/cooking-memory-layer.md references/recipe-import-rules.md references/meal-planning-rules.md templates/failure-diagnosis.md templates/imported-recipe-review.md templates/principle-card.md docs/interactive-qa-agent-test-plan.md scripts/cooking_memory.py scripts/run_agent_skill_qa.py tests/test_interactive_qa_mode_docs.py tests/test_cooking_memory.py tests/test_run_agent_skill_qa.py docs/superpowers/specs/2026-05-26-cooking-flow-elicitation-design.md docs/superpowers/plans/2026-05-26-cooking-flow-elicitation.md
```

Expected: no whitespace errors.

- [ ] Review path-limited diff:

```bash
git diff -- SKILL.md README.md references/cooking-memory-layer.md references/recipe-import-rules.md references/meal-planning-rules.md templates/failure-diagnosis.md templates/imported-recipe-review.md templates/principle-card.md docs/interactive-qa-agent-test-plan.md scripts/cooking_memory.py scripts/run_agent_skill_qa.py tests/test_interactive_qa_mode_docs.py tests/test_cooking_memory.py tests/test_run_agent_skill_qa.py docs/superpowers/specs/2026-05-26-cooking-flow-elicitation-design.md docs/superpowers/plans/2026-05-26-cooking-flow-elicitation.md
```

Expected: only flow elicitation contract changes and this plan.
