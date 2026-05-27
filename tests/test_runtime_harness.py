import importlib.util
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "runtime_harness.py"


def load_module():
    spec = importlib.util.spec_from_file_location("runtime_harness", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load runtime_harness.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RuntimeHarnessTest(unittest.TestCase):
    def test_detect_python_uses_windows_py_launcher_fallback(self):
        module = load_module()

        def fake_run(command, **kwargs):
            completed = MagicMock()
            if command == ["py", "-3", "--version"]:
                completed.returncode = 0
                completed.stdout = "Python 3.12.6\n"
                completed.stderr = ""
                return completed
            completed.returncode = 1
            completed.stdout = ""
            completed.stderr = "not found"
            return completed

        with patch.object(module.subprocess, "run", side_effect=fake_run):
            result = module.detect_python(
                candidates=(("python3",), ("python",), ("py", "-3")),
                include_current=False,
            )

        self.assertTrue(result.available)
        self.assertEqual(("py", "-3"), result.command)
        self.assertEqual("3.12.6", result.version)

    def test_doctor_records_runtime_status(self):
        module = load_module()

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = module.build_runtime_status(
                memory_root=root,
                platform_name="Windows",
                python_result=module.PythonCheck(
                    available=True,
                    command=("py", "-3"),
                    version="3.12.6",
                    error=None,
                ),
            )
            module.write_runtime_record(root, result)
            record = json.loads((root / "runtime.json").read_text(encoding="utf-8"))

        self.assertEqual("py -3", record["python"]["command"])
        self.assertEqual("3.12.6", record["python"]["version"])
        self.assertTrue(record["capabilities"]["memory"])
        self.assertTrue(record["capabilities"]["pdf"])
        self.assertTrue(record["capabilities"]["printing"])

    def test_missing_python_produces_windows_install_hint(self):
        module = load_module()

        result = module.build_runtime_status(
            memory_root=Path("/tmp/rookie-cooking"),
            platform_name="Windows",
            python_result=module.PythonCheck(
                available=False,
                command=(),
                version=None,
                error="No Python command found",
            ),
        )

        self.assertFalse(result["python"]["available"])
        self.assertFalse(result["capabilities"]["memory"])
        self.assertFalse(result["capabilities"]["pdf"])
        self.assertFalse(result["capabilities"]["printing"])
        self.assertIn("winget install Python.Python.3.12", result["install_hint"])
        self.assertIn("py -3 -m pip install -r requirements.txt", result["install_hint"])


if __name__ == "__main__":
    unittest.main()
