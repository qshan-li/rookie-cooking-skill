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
                Path("recipes/chinese-home/tomato-egg.md"),
                Path("recipes/chinese-home/qingjiao-rousi.md"),
                Path("recipes/chinese-home/steamed-egg.md"),
                Path("recipes/chinese-home/stir-fried-greens.md"),
                Path("recipes/chinese-home/hongshaorou.md"),
            ],
            recipes,
        )

    def test_validation_record_path_uses_recipe_stem(self):
        module = load_module()

        path = module.validation_record_path(
            Path("output/validation"),
            Path("recipes/chinese-home/tomato-egg.md"),
        )

        self.assertEqual(Path("output/validation/tomato-egg-validation.json"), path)


if __name__ == "__main__":
    unittest.main()
