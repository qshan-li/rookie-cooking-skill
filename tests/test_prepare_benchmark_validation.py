import importlib.util
from pathlib import Path
import sys
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "prepare_benchmark_validation.py"


def load_module():
    spec = importlib.util.spec_from_file_location("prepare_benchmark_validation", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load prepare_benchmark_validation.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PrepareBenchmarkValidationTest(unittest.TestCase):
    def test_lists_the_five_benchmark_recipes(self):
        module = load_module()

        recipes = module.benchmark_recipes(Path("."))

        self.assertEqual(
            [
                Path("recipes/vegetable/fan-qie-chao-dan.md"),
                Path("recipes/meat/qing-jiao-rou-si.md"),
                Path("recipes/soup/zheng-dan-geng.md"),
                Path("recipes/vegetable/qing-chao-xiao-qing-cai.md"),
                Path("recipes/meat/hong-shao-rou.md"),
            ],
            recipes,
        )

    def test_validation_record_path_uses_recipe_stem(self):
        module = load_module()

        path = module.validation_record_path(
            Path("output/validation"),
            Path("recipes/vegetable/fan-qie-chao-dan.md"),
        )

        self.assertEqual(Path("output/validation/fan-qie-chao-dan-validation.json"), path)


if __name__ == "__main__":
    unittest.main()
