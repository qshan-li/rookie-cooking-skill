import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


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
            (root / "SKILL.md").write_text("---\nname: rookie-cooking-skill\n---\n", encoding="utf-8")

            checks = module.local_install_checks(root, home)

        self.assertFalse(any(check.installed for check in checks))
        self.assertTrue(all(root / "SKILL.md" not in check.paths for check in checks))

    def test_claude_project_skill_directory_is_detected(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            home = Path(tmp) / "home"
            skill_dir = root / ".claude" / "skills" / "rookie-cooking-skill"
            skill_dir.mkdir(parents=True)
            home.mkdir()
            (skill_dir / "SKILL.md").write_text("---\nname: rookie-cooking-skill\n---\n", encoding="utf-8")

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
            "未指定输出模式，默认生成。\n## 完整解释版\n...\n## 厨房执行版\n...",
        )

        self.assertEqual("fail", result.status)

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
            "## 厨房执行版\n安全提示\n失败信号\n请选择后续交付方式：生成 PDF、直接打印、暂不需要。",
        )

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

    def test_memory_init_case_requires_write_preview(self):
        module = load_module()

        result = module.evaluate_output(
            module.TEST_CASES["I"],
            "Write preview\nWill write:\n- defaults.servings = 4\nConfirm write / Edit values / Cancel",
        )

        self.assertEqual("pass", result.status)

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
