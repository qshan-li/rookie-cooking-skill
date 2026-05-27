import importlib.util
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "render_recipe_pdf.py"


def load_module():
    spec = importlib.util.spec_from_file_location("render_recipe_pdf", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load render_recipe_pdf.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RenderRecipePdfTest(unittest.TestCase):
    def test_print_css_keeps_headings_with_following_content(self):
        css = (Path(__file__).resolve().parents[1] / "assets" / "print.css").read_text(encoding="utf-8")

        self.assertIn("break-after: avoid", css)
        self.assertIn("page-break-after: avoid", css)
        self.assertIn("h1 + p", css)
        self.assertIn("h2 + table", css)

    def test_build_html_adds_recipe_title_to_printable_body(self):
        module = load_module()

        html = module.build_html("## 厨房执行版\n\n- 开火。", "", "番茄炒蛋")

        self.assertIn("<title>番茄炒蛋</title>", html)
        self.assertIn("<h1>番茄炒蛋</h1>", html)
        self.assertNotIn("<h2>厨房执行版</h2>", html)
        self.assertIn("<li>开火。</li>", html)

    def test_pdf_name_does_not_duplicate_kitchen_suffix(self):
        module = load_module()

        self.assertEqual("hao-you-sheng-cai-kitchen", module.kitchen_output_stem("hao-you-sheng-cai"))
        self.assertEqual(
            "hao-you-sheng-cai-kitchen",
            module.kitchen_output_stem("hao-you-sheng-cai-kitchen"),
        )

    def test_main_uses_recipe_heading_as_printable_title(self):
        module = load_module()

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            recipe_path = tmp_path / "fan-qie-chao-dan.md"
            css_path = tmp_path / "print.css"
            output_dir = tmp_path / "output"
            html_dir = tmp_path / "html"
            recipe_path.write_text(
                "# 番茄炒蛋\n\n## 完整解释版\n\n正文\n\n## 厨房执行版\n\n- 开火。\n",
                encoding="utf-8",
            )
            css_path.write_text("", encoding="utf-8")

            argv = [
                "render_recipe_pdf.py",
                str(recipe_path),
                "--output-dir",
                str(output_dir),
                "--tmp-dir",
                str(html_dir),
                "--css",
                str(css_path),
            ]
            with (
                patch.object(sys, "argv", argv),
                patch.object(module, "find_chrome", return_value="chrome"),
                patch.object(module, "render_pdf"),
                patch("builtins.print"),
            ):
                module.main()

            html = (html_dir / "fan-qie-chao-dan.html").read_text(encoding="utf-8")
            self.assertIn("<title>番茄炒蛋</title>", html)
            self.assertIn("<h1>番茄炒蛋</h1>", html)

    def test_main_can_directly_print_generated_kitchen_pdf(self):
        module = load_module()

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            recipe_path = tmp_path / "fan-qie-chao-dan.md"
            css_path = tmp_path / "print.css"
            output_dir = tmp_path / "output"
            html_dir = tmp_path / "html"
            recipe_path.write_text(
                "# 番茄炒蛋\n\n## 完整解释版\n\n正文\n\n## 厨房执行版\n\n- 开火。\n",
                encoding="utf-8",
            )
            css_path.write_text("", encoding="utf-8")

            argv = [
                "render_recipe_pdf.py",
                str(recipe_path),
                "--output-dir",
                str(output_dir),
                "--tmp-dir",
                str(html_dir),
                "--css",
                str(css_path),
                "--print",
                "--printer",
                "KitchenPrinter",
            ]
            with (
                patch.object(sys, "argv", argv),
                patch.object(module, "find_chrome", return_value="chrome"),
                patch.object(module, "render_pdf"),
                patch.object(module, "print_pdf") as print_pdf,
                patch("builtins.print"),
            ):
                module.main()

            print_pdf.assert_called_once_with(
                output_dir.resolve() / "fan-qie-chao-dan-kitchen.pdf",
                "KitchenPrinter",
            )

    def test_list_printers_uses_lpstat_when_available(self):
        module = load_module()

        class Completed:
            returncode = 0
            stdout = "KitchenPrinter\nOfficePrinter\n"
            stderr = ""

        with (
            patch.object(module, "_load_printer_module", side_effect=RuntimeError("no printer module")),
            patch.object(module.shutil, "which", return_value="/usr/bin/lpstat"),
            patch.object(module.subprocess, "run", return_value=Completed()) as run,
        ):
            printers = module.list_printers()

        run.assert_called_once_with(
            ["/usr/bin/lpstat", "-e"],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(["KitchenPrinter", "OfficePrinter"], printers)

    def test_main_can_list_printers_before_print_choice(self):
        module = load_module()

        argv = ["render_recipe_pdf.py", "--list-printers"]
        with (
            patch.object(sys, "argv", argv),
            patch.object(module, "list_printers", return_value=["KitchenPrinter", "OfficePrinter"]),
            patch("builtins.print") as print_call,
        ):
            module.main()

        print_call.assert_any_call("KitchenPrinter")
        print_call.assert_any_call("OfficePrinter")

    def test_main_renders_temporary_kitchen_markdown_without_recipe_file(self):
        module = load_module()

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            kitchen_path = tmp_path / "tang-cu-pai-gu.md"
            css_path = tmp_path / "print.css"
            output_dir = tmp_path / "output"
            html_dir = tmp_path / "html"
            kitchen_path.write_text("## 厨房执行版\n\n- 收汁 2 分钟。\n", encoding="utf-8")
            css_path.write_text("", encoding="utf-8")

            argv = [
                "render_recipe_pdf.py",
                "--kitchen-markdown",
                str(kitchen_path),
                "--title",
                "糖醋排骨",
                "--output-dir",
                str(output_dir),
                "--tmp-dir",
                str(html_dir),
                "--css",
                str(css_path),
            ]
            with (
                patch.object(sys, "argv", argv),
                patch.object(module, "find_chrome", return_value="chrome"),
                patch.object(module, "render_pdf"),
                patch("builtins.print"),
            ):
                module.main()

            html = (html_dir / "tang-cu-pai-gu.html").read_text(encoding="utf-8")
            self.assertIn("<title>糖醋排骨</title>", html)
            self.assertIn("<h1>糖醋排骨</h1>", html)
            self.assertNotIn("<h2>厨房执行版</h2>", html)
            self.assertIn("<li>收汁 2 分钟。</li>", html)
            self.assertFalse(kitchen_path.exists())

    def test_temporary_kitchen_markdown_extracts_kitchen_section_from_full_recipe(self):
        module = load_module()

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            kitchen_path = tmp_path / "fan-qie-chao-dan.md"
            css_path = tmp_path / "print.css"
            output_dir = tmp_path / "output"
            html_dir = tmp_path / "html"
            kitchen_path.write_text(
                (
                    "# 番茄炒蛋\n\n"
                    "## 完整解释版\n\n"
                    "完整解释正文。\n\n"
                    "## 厨房执行版\n\n"
                    "- 开火。\n\n"
                    "### Review\n\n"
                    "- 状态：`draft`\n"
                ),
                encoding="utf-8",
            )
            css_path.write_text("", encoding="utf-8")

            argv = [
                "render_recipe_pdf.py",
                "--kitchen-markdown",
                str(kitchen_path),
                "--title",
                "番茄炒蛋",
                "--output-dir",
                str(output_dir),
                "--tmp-dir",
                str(html_dir),
                "--css",
                str(css_path),
            ]
            with (
                patch.object(sys, "argv", argv),
                patch.object(module, "find_chrome", return_value="chrome"),
                patch.object(module, "render_pdf"),
                patch("builtins.print"),
            ):
                module.main()

            html = (html_dir / "fan-qie-chao-dan.html").read_text(encoding="utf-8")
            self.assertIn("<h1>番茄炒蛋</h1>", html)
            self.assertIn("<li>开火。</li>", html)
            self.assertNotIn("完整解释正文", html)
            self.assertNotIn("Review", html)

    def test_temporary_kitchen_markdown_strips_embedded_title(self):
        module = load_module()

        html = module.build_html("# 番茄炒蛋 厨房执行版\n\n- 开火。", "", "番茄炒蛋")

        self.assertIn("<h1>番茄炒蛋</h1>", html)
        self.assertNotIn("<h1>番茄炒蛋 厨房执行版</h1>", html)
        self.assertIn("<li>开火。</li>", html)

    def test_main_avoids_duplicate_kitchen_suffix_for_temporary_markdown_pdf(self):
        module = load_module()

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            kitchen_path = tmp_path / "hao-you-sheng-cai-kitchen.md"
            css_path = tmp_path / "print.css"
            output_dir = tmp_path / "output"
            html_dir = tmp_path / "html"
            kitchen_path.write_text("## 厨房执行版\n\n- 焯生菜。", encoding="utf-8")
            css_path.write_text("", encoding="utf-8")

            argv = [
                "render_recipe_pdf.py",
                "--kitchen-markdown",
                str(kitchen_path),
                "--title",
                "蚝油生菜",
                "--output-dir",
                str(output_dir),
                "--tmp-dir",
                str(html_dir),
                "--css",
                str(css_path),
            ]
            with (
                patch.object(sys, "argv", argv),
                patch.object(module, "find_chrome", return_value="chrome"),
                patch.object(module, "render_pdf") as render_pdf,
                patch("builtins.print"),
            ):
                module.main()

            self.assertEqual(
                output_dir.resolve() / "hao-you-sheng-cai-kitchen.pdf",
                render_pdf.call_args.args[2],
            )

    def test_temporary_kitchen_markdown_can_use_recipe_slug_for_pdf_name(self):
        module = load_module()

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            kitchen_path = tmp_path / "print-job.md"
            css_path = tmp_path / "print.css"
            output_dir = tmp_path / "output"
            html_dir = tmp_path / "html"
            kitchen_path.write_text("## 厨房执行版\n\n- 炒饭。", encoding="utf-8")
            css_path.write_text("", encoding="utf-8")

            argv = [
                "render_recipe_pdf.py",
                "--kitchen-markdown",
                str(kitchen_path),
                "--title",
                "卤牛肉炒饭",
                "--output-stem",
                "lu-niu-rou-chao-fan",
                "--output-dir",
                str(output_dir),
                "--tmp-dir",
                str(html_dir),
                "--css",
                str(css_path),
            ]
            with (
                patch.object(sys, "argv", argv),
                patch.object(module, "find_chrome", return_value="chrome"),
                patch.object(module, "render_pdf") as render_pdf,
                patch("builtins.print"),
            ):
                module.main()

            self.assertEqual(
                output_dir.resolve() / "lu-niu-rou-chao-fan-kitchen.pdf",
                render_pdf.call_args.args[2],
            )
            self.assertTrue((html_dir / "lu-niu-rou-chao-fan.html").exists())

    def test_main_keeps_recipe_file_when_rendering_repository_recipe(self):
        module = load_module()

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            recipe_path = tmp_path / "fan-qie-chao-dan.md"
            css_path = tmp_path / "print.css"
            output_dir = tmp_path / "output"
            html_dir = tmp_path / "html"
            recipe_path.write_text(
                "# 番茄炒蛋\n\n## 完整解释版\n\n正文\n\n## 厨房执行版\n\n- 开火。\n",
                encoding="utf-8",
            )
            css_path.write_text("", encoding="utf-8")

            argv = [
                "render_recipe_pdf.py",
                str(recipe_path),
                "--output-dir",
                str(output_dir),
                "--tmp-dir",
                str(html_dir),
                "--css",
                str(css_path),
            ]
            with (
                patch.object(sys, "argv", argv),
                patch.object(module, "find_chrome", return_value="chrome"),
                patch.object(module, "render_pdf"),
                patch("builtins.print"),
            ):
                module.main()

            self.assertTrue(recipe_path.exists())

    def test_default_output_paths_live_under_rookie_cooking_home(self):
        module = load_module()

        expected_home = Path.home() / ".rookie-cooking"

        self.assertEqual(expected_home / "output" / "pdf", module.DEFAULT_OUTPUT_DIR)
        self.assertEqual(expected_home / "tmp" / "pdfs", module.DEFAULT_TMP_DIR)

    def test_main_set_default_printer(self):
        module = load_module()
        mock_printer = MagicMock()
        argv = ["render_recipe_pdf.py", "--set-default", "192.168.1.100"]
        with (
            patch.object(sys, "argv", argv),
            patch.object(module, "_load_printer_module", return_value=mock_printer),
            patch("builtins.print") as print_call,
        ):
            module.main()
        mock_printer.set_default_printer.assert_called_once_with("192.168.1.100")
        print_call.assert_any_call("默认打印机已设置: 192.168.1.100")

    def test_main_test_printer_success(self):
        module = load_module()
        mock_printer = MagicMock()
        mock_printer.ipp_get_printer_attributes.return_value = MagicMock(status="idle")
        argv = ["render_recipe_pdf.py", "--test-printer", "192.168.1.50"]
        with (
            patch.object(sys, "argv", argv),
            patch.object(module, "_load_printer_module", return_value=mock_printer),
            patch("builtins.print") as print_call,
        ):
            module.main()
        mock_printer.ipp_get_printer_attributes.assert_called_once_with("192.168.1.50")
        print_call.assert_any_call("打印机可达: 192.168.1.50")

    def test_main_test_printer_failure_exits_nonzero(self):
        module = load_module()

        class FakePrinterError(Exception):
            def __init__(self):
                super().__init__("打印机当前不可用")
                self.message = "打印机当前不可用"

        mock_printer = MagicMock()
        mock_printer.PrinterError = FakePrinterError
        mock_printer.ipp_get_printer_attributes.side_effect = FakePrinterError()
        argv = ["render_recipe_pdf.py", "--test-printer", "192.168.1.50"]
        with (
            patch.object(sys, "argv", argv),
            patch.object(module, "_load_printer_module", return_value=mock_printer),
            patch("builtins.print") as print_call,
            self.assertRaises(SystemExit) as ctx,
        ):
            module.main()
        self.assertEqual(ctx.exception.code, 1)
        print_call.assert_any_call("打印机不可达: 192.168.1.50")


if __name__ == "__main__":
    unittest.main()
