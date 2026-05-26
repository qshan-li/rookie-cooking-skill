import importlib.util
from pathlib import Path
import sys
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "apply_kitchen_validation.py"


def load_module():
    spec = importlib.util.spec_from_file_location("apply_kitchen_validation", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load apply_kitchen_validation.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALID_RECORD = {
    "date": "2026-05-26",
    "cook": "test-cook",
    "environment": "gas stove, wok, no thermometer",
    "servings": "2",
    "ingredient_weights": "番茄 360 g，鸡蛋 150 g",
    "step_times": "18 分钟",
    "heat_notes": "中火炒番茄 3 分钟",
    "state_checks": "番茄出汁 80 ml，鸡蛋表面湿润时盛出",
    "failure_points": "无",
    "changes": "无需修改",
    "conclusion": "validated-candidate",
}


BASE_RECIPE = """# 番茄炒蛋

## 完整解释版

## 厨房执行版

### Review

- 状态：`passed`
- Review 日期：2026-05-26
- 未解决风险：未做真实厨房实测。
"""


class ApplyKitchenValidationTest(unittest.TestCase):
    def test_appends_complete_record_without_marking_validated_by_default(self):
        module = load_module()

        updated = module.apply_record(BASE_RECIPE, VALID_RECORD, mark_validated=False)

        self.assertIn("## 厨房实测记录", updated)
        self.assertIn("### 实测 2026-05-26", updated)
        self.assertIn("- 实际克数：番茄 360 g，鸡蛋 150 g", updated)
        self.assertIn("- 结论：`validated-candidate`", updated)
        self.assertIn("- 状态：`passed`", updated)

    def test_mark_validated_updates_review_status_for_validated_candidate(self):
        module = load_module()

        updated = module.apply_record(BASE_RECIPE, VALID_RECORD, mark_validated=True)

        self.assertIn("- 状态：`validated`", updated)
        self.assertNotIn("- 状态：`passed`", updated)

    def test_mark_validated_rejects_non_candidate_record(self):
        module = load_module()
        record = {**VALID_RECORD, "conclusion": "revise-needed"}

        with self.assertRaises(ValueError):
            module.apply_record(BASE_RECIPE, record, mark_validated=True)

    def test_missing_record_field_is_rejected(self):
        module = load_module()
        record = dict(VALID_RECORD)
        del record["heat_notes"]

        with self.assertRaises(ValueError):
            module.apply_record(BASE_RECIPE, record, mark_validated=False)


if __name__ == "__main__":
    unittest.main()
