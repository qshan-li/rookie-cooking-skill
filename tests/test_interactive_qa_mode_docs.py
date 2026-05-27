from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InteractiveQAModeDocsTest(unittest.TestCase):
    def test_skill_defines_agent_neutral_interactive_output_selection(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("## Interactive QA Mode", skill)
        self.assertIn("agent-neutral", skill)
        self.assertIn("interactive choice tool", skill)
        self.assertIn("recipe output mode is missing", skill)
        self.assertIn("If the interaction tool is unavailable", skill)

    def test_recipe_generation_only_offers_default_and_kitchen_modes(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Ask the user to choose one recipe output mode", skill)
        self.assertIn("Default output: Full explanation version", skill)
        self.assertIn("Kitchen execution output", skill)
        self.assertNotIn("Quick output", skill)
        self.assertNotIn("Precise output", skill)

    def test_default_recipe_generation_outputs_full_version_then_print_choice(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Default output: Full explanation version", skill)
        self.assertIn("After either Recipe Generation output mode finishes", skill)
        self.assertIn("PDF or direct printing", skill)
        self.assertIn("PDF and printed output must use the kitchen execution version", skill)
        self.assertIn("If the user chooses direct printing, ask them to choose a printer device", skill)

    def test_first_run_adaptation_is_optional_and_defaults_continue(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        memory = (ROOT / "references" / "cooking-memory-layer.md").read_text(encoding="utf-8")

        self.assertIn("## First-Run Adaptation Elicitation", skill)
        self.assertIn("Use defaults and continue", skill)
        self.assertIn("Adapt this recipe only", skill)
        self.assertIn("Initialize long-term preferences", skill)
        self.assertIn("must be the default choice", skill)
        self.assertIn("must present this choice before recipe generation", skill)
        self.assertIn("do not generate the recipe after only the output-mode choice", skill)
        self.assertIn("do not persist those answers", skill)
        self.assertIn("profile 不存在且交互选择工具可用时，生成前必须提供一次可选的本次适配入口", memory)
        self.assertIn("默认选项必须是继续使用默认值", memory)

    def test_recipe_output_mode_is_never_persisted_in_memory(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        memory = (ROOT / "references" / "cooking-memory-layer.md").read_text(encoding="utf-8")
        profile_example = (ROOT / "references" / "user-profile.example.yaml").read_text(encoding="utf-8")

        self.assertIn("Recipe output mode is not a durable preference", skill)
        self.assertIn("even when a profile exists", skill)
        self.assertIn("输出模式不是长期记忆字段", memory)
        self.assertNotIn("preferred_output", memory)
        self.assertNotIn("preferred_output", profile_example)

    def test_default_output_must_not_embed_kitchen_execution_body(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Default output chat body must contain only the full explanation version", skill)
        self.assertIn("Do not include a `## 厨房执行版` section", skill)
        self.assertIn("only after the user chooses Generate PDF or Direct print", skill)

    def test_post_generation_delivery_uses_choices_and_temp_artifacts(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("## Post-Generation Delivery Flow", skill)
        self.assertIn("Use an interactive choice tool", skill)
        self.assertIn("Generate PDF", skill)
        self.assertIn("Direct print", skill)
        self.assertIn("No delivery", skill)
        self.assertIn("Do not write one-off generated recipes to `recipes/`", skill)
        self.assertIn("temporary kitchen execution artifact", skill)
        self.assertIn("`~/.rookie-cooking/tmp/print-jobs/`", skill)
        self.assertIn("deletes the temporary kitchen Markdown after a successful render", skill)
        self.assertIn("does not duplicate an existing `-kitchen` suffix", skill)

    def test_default_mode_does_not_load_or_embed_kitchen_template(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        full_template = (ROOT / "templates" / "recipe-full.md").read_text(encoding="utf-8")

        self.assertIn("Default output 专用，不加载 kitchen 版", skill)
        self.assertIn("仅在选择 Kitchen output / PDF / 打印时加载", skill)
        self.assertNotIn("## 厨房执行版", full_template)

    def test_troubleshooting_reads_memory_without_silent_long_term_writes(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        memory = (ROOT / "references" / "cooking-memory-layer.md").read_text(encoding="utf-8")
        diagnosis_template = (ROOT / "templates" / "failure-diagnosis.md").read_text(encoding="utf-8")

        self.assertIn("## Troubleshooting Workflow", skill)
        self.assertIn("Identify dish, symptom, severity, and safety risk", skill)
        self.assertIn("read relevant local memory", skill)
        self.assertIn("separate observed facts, likely causes, and assumptions", skill)
        self.assertIn("Record feedback only as a pending memory candidate", skill)
        self.assertIn("Troubleshooting 可以读取相关记忆来排序原因", memory)
        self.assertIn("不能把一次失败静默写成长期偏好", memory)
        self.assertIn("## 已使用上下文", diagnosis_template)
        self.assertIn("## 记忆处理", diagnosis_template)

    def test_meal_planning_elicits_shopping_list_detail_before_output(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        rules = (ROOT / "references" / "meal-planning-rules.md").read_text(encoding="utf-8")
        template = (ROOT / "templates" / "meal-plan.md").read_text(encoding="utf-8")

        self.assertIn("## Meal Planning Shopping List Elicitation", skill)
        self.assertIn("Ask the user to choose one shopping list mode", skill)
        self.assertIn("Full shopping list", skill)
        self.assertIn("Missing-items checklist", skill)
        self.assertIn("Skip shopping list", skill)
        self.assertIn("Do not dump a full shopping list before this choice", skill)
        self.assertIn("购物清单必须先触发选择", rules)
        self.assertIn("不要默认输出完整购物清单", rules)
        self.assertIn("{{shopping_list_mode}}", template)

    def test_readme_documents_multi_agent_qa_fallback(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("Codex", readme)
        self.assertIn("Claude Code", readme)
        self.assertIn("OpenClaw", readme)
        self.assertIn("Hermes Agent", readme)
        self.assertIn("QA 模式", readme)
        self.assertIn("不阻塞生成", readme)
        self.assertIn("默认：完整解释版", readme)
        self.assertIn("厨房执行版：一页打印卡", readme)
        self.assertNotIn("快速：", readme)
        self.assertNotIn("精准：", readme)
        self.assertIn("PDF 或直接打印", readme)
        self.assertIn("选择打印设备", readme)
        self.assertIn("不要写入 `recipes/`", readme)

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


if __name__ == "__main__":
    unittest.main()
