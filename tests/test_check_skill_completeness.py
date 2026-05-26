import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_skill_completeness.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_skill_completeness", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load check_skill_completeness.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class KitchenValidationRulesTest(unittest.TestCase):
    def test_passed_recipe_does_not_need_kitchen_validation_record(self):
        checker = load_checker()

        violations = checker.validate_kitchen_validation_status(
            "# 番茄炒蛋\n\n### Review\n\n- 状态：`passed`\n",
            Path("recipes/chinese-home/tomato-egg.md"),
        )

        self.assertEqual([], violations)

    def test_validated_recipe_requires_a_complete_kitchen_record(self):
        checker = load_checker()

        violations = checker.validate_kitchen_validation_status(
            "# 番茄炒蛋\n\n### Review\n\n- 状态：`validated`\n",
            Path("recipes/chinese-home/tomato-egg.md"),
        )

        self.assertIn("validated status requires ## 厨房实测记录", violations)

    def test_complete_kitchen_record_allows_validated_status(self):
        checker = load_checker()

        violations = checker.validate_kitchen_validation_status(
            """# 番茄炒蛋

### Review

- 状态：`validated`

## 厨房实测记录

### 实测 2026-05-26

- 操作者：test
- 环境：gas, wok, no thermometer
- 实际份量：2
- 实际克数：番茄 360 g，鸡蛋 150 g
- 实际时间：18 分钟
- 火力记录：中火炒番茄 3 分钟
- 状态判断：番茄出汁 80 ml
- 失败点：无
- 修正建议：无需修改
- 结论：`validated-candidate`
""",
            Path("recipes/chinese-home/tomato-egg.md"),
        )

        self.assertEqual([], violations)


class RepositoryChecksTest(unittest.TestCase):
    def test_repository_check_requires_at_least_twenty_recipes(self):
        checker = load_checker()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "recipes" / "chinese-home").mkdir(parents=True)
            (root / "references").mkdir()
            (root / "references" / "source-notes.md").write_text("| 番茄炒蛋 |\n", encoding="utf-8")
            (root / "recipes" / "chinese-home" / "tomato-egg.md").write_text(
                """# 番茄炒蛋

## 完整解释版

| 步骤 | 操作 | 时间 | 火力 | 目标状态 | 失败信号 | 为什么 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | test | 1 分钟 | 中火 | test | test | test |

### 食品安全

- test

## 厨房执行版

### Review

- 状态：`passed`
- `protein-denaturation`
""",
                encoding="utf-8",
            )

            result = checker.check_repository(root)

        self.assertFalse(result.ok)
        self.assertIn("recipe_count=1 required=20", result.errors)

    def test_repository_check_fails_when_required_benchmark_validations_are_missing(self):
        checker = load_checker()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "recipes" / "chinese-home").mkdir(parents=True)
            (root / "references").mkdir()
            (root / "references" / "source-notes.md").write_text("| 番茄炒蛋 |\n", encoding="utf-8")
            (root / "recipes" / "chinese-home" / "tomato-egg.md").write_text(
                """# 番茄炒蛋

## 完整解释版

| 步骤 | 操作 | 时间 | 火力 | 目标状态 | 失败信号 | 为什么 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | test | 1 分钟 | 中火 | test | test | test |

### 食品安全

- test

## 厨房执行版

### Review

- 状态：`passed`
- `protein-denaturation`
""",
                encoding="utf-8",
            )

            result = checker.check_repository(root, required_benchmark_validations=1)

        self.assertFalse(result.ok)
        self.assertIn("benchmark_validated=0 required=1", result.errors)


if __name__ == "__main__":
    unittest.main()
