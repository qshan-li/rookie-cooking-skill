from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RecipeKitchenTemplateTest(unittest.TestCase):
    def test_kitchen_template_is_one_page_print_card(self):
        template = (ROOT / "templates" / "recipe-kitchen.md").read_text(encoding="utf-8")

        self.assertTrue(template.startswith("# {{dish_name}}\n"))
        self.assertIn("{{servings}}｜{{total_time}}｜{{equipment}}｜目标：{{target_result}}", template)
        self.assertIn("## 备料", template)
        self.assertIn("## 做法", template)
        self.assertIn("| 顺序 | 火力/时间 | 做什么 | 看到什么就下一步 | 出错怎么办 |", template)
        self.assertIn("## 安全 / 补救", template)

    def test_kitchen_template_omits_chat_only_or_duplicate_print_sections(self):
        template = (ROOT / "templates" / "recipe-kitchen.md").read_text(encoding="utf-8")

        self.assertNotIn("# {{dish_name}} 厨房执行版", template)
        self.assertNotIn("## 时间线", template)
        self.assertNotIn("## 步骤", template)
        self.assertNotIn("## 失败信号", template)
        self.assertNotIn("本次使用的偏好 / 假设", template)
        self.assertNotIn("{{applied_feedback_or_none}}", template)

    def test_print_css_uses_compact_kitchen_card_spacing(self):
        css = (ROOT / "assets" / "print.css").read_text(encoding="utf-8")

        self.assertIn("margin: 10mm;", css)
        self.assertIn("font-size: 11pt;", css)
        self.assertIn("line-height: 1.35;", css)
        self.assertIn("font-size: 19pt;", css)
        self.assertIn("padding: 1.2mm 1.4mm;", css)


if __name__ == "__main__":
    unittest.main()
