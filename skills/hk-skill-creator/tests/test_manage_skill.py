from __future__ import annotations

import argparse
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).parents[1] / "scripts" / "manage_skill.py"
SPEC = importlib.util.spec_from_file_location("manage_skill", SCRIPT)
assert SPEC and SPEC.loader
manage_skill = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manage_skill)


class ManageSkillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.home = Path(self.temporary_directory.name)
        (self.home / "dotfiles" / "skills").mkdir(parents=True)
        self.home_patch = patch.dict(os.environ, {"HOME": str(self.home)})
        self.home_patch.start()

    def tearDown(self) -> None:
        self.home_patch.stop()
        self.temporary_directory.cleanup()

    def create(self, name: str = "demo") -> Path:
        manage_skill.create_skill(
            argparse.Namespace(
                name=name,
                description="Create demo artifacts. Use when a user requests a demo skill.",
                title=None,
                short_description=None,
                dry_run=False,
            )
        )
        destination = self.home / "dotfiles" / "skills" / "hk-demo"
        return destination

    def validate(self, name: str = "demo") -> None:
        manage_skill.validate_skill(argparse.Namespace(name=name))

    def test_normalize_name_adds_prefix_exactly_once(self) -> None:
        self.assertEqual(manage_skill.normalize_name("hk-hk-Demo"), "hk-demo")
        self.assertEqual(manage_skill.normalize_name("Demo"), "hk-demo")

    def test_created_skill_passes_after_placeholder_is_replaced(self) -> None:
        destination = self.create()
        self.assertTrue((destination / "README.md").is_file())
        skill_md = destination / "SKILL.md"
        skill_md.write_text(skill_md.read_text().replace("[TBD: Define the skill workflow in concise, imperative English.]", "Create the requested demo."))
        self.validate()

    def test_rejects_duplicate_frontmatter_key(self) -> None:
        destination = self.create()
        skill_md = destination / "SKILL.md"
        skill_md.write_text(skill_md.read_text().replace("name: hk-demo", "name: hk-demo\nname: hk-demo"))
        with self.assertRaisesRegex(manage_skill.SkillError, "duplicate key"):
            self.validate()

    def test_rejects_invalid_openai_metadata(self) -> None:
        destination = self.create()
        (destination / "agents" / "openai.yaml").write_text("interface:\n  display_name: Demo\n")
        with self.assertRaisesRegex(manage_skill.SkillError, "is missing"):
            self.validate()

    def test_rejects_default_prompt_without_skill_name(self) -> None:
        destination = self.create()
        metadata = destination / "agents" / "openai.yaml"
        metadata.write_text(metadata.read_text().replace("$hk-demo", "$other-skill"))
        with self.assertRaisesRegex(manage_skill.SkillError, "must mention"):
            self.validate()

    def test_rejects_broken_local_link_and_prohibited_resource(self) -> None:
        destination = self.create()
        skill_md = destination / "SKILL.md"
        skill_md.write_text(skill_md.read_text().replace("[TBD: Define the skill workflow in concise, imperative English.]", "Read [the reference](references/missing.md)."))
        (destination / "CHANGELOG.md").write_text("Documentation")
        with self.assertRaises(manage_skill.SkillError) as context:
            self.validate()
        self.assertIn("prohibited documentation resource", str(context.exception))
        self.assertIn("broken local link", str(context.exception))

    def test_rejects_missing_readme(self) -> None:
        destination = self.create()
        (destination / "README.md").unlink()
        with self.assertRaisesRegex(manage_skill.SkillError, "missing .*README.md"):
            self.validate()

    def test_utf8_english_is_allowed(self) -> None:
        destination = self.create()
        skill_md = destination / "SKILL.md"
        skill_md.write_text(skill_md.read_text().replace("[TBD: Define the skill workflow in concise, imperative English.]", "Create a café guide."), encoding="utf-8")
        self.validate()

    def test_rejects_japanese_agent_artifact(self) -> None:
        destination = self.create()
        skill_md = destination / "SKILL.md"
        skill_md.write_text(
            skill_md.read_text().replace(
                "[TBD: Define the skill workflow in concise, imperative English.]",
                "依頼されたデモを作成します。",
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(manage_skill.SkillError, "agent-facing text must be written in English"):
            self.validate()

    def test_rejects_readme_without_substantive_japanese(self) -> None:
        destination = self.create()
        (destination / "README.md").write_text("# Demo\n\nEnglish documentation only.\n", encoding="utf-8")
        with self.assertRaisesRegex(manage_skill.SkillError, "missing required section"):
            self.validate()

    def test_accepts_trigger_description_without_literal_use_when(self) -> None:
        destination = self.create()
        skill_md = destination / "SKILL.md"
        content = skill_md.read_text().replace(
            "Create demo artifacts. Use when a user requests a demo skill.",
            "Create demo artifacts whenever a user requests a reusable demonstration skill.",
        ).replace(
            "[TBD: Define the skill workflow in concise, imperative English.]",
            "Create the requested demo.",
        )
        skill_md.write_text(content, encoding="utf-8")
        self.validate()

    def test_rejects_short_openai_description(self) -> None:
        destination = self.create()
        metadata = destination / "agents" / "openai.yaml"
        metadata.write_text(
            metadata.read_text().replace(
                "Use HK Demo across AI coding agents",
                "Too short",
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(manage_skill.SkillError, "25-64 characters"):
            self.validate()

    def test_rejects_thin_required_readme_section(self) -> None:
        destination = self.create()
        readme = destination / "README.md"
        readme.write_text(
            readme.read_text().replace(
                "このスキルの目的と、対応する作業を説明します。",
                "説明。",
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(manage_skill.SkillError, "section lacks substantive Japanese content"):
            self.validate()


if __name__ == "__main__":
    unittest.main()
