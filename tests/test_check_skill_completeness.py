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
            Path("recipes/vegetable/fan-qie-chao-dan.md"),
        )

        self.assertEqual([], violations)

    def test_validated_recipe_requires_a_complete_kitchen_record(self):
        checker = load_checker()

        violations = checker.validate_kitchen_validation_status(
            "# 番茄炒蛋\n\n### Review\n\n- 状态：`validated`\n",
            Path("recipes/vegetable/fan-qie-chao-dan.md"),
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
            Path("recipes/vegetable/fan-qie-chao-dan.md"),
        )

        self.assertEqual([], violations)


class RepositoryChecksTest(unittest.TestCase):
    def test_migration_manifest_must_cover_howtocook_recipe_targets(self):
        checker = load_checker()

        violations = checker.validate_migration_manifest(
            "| 上游路径 | 目标文件 | 目标目录 | 迁移状态 |\n"
            "| --- | --- | --- | --- |\n",
            [Path("recipes/vegetable/fan-qie-chao-dan.md")],
        )

        self.assertEqual(
            ["migration manifest missing target: recipes/vegetable/fan-qie-chao-dan.md"],
            violations,
        )

    def test_migration_manifest_accepts_listed_howtocook_recipe_targets(self):
        checker = load_checker()

        violations = checker.validate_migration_manifest(
            "| 上游路径 | 目标文件 | 目标目录 | 迁移状态 |\n"
            "| --- | --- | --- | --- |\n"
            "| `dishes/vegetable_dish/西红柿炒鸡蛋.md` | "
            "`recipes/vegetable/fan-qie-chao-dan.md` | `recipes/vegetable/` | `passed` |\n",
            [Path("recipes/vegetable/fan-qie-chao-dan.md")],
        )

        self.assertEqual([], violations)

    def test_migration_manifest_rejects_unresolved_source_status(self):
        checker = load_checker()

        violations = checker.validate_migration_manifest(
            "| 上游路径 | 目标文件 | 目标目录 | 迁移状态 |\n"
            "| --- | --- | --- | --- |\n"
            "| 原创整理 | `recipes/cold-dish/sha-la-you-cu-zhi.md` | "
            "`recipes/cold-dish/` | `source-needs-normalization` |\n",
            [],
        )

        self.assertEqual(
            ["migration manifest contains unresolved source status: source-needs-normalization"],
            violations,
        )

    def test_howtocook_source_recipe_cannot_stay_draft(self):
        checker = load_checker()

        violations = checker.validate_recipe(
            """# 番茄炒蛋

## 完整解释版

| 步骤 | 操作 | 时间 | 火力 | 目标状态 | 失败信号 | 为什么 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | test | 1 分钟 | 中火 | test | test | test |

### 食品安全

- test

## 厨房执行版

### Review

- 状态：`draft`
- `protein-denaturation`

## 来源说明

- 基础参考：Anduin2017/HowToCook `dishes/vegetable_dish/西红柿炒鸡蛋.md`
""",
            Path("recipes/vegetable/fan-qie-chao-dan.md"),
            "| 番茄炒蛋 |\n",
        )

        self.assertIn("HowToCook source recipes must be `passed` or `validated`", violations)

    def test_recipe_requires_applied_preferences_or_assumptions(self):
        checker = load_checker()

        violations = checker.validate_recipe(
            """# 用户自建菜

## 完整解释版

| 步骤 | 操作 | 时间 | 火力 | 目标状态 | 失败信号 | 为什么 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | test | 1 分钟 | 中火 | test | test | test |

### 食品安全

- test

## 厨房执行版

### Review

- 状态：`draft`
- `protein-denaturation`

## 来源说明

- 基础参考：用户自建。
""",
            Path("recipes/vegetable/user-recipe.md"),
            "| 用户自建菜 |\n",
        )

        self.assertIn("missing applied preferences or assumptions", violations)

    def test_non_howtocook_recipe_can_stay_draft(self):
        checker = load_checker()

        violations = checker.validate_recipe(
            """# 用户自建菜

## 完整解释版

| 步骤 | 操作 | 时间 | 火力 | 目标状态 | 失败信号 | 为什么 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | test | 1 分钟 | 中火 | test | test | test |

- 已使用偏好 / 假设：默认 2 人份、普通家庭灶具、无温度计

### 食品安全

- test

## 厨房执行版

### Review

- 状态：`draft`
- `protein-denaturation`

## 来源说明

- 基础参考：用户自建。
""",
            Path("recipes/vegetable/user-recipe.md"),
            "| 用户自建菜 |\n",
        )

        self.assertEqual([], violations)

    def test_repository_check_requires_skill_structure_paths(self):
        checker = load_checker()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            result = checker.check_repository(root)

        self.assertFalse(result.ok)
        self.assertIn("missing required path: SKILL.md", result.errors)
        self.assertIn("missing required path: agents/openai.yaml", result.errors)
        self.assertIn("missing required path: templates/recipe-full.md", result.errors)
        self.assertIn("missing required path: docs/howtocook-migration-manifest.md", result.errors)
        self.assertIn("missing required path: references/user-profile.example.yaml", result.errors)
        self.assertIn("missing required path: references/feedback-log.example.yaml", result.errors)
        self.assertIn("missing required path: references/memory-merge-rules.md", result.errors)
        self.assertIn("missing required path: templates/meal-plan.md", result.errors)
        self.assertIn("missing required path: references/meal-planning-rules.md", result.errors)
        self.assertIn("missing required path: templates/recipe-changelog.md", result.errors)
        self.assertIn("missing required path: references/recipe-versioning.md", result.errors)
        self.assertIn("missing required path: templates/imported-recipe-review.md", result.errors)
        self.assertIn("missing required path: references/recipe-import-rules.md", result.errors)
        self.assertIn("missing required path: scripts/cooking_memory.py", result.errors)
        self.assertIn("missing required path: scripts/sync_skill_install.py", result.errors)

    def test_repository_check_requires_ten_principle_cards(self):
        checker = load_checker()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "recipes" / "vegetable").mkdir(parents=True)
            (root / "references").mkdir()
            (root / "references" / "source-notes.md").write_text("", encoding="utf-8")

            result = checker.check_repository(root)

        self.assertFalse(result.ok)
        self.assertIn("principle_count=0 required=10", result.errors)

    def test_repository_check_requires_at_least_twenty_recipes(self):
        checker = load_checker()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "recipes" / "vegetable").mkdir(parents=True)
            (root / "references").mkdir()
            (root / "references" / "source-notes.md").write_text("| 番茄炒蛋 |\n", encoding="utf-8")
            (root / "recipes" / "vegetable" / "fan-qie-chao-dan.md").write_text(
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
            (root / "recipes" / "vegetable").mkdir(parents=True)
            (root / "references").mkdir()
            (root / "references" / "source-notes.md").write_text("| 番茄炒蛋 |\n", encoding="utf-8")
            (root / "recipes" / "vegetable" / "fan-qie-chao-dan.md").write_text(
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
