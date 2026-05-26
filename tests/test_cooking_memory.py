import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "cooking_memory.py"


def load_memory_module():
    spec = importlib.util.spec_from_file_location("cooking_memory", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load cooking_memory.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CookingMemoryTest(unittest.TestCase):
    def test_memory_root_prefers_environment_override(self):
        memory = load_memory_module()

        root = memory.memory_root({"ROOKIE_COOKING_HOME": "/tmp/rookie-test"})

        self.assertEqual(Path("/tmp/rookie-test"), root)

    def test_read_returns_no_memory_when_profile_is_missing(self):
        memory = load_memory_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            result = memory.read_memory(Path(temp_dir), dish="tomato-egg", diners=["self"])

        self.assertFalse(result["memory_found"])
        self.assertEqual({}, result["applied"])
        self.assertIn("No cooking profile found", result["notices"][0])

    def test_init_profile_creates_readable_defaults(self):
        memory = load_memory_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            memory.init_profile(root)

            result = memory.read_memory(root, dish="tomato-egg", diners=["self"])

        self.assertTrue(result["memory_found"])
        self.assertEqual(2, result["applied"]["servings"]["value"])
        self.assertFalse(result["applied"]["equipment"]["has_thermometer"]["value"])
        self.assertEqual("mild", result["applied"]["taste"]["spice_level"]["value"])

    def test_read_filters_household_members_by_requested_diners(self):
        memory = load_memory_module()

        profile = {
            "profile_version": 1,
            "defaults": {"servings": 2},
            "taste": {"salt_level": "normal"},
            "equipment": {"has_scale": True},
            "household_members": [
                {
                    "member_id": "self",
                    "display_name": "我",
                    "taste": {"spice_level": "mild"},
                    "dislikes": {"ingredients": []},
                },
                {
                    "member_id": "partner",
                    "display_name": "家人",
                    "taste": {"spice_level": "none"},
                    "dislikes": {"ingredients": ["香菜"]},
                },
            ],
            "recipe_preferences": {},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            memory.write_profile(root, profile)

            result = memory.read_memory(root, dish="tomato-egg", diners=["partner"])

        members = result["applied"]["household_members"]
        self.assertEqual(["partner"], [member["member_id"] for member in members])
        self.assertEqual(["香菜"], members[0]["dislikes"]["ingredients"])

    def test_read_filters_feedback_by_dish_and_skips_malformed_jsonl(self):
        memory = load_memory_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            memory.init_profile(root)
            feedback_path = root / "feedback.jsonl"
            feedback_path.write_text(
                "\n".join(
                    [
                        "{not-json",
                        json.dumps(
                            {
                                "entry_id": "other",
                                "recipe_id": "qingjiao-rousi",
                                "suggested_adjustment": {"salt_multiplier": 0.8},
                                "status": "pending-confirmation",
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "entry_id": "tomato",
                                "recipe_id": "tomato-egg",
                                "suggested_adjustment": {
                                    "salt_multiplier": 0.85,
                                    "note": "下次先少放盐。",
                                },
                                "status": "pending-confirmation",
                                "memory_candidate": {"confidence": 0.6},
                            },
                            ensure_ascii=False,
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = memory.read_memory(root, dish="tomato-egg", diners=["self"])

        feedback = result["applied"]["recipe_feedback"]
        self.assertEqual(1, len(feedback))
        self.assertEqual("tomato-egg", feedback[0]["recipe_id"])
        self.assertEqual("suggestion", feedback[0]["label"])
        self.assertIn("Skipped malformed JSONL line 1", result["notices"])

    def test_add_feedback_creates_pending_candidate_and_confirm_promotes_to_profile(self):
        memory = load_memory_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            memory.init_profile(root)

            feedback = memory.add_feedback(
                root,
                recipe_id="tomato-egg",
                recipe_name="番茄炒蛋",
                issue="too_salty",
                result="edible",
                observation="成品偏咸。",
                eaten_by=["self"],
            )
            candidate_id = feedback["memory_candidate"]["candidate_id"]
            memory.confirm_candidate(root, candidate_id)
            profile = memory.read_profile(root)

        self.assertEqual("pending-confirmation", feedback["status"])
        self.assertEqual(
            0.85,
            profile["recipe_preferences"]["tomato-egg"]["salt_multiplier"],
        )

    def test_adjustment_for_issue_supports_flow_taxonomy(self):
        memory = load_memory_module()

        watery = memory.adjustment_for_issue("too_watery")
        burnt = memory.adjustment_for_issue("burnt")
        undercooked = memory.adjustment_for_issue("undercooked")
        separated = memory.adjustment_for_issue("separated")

        self.assertIn("batch_size_multiplier", watery)
        self.assertIn("heat_level_note", burnt)
        self.assertIn("cook_time_multiplier", undercooked)
        self.assertIn("heat_level_note", separated)

    def test_add_feedback_uses_taxonomy_adjustment_key_for_watery_issue(self):
        memory = load_memory_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            memory.init_profile(root)

            feedback = memory.add_feedback(
                root,
                recipe_id="stir-fried-greens",
                recipe_name="清炒小青菜",
                issue="too_watery",
                result="edible",
                observation="锅底很多水。",
                eaten_by=["self"],
            )

        candidate = feedback["memory_candidate"]
        self.assertEqual(
            "recipe_preferences.stir-fried-greens.batch_size_multiplier",
            candidate["key"],
        )
        self.assertEqual(0.8, candidate["value"])

    def test_reject_candidate_does_not_mutate_profile(self):
        memory = load_memory_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            memory.init_profile(root)
            feedback = memory.add_feedback(
                root,
                recipe_id="tomato-egg",
                recipe_name="番茄炒蛋",
                issue="too_salty",
                result="edible",
                observation="成品偏咸。",
                eaten_by=["self"],
            )
            candidate_id = feedback["memory_candidate"]["candidate_id"]

            memory.reject_candidate(root, candidate_id)
            profile = memory.read_profile(root)

        self.assertEqual({}, profile["recipe_preferences"])

    def test_sensitive_profile_update_requires_explicit_confirmation(self):
        memory = load_memory_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            memory.init_profile(root)

            with self.assertRaises(memory.MemoryDataError):
                memory.update_profile_value(
                    root,
                    "household_members.0.sensitive_constraints.allergies.0",
                    "花生",
                    confirm_sensitive=False,
                )

            memory.update_profile_value(
                root,
                "household_members.0.sensitive_constraints.allergies.0",
                "花生",
                confirm_sensitive=True,
            )
            profile = memory.read_profile(root)

        self.assertEqual(
            "花生",
            profile["household_members"][0]["sensitive_constraints"]["allergies"][0],
        )

    def test_malformed_profile_raises_clear_error(self):
        memory = load_memory_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "profile.yaml").write_text("defaults\n", encoding="utf-8")

            with self.assertRaisesRegex(memory.MemoryDataError, "Malformed profile.yaml"):
                memory.read_memory(root, dish="tomato-egg", diners=["self"])

    def test_profile_update_replaces_file_without_leaving_temp_file(self):
        memory = load_memory_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            memory.init_profile(root)

            memory.update_profile_value(root, "defaults.servings", 4)
            profile = memory.read_profile(root)

            temp_files = list(root.glob("*.tmp"))

        self.assertEqual(4, profile["defaults"]["servings"])
        self.assertEqual([], temp_files)

    def test_cli_read_outputs_json(self):
        memory = load_memory_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            memory.init_profile(root)

            with mock.patch.dict(os.environ, {"ROOKIE_COOKING_HOME": str(root)}):
                with mock.patch("sys.stdout") as stdout:
                    exit_code = memory.main(["read", "--dish", "tomato-egg", "--diners", "self"])

        self.assertEqual(0, exit_code)
        output = "".join(call.args[0] for call in stdout.write.call_args_list)
        self.assertTrue(json.loads(output)["memory_found"])


if __name__ == "__main__":
    unittest.main()
