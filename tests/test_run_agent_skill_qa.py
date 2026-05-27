import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_agent_skill_qa.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_agent_skill_qa", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load run_agent_skill_qa.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class AgentSkillQATest(unittest.TestCase):
    def test_root_skill_file_alone_is_not_installed_for_agents(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            home = Path(tmp) / "home"
            root.mkdir()
            home.mkdir()
            (root / "SKILL.md").write_text("---\nname: rookie-cooking\n---\n", encoding="utf-8")

            checks = module.local_install_checks(root, home)

        self.assertFalse(any(check.installed for check in checks))
        self.assertTrue(all(root / "SKILL.md" not in check.paths for check in checks))

    def test_claude_project_skill_directory_is_detected(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            home = Path(tmp) / "home"
            skill_dir = root / ".claude" / "skills" / module.SKILL_NAME
            skill_dir.mkdir(parents=True)
            home.mkdir()
            (skill_dir / "SKILL.md").write_text("---\nname: rookie-cooking\n---\n", encoding="utf-8")

            checks = module.local_install_checks(root, home)

        claude = next(check for check in checks if check.agent == "claude")
        self.assertTrue(claude.installed)

    def test_unqualified_recipe_generation_accepts_qa_choice_output(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["A"],
            "请选择菜谱输出模式：默认、厨房执行版。\n首次适配：继续使用默认值、仅适配本次、初始化长期偏好。",
        )

        self.assertEqual("pass", result.status)
        self.assertIn("interactive QA", result.reason)

    def test_unqualified_recipe_generation_rejects_output_mode_only_qa_without_first_run_adaptation(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["A"],
            "请选择菜谱输出模式：默认、厨房执行版。",
        )

        self.assertEqual("fail", result.status)

    def test_unqualified_recipe_generation_rejects_old_four_option_qa(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["A"],
            "请选择输出强度：默认、快速、精准、厨房版-only。",
        )

        self.assertEqual("fail", result.status)

    def test_default_recipe_generation_accepts_full_only_plus_print_choice(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["A"],
            "未指定输出模式，默认生成。本次使用默认适配继续。\n## 完整解释版\n...\n请选择后续交付方式：生成 PDF、直接打印、暂不需要。",
        )

        self.assertEqual("pass", result.status)

    def test_default_recipe_generation_rejects_plain_text_delivery_question(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["A"],
            "未指定输出模式，默认生成。\n## 完整解释版\n...\n需要生成 PDF 或直接打印吗？",
        )

        self.assertEqual("fail", result.status)

    def test_default_recipe_generation_rejects_kitchen_version_body(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["A"],
            "未指定输出模式，默认生成。\n## 完整解释版\n...\n## 备料\n...\n## 做法\n| 出错怎么办 |",
        )

        self.assertEqual("fail", result.status)

    def test_default_recipe_generation_allows_fast_texture_word_and_kitchen_pdf_delivery_wording(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["A"],
            (
                "未指定输出模式，默认生成。本次使用默认适配继续。\n"
                "## 完整解释版\n"
                "热油能让蛋液快速蓬松。\n"
                "请选择后续交付方式：生成厨房执行版 PDF、直接打印、暂不需要。"
            ),
        )

        self.assertEqual("pass", result.status)

    def test_kitchen_only_case_rejects_full_explanation_output(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["B"],
            "## 完整解释版\n...\n## 厨房执行版\n...",
        )

        self.assertEqual("fail", result.status)

    def test_kitchen_only_case_accepts_pdf_or_print_followup(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["B"],
            (
                "# 番茄炒蛋\n"
                "## 备料\n"
                "- 鸡蛋\n"
                "## 做法\n"
                "| 顺序 | 火力/时间 | 做什么 | 看到什么就下一步 | 出错怎么办 |\n"
                "| --- | --- | --- | --- | --- |\n"
                "| 1 | 中火 / 30 秒 | 倒蛋液 | 边缘凝固 | 火太大就离火 |\n"
                "## 安全 / 补救\n"
                "请选择后续交付方式：生成 PDF、直接打印、暂不需要。"
            ),
        )

        self.assertEqual("pass", result.status)

    def test_kitchen_only_case_rejects_plain_step_list_without_print_card_table(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["B"],
            (
                "# 番茄炒蛋 厨房执行版\n"
                "## 基本信息\n1 人份\n"
                "## 原料\n- 鸡蛋 2 个\n"
                "## 步骤\n"
                "1. 热锅。\n"
                "2. 倒蛋液炒到凝固。\n"
                "## 安全\n鸡蛋要熟。\n"
                "## 失败补救\n太老下次缩短时间。\n"
                "请选择后续交付方式：生成 PDF、直接打印、暂不需要。"
            ),
        )

        self.assertEqual("fail", result.status)
        self.assertIn("kitchen print-card table", result.reason)

    def test_kitchen_print_card_accepts_rendered_html_table(self):
        module = load_module()

        html = (
            "<h2>备料</h2>"
            "<table><thead><tr>"
            "<th>顺序</th><th>火力/时间</th><th>做什么</th>"
            "<th>看到什么就下一步</th><th>出错怎么办</th>"
            "</tr></thead></table>"
            "<h2>安全 / 补救</h2>"
        )

        self.assertTrue(module.has_kitchen_print_card_body(html))

    def test_kitchen_print_card_rejects_rendered_html_plain_steps(self):
        module = load_module()

        html = (
            "<h2>基本信息</h2><p>1 人份</p>"
            "<h2>原料</h2><ul><li>鸡蛋 2 个</li></ul>"
            "<h2>步骤</h2><ol><li>热锅。</li><li>倒蛋液。</li></ol>"
            "<h2>安全</h2><p>鸡蛋要熟。</p>"
            "<h2>失败补救</h2><p>太老下次缩短时间。</p>"
        )

        self.assertFalse(module.has_kitchen_print_card_body(html))

    def test_validate_kitchen_artifact_maps_pdf_to_intermediate_html(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf_path = root / "output" / "pdf" / "fan-qie-chao-dan-kitchen.pdf"
            html_dir = root / "tmp" / "pdfs"
            pdf_path.parent.mkdir(parents=True)
            html_dir.mkdir(parents=True)
            pdf_path.write_bytes(b"%PDF-1.4 fake")
            (html_dir / "fan-qie-chao-dan.html").write_text(
                (
                    "<h2>备料</h2>"
                    "<table><tr><th>火力/时间</th><th>做什么</th>"
                    "<th>看到什么就下一步</th><th>出错怎么办</th></tr></table>"
                    "<h2>安全 / 补救</h2>"
                ),
                encoding="utf-8",
            )

            result = module.validate_kitchen_artifact(pdf_path, html_dir)

        self.assertEqual("pass", result.status)

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

    def test_learning_case_accepts_progressive_disclosure_hook(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["F"],
            "一句话解释：青菜细胞壁在高温下破裂，水分被释放出来。\n关键变量：锅温、盐的时机、批量。\n新手判断：下锅后锅底出水说明锅温不够或盐放太早。\n想展开说原理机制，或者用一道菜来验证，可以继续问。",
        )

        self.assertEqual("pass", result.status)

    def test_learning_case_accepts_recipe_verification_entry(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["F"],
            "一句话解释：盐会改变食材内外水分移动。\n关键变量：盐量、时机。\n想用清炒小青菜动手验证这个原理吗？",
        )

        self.assertEqual("pass", result.status)

    def test_learning_case_rejects_output_mode_qa(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["F"],
            "请选择输出模式：默认、厨房执行版。\n一句话解释：锅温低会让水分来不及蒸发。",
        )

        self.assertEqual("fail", result.status)

    def test_meal_planning_accepts_schedule_with_shopping_mode_choice(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["G"],
            "## 菜单\n两菜一汤\n## 厨房排程\nT-30 开始。\n## 设备冲突\n无。\n请选择购物清单模式：完整购物清单、缺货检查清单、跳过购物清单。",
        )

        self.assertEqual("pass", result.status)

    def test_meal_planning_rejects_full_shopping_list_without_mode_choice(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["G"],
            "## 菜单\n两菜一汤\n## 厨房排程\nT-30 开始。\n## 购物清单\n### 主料\n| 食材 | 总量 |",
        )

        self.assertEqual("fail", result.status)

    def test_recipe_import_requires_persistence_and_output_shape_split(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["H"],
            "导入意图：本次对话改写\n持久化目标：不保存\n输出形态：完整解释版\n导入状态：draft",
        )

        self.assertEqual("pass", result.status)

    def test_recipe_import_rejects_missing_intent_split(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["H"],
            "导入状态：draft\n## 完整解释版",
        )

        self.assertEqual("fail", result.status)

    def test_memory_init_case_requires_write_preview(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["I"],
            "Write preview\nWill write:\n- defaults.servings = 4\nConfirm write / Edit values / Cancel",
        )

        self.assertEqual("pass", result.status)

    def test_acp_evaluation_ignores_tool_output_before_final_answer(self):
        module = load_module()

        transcript = (
            "[tool] Read templates/recipe-kitchen.md (completed)\n"
            "output:\n"
            "  # {{dish_name}}\n"
            "  默认 Recipe Generation 使用完整解释版。快速和精准不再作为选项。\n"
            "[thinking] Now answer.\n"
            "已找到你的个人资料，直接输出厨房执行版。\n"
            "\n"
            "# 番茄炒蛋\n"
            "\n"
            "## 备料\n"
            "- 鸡蛋 2 个。\n"
            "\n"
            "## 做法\n"
            "| 顺序 | 火力/时间 | 做什么 | 看到什么就下一步 | 出错怎么办 |\n"
            "| 1 | 中火 1 分钟 | 炒蛋 | 凝固 | 发硬就提前盛出 |\n"
            "\n"
            "## 安全 / 补救\n"
            "- 鸡蛋完全凝固。\n"
            "\n"
            "请选择后续交付方式：生成 PDF、直接打印、暂不需要。\n"
            "\n"
            "[done] end_turn\n"
        )

        result = module.evaluate_output(module.TEST_CASES["B"], transcript)

        self.assertEqual("pass", result.status)

    def test_plan_output_lists_full_flow_case_matrix(self):
        module = load_module()

        buffer = io.StringIO()
        with patch("sys.stdout", buffer):
            exit_code = module.print_plan(Path("/repo"), Path("/home/test"), Path("/tmp/out"))

        output = buffer.getvalue()
        self.assertEqual(0, exit_code)
        self.assertIn("## Test cases", output)
        self.assertIn("A | Recipe Generation", output)
        self.assertIn("E | Troubleshooting", output)
        self.assertIn("F | Learning", output)
        self.assertIn("G | Meal Planning", output)
        self.assertIn("H | Recipe Import", output)
        self.assertIn("I | Memory Init / Update", output)

    def test_gemini_headless_command_uses_prompt_flag(self):
        module = load_module()

        command = module.build_headless_command(
            "gemini",
            module.TEST_CASES["A"].prompt,
            Path("/repo"),
            Path("/tmp/out.txt"),
        )

        self.assertEqual("gemini", command[0])
        self.assertIn("--prompt", command)
        self.assertIn("--skip-trust", command)

    def test_codex_acp_command_uses_acpx(self):
        module = load_module()

        command = module.build_acp_command(
            "codex",
            module.TEST_CASES["A"].prompt,
            Path("/repo"),
        )

        self.assertEqual(["npx", "-y", "acpx"], command[:3])
        self.assertIn("--cwd", command)
        self.assertIn("codex", command)

    def test_codex_acp_command_uses_one_shot_exec(self):
        module = load_module()

        command = module.build_acp_command(
            "codex",
            module.TEST_CASES["A"].prompt,
            Path("/repo"),
        )

        agent_index = command.index("codex")
        self.assertEqual("exec", command[agent_index + 1])

    def test_acp_command_auto_approves_tool_requests_for_skill_loading(self):
        module = load_module()

        command = module.build_acp_command(
            "claude",
            module.TEST_CASES["A"].prompt,
            Path("/repo"),
        )

        self.assertIn("--approve-all", command)

    def test_hermes_acp_command_uses_raw_agent_one_shot_exec(self):
        module = load_module()

        command = module.build_acp_command(
            "hermes",
            module.TEST_CASES["A"].prompt,
            Path("/repo"),
        )

        self.assertIn("--agent", command)
        self.assertIn("hermes acp --accept-hooks", command)
        self.assertIn("exec", command)
        self.assertLess(command.index("exec"), len(command) - 1)

    def test_run_acp_keeps_nonzero_returncode_as_report_data_when_output_passes(self):
        module = load_module()

        original_command_available = module.command_available
        original_run_command = module.run_command

        class Completed:
            returncode = 5
            stdout = "未指定输出模式，默认生成。本次使用默认适配继续。\n## 完整解释版\n...\n请选择后续交付方式：生成 PDF、直接打印、暂不需要。"
            stderr = ""

        try:
            module.command_available = lambda _command: True
            module.run_command = lambda _command, _timeout_seconds: Completed()

            with tempfile.TemporaryDirectory() as tmp:
                output_dir = Path(tmp)
                exit_code = module.run_acp(Path("/repo"), ["claude"], ["A"], output_dir, 1)
                report_text = (output_dir / "agent-skill-qa-acp-report.jsonl").read_text(encoding="utf-8")

            self.assertEqual(0, exit_code)
            self.assertIn('"returncode": 5', report_text)
        finally:
            module.command_available = original_command_available
            module.run_command = original_run_command


if __name__ == "__main__":
    unittest.main()
