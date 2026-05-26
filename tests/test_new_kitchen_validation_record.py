import importlib.util
from pathlib import Path
import sys
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "new_kitchen_validation_record.py"


def load_module():
    spec = importlib.util.spec_from_file_location("new_kitchen_validation_record", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load new_kitchen_validation_record.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class NewKitchenValidationRecordTest(unittest.TestCase):
    def test_builds_blank_record_from_recipe_heading(self):
        module = load_module()

        record = module.build_record(
            "# 番茄炒蛋\n\n## 完整解释版\n",
            date="2026-05-26",
        )

        self.assertEqual("番茄炒蛋", record["recipe"])
        self.assertEqual("2026-05-26", record["date"])
        self.assertEqual("", record["cook"])
        self.assertEqual("", record["ingredient_weights"])
        self.assertEqual("keep-passed", record["conclusion"])

    def test_rejects_recipe_without_heading(self):
        module = load_module()

        with self.assertRaises(ValueError):
            module.build_record("## 完整解释版\n", date="2026-05-26")


if __name__ == "__main__":
    unittest.main()
