import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sync_skill_install.py"


def load_module():
    spec = importlib.util.spec_from_file_location("sync_skill_install", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load sync_skill_install.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SyncSkillInstallTest(unittest.TestCase):
    def test_sync_copies_source_to_central_install_and_excludes_generated_paths(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            home = Path(tmp) / "home"
            root.mkdir()
            home.mkdir()
            (root / "SKILL.md").write_text("---\nname: rookie-cooking\n---\n", encoding="utf-8")
            (root / "scripts").mkdir()
            (root / "scripts" / "tool.py").write_text("print('ok')\n", encoding="utf-8")
            (root / ".git").mkdir()
            (root / ".git" / "config").write_text("ignored\n", encoding="utf-8")
            (root / "output").mkdir()
            (root / "output" / "generated.pdf").write_text("ignored\n", encoding="utf-8")
            (root / "tmp").mkdir()
            (root / "tmp" / "scratch.html").write_text("ignored\n", encoding="utf-8")

            result = module.sync_skill(root, home, include_agent_links=False)

            install = home / ".local" / "share" / "agent-skills" / module.SKILL_NAME
            self.assertIn(install, result.synced_paths)
            self.assertTrue((install / "SKILL.md").exists())
            self.assertTrue((install / "scripts" / "tool.py").exists())
            self.assertFalse((install / ".git").exists())
            self.assertFalse((install / "output").exists())
            self.assertFalse((install / "tmp").exists())

    def test_sync_refuses_to_install_inside_source_tree(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            home = root / "fake-home"
            root.mkdir()
            home.mkdir()
            (root / "SKILL.md").write_text("---\nname: rookie-cooking\n---\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                module.sync_skill(root, home, include_agent_links=False)

    def test_sync_creates_agent_skill_links_to_central_install(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            home = Path(tmp) / "home"
            root.mkdir()
            home.mkdir()
            (root / "SKILL.md").write_text("---\nname: rookie-cooking\n---\n", encoding="utf-8")

            result = module.sync_skill(root, home, include_agent_links=True)

            central = home / ".local" / "share" / "agent-skills" / module.SKILL_NAME
            link = home / ".codex" / "skills" / module.SKILL_NAME
            self.assertIn(link, result.linked_paths)
            self.assertTrue(link.is_symlink())
            self.assertEqual(central, link.resolve())


if __name__ == "__main__":
    unittest.main()
