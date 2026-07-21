#!/usr/bin/env python3
"""Create and validate portable skills under $HOME/dotfiles/skills."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


NAME_PATTERN = re.compile(r"^hk-[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_PATTERN = re.compile(r"\A---\n(.*?)\n---(?:\n|\Z)", re.DOTALL)
UNFINISHED_PATTERN = re.compile(
    r"\b(?:" + "TO" + "DO|" + "TB" + "D)\b", re.IGNORECASE
)
ABSOLUTE_USER_PATH_PATTERN = re.compile(r"/(?:Users|home)/[^/\s]+/")
FORBIDDEN_DESTINATION_PATTERN = re.compile(
    r"(?:\$CODEX_HOME/" + "skills|~/\.claude/" + "skills|\.codex/" + "skills|\.claude/" + "skills)"
)
MARKDOWN_LINK_PATTERN = re.compile(r"!?\[[^]]*\]\(([^)]+)\)")
FORBIDDEN_RESOURCE_PATTERN = re.compile(
    r"^(?:change(?:log|s)|install(?:ation)?(?:-guide)?)\b", re.IGNORECASE
)
TEXT_SUFFIXES = {".md", ".py", ".sh", ".txt", ".yaml", ".yml", ".json", ".toml"}
JAPANESE_PATTERN = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]")
README_SECTIONS = (
    "\u3053\u306e\u30b9\u30ad\u30eb\u306b\u3064\u3044\u3066",
    "\u52b9\u679c\u7684\u306a\u4f7f\u3044\u65b9",
    "\u5b9f\u88c5\u306e\u80cc\u666f\u3068\u6c7a\u5b9a",
)
MIN_README_SECTION_JAPANESE_CHARS = 20
MIN_SHORT_DESCRIPTION_LENGTH = 25
MAX_SHORT_DESCRIPTION_LENGTH = 64


class SkillError(ValueError):
    """Report an invalid skill request or artifact."""


def skills_root() -> Path:
    home = Path.home()
    dotfiles = home / "dotfiles"
    if not dotfiles.is_dir():
        raise SkillError("$HOME/dotfiles does not exist or is not a directory")
    return dotfiles / "skills"


def normalize_name(value: str) -> str:
    name = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    while name.startswith("hk-"):
        name = name[3:]
    name = f"hk-{name}"
    if not NAME_PATTERN.fullmatch(name):
        raise SkillError("the skill name must contain letters or digits")
    if len(name) > 64:
        raise SkillError("the complete skill name must not exceed 64 characters")
    return name


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def create_skill(args: argparse.Namespace) -> None:
    name = normalize_name(args.name)
    title = args.title or " ".join(part.upper() if part == "hk" else part.title() for part in name.split("-"))
    root = skills_root()
    destination = root / name
    if destination.exists():
        raise SkillError(f"skill already exists: $HOME/dotfiles/skills/{name}")

    skill_md = (
        "---\n"
        f"name: {name}\n"
        f"description: {yaml_quote(args.description)}\n"
        "---\n\n"
        f"# {title}\n\n"
        "[" + "TB" + "D: Define the skill workflow in concise, imperative English.]\n"
    )
    short_description = args.short_description or f"Use {title} across AI coding agents"
    validate_short_description(short_description)
    openai_yaml = (
        "interface:\n"
        f"  display_name: {yaml_quote(title)}\n"
        f"  short_description: {yaml_quote(short_description)}\n"
        f"  default_prompt: {yaml_quote(f'Use ${name} to complete this task.')}\n"
    )
    readme = (
        f"# {title}\n\n"
        "## \u3053\u306e\u30b9\u30ad\u30eb\u306b\u3064\u3044\u3066\n\n"
        "\u3053\u306e\u30b9\u30ad\u30eb\u306e\u76ee\u7684\u3068\u3001\u5bfe\u5fdc\u3059\u308b\u4f5c\u696d\u3092\u8aac\u660e\u3057\u307e\u3059\u3002\n\n"
        "## \u52b9\u679c\u7684\u306a\u4f7f\u3044\u65b9\n\n"
        "\u3053\u306e\u30b9\u30ad\u30eb\u3092\u5229\u7528\u3059\u308b\u72b6\u6cc1\u3068\u3001\u4f9d\u983c\u6642\u306b\u4f1d\u3048\u308b\u3068\u3088\u3044\u60c5\u5831\u3092\u8aac\u660e\u3057\u307e\u3059\u3002\n\n"
        "## \u5b9f\u88c5\u306e\u80cc\u666f\u3068\u6c7a\u5b9a\n\n"
        "\u63a1\u7528\u3057\u305f\u30ef\u30fc\u30af\u30d5\u30ed\u30fc\u3001\u30ea\u30bd\u30fc\u30b9\u69cb\u6210\u3001\u91cd\u8981\u306a\u8a2d\u8a08\u5224\u65ad\u3092\u8aac\u660e\u3057\u307e\u3059\u3002\n"
    )

    if args.dry_run:
        print(f"Would create $HOME/dotfiles/skills/{name}")
        return

    (destination / "agents").mkdir(parents=True)
    (destination / "SKILL.md").write_text(skill_md, encoding="utf-8")
    (destination / "agents" / "openai.yaml").write_text(openai_yaml, encoding="utf-8")
    (destination / "README.md").write_text(readme, encoding="utf-8")
    print(f"Created $HOME/dotfiles/skills/{name}")


def parse_frontmatter(content: str) -> dict[str, str]:
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        raise SkillError("SKILL.md has invalid frontmatter delimiters")
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if not separator or not key.strip() or not value.strip():
            raise SkillError("SKILL.md frontmatter must contain simple key-value pairs")
        key = key.strip()
        if key in values:
            raise SkillError(f"SKILL.md frontmatter contains duplicate key: {key}")
        values[key] = parse_yaml_scalar(value.strip(), f"frontmatter {key}")
    if set(values) != {"name", "description"}:
        raise SkillError("SKILL.md frontmatter must contain only name and description")
    return values


def parse_yaml_scalar(value: str, label: str) -> str:
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as error:
            raise SkillError(f"{label} contains an invalid quoted value") from error
        if not isinstance(parsed, str):
            raise SkillError(f"{label} must be a string")
        return parsed
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise SkillError(f"{label} contains an invalid quoted value")
        return value[1:-1].replace("''", "'")
    if value[0] in "[{&*!|>" or " #" in value:
        raise SkillError(f"{label} must be a simple string")
    return value


def parse_openai_yaml(content: str) -> dict[str, str]:
    lines = [line for line in content.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if not lines or lines[0] != "interface:":
        raise SkillError("agents/openai.yaml must start with an interface mapping")
    values: dict[str, str] = {}
    for line in lines[1:]:
        if not line.startswith("  ") or line.startswith("   ") or "\t" in line:
            raise SkillError("agents/openai.yaml has unsupported or invalid structure")
        key, separator, value = line.strip().partition(":")
        if not separator or not key or not value.strip():
            raise SkillError("agents/openai.yaml must contain simple key-value pairs")
        if key in values:
            raise SkillError(f"agents/openai.yaml contains duplicate key: {key}")
        values[key] = parse_yaml_scalar(value.strip(), f"agents/openai.yaml {key}")
    required = {"display_name", "short_description", "default_prompt"}
    missing = required - values.keys()
    if missing:
        raise SkillError(f"agents/openai.yaml is missing: {', '.join(sorted(missing))}")
    validate_short_description(values["short_description"])
    return values


def validate_short_description(value: str) -> None:
    length = len(value)
    if not MIN_SHORT_DESCRIPTION_LENGTH <= length <= MAX_SHORT_DESCRIPTION_LENGTH:
        raise SkillError(
            "agents/openai.yaml short_description must contain "
            f"{MIN_SHORT_DESCRIPTION_LENGTH}-{MAX_SHORT_DESCRIPTION_LENGTH} characters"
        )


def validate_readme(readme: str) -> list[str]:
    errors: list[str] = []
    for index, heading in enumerate(README_SECTIONS):
        marker = f"## {heading}"
        start = readme.find(marker)
        if start < 0:
            errors.append(f"README.md: missing required section: {heading}")
            continue
        body_start = start + len(marker)
        following = [readme.find(f"## {item}", body_start) for item in README_SECTIONS[index + 1 :]]
        following = [position for position in following if position >= 0]
        body_end = min(following) if following else len(readme)
        body = readme[body_start:body_end]
        if len(JAPANESE_PATTERN.findall(body)) < MIN_README_SECTION_JAPANESE_CHARS:
            errors.append(f"README.md: section lacks substantive Japanese content: {heading}")
    return errors


def validate_local_links(content: str, source: Path, destination: Path) -> list[str]:
    errors: list[str] = []
    for target in MARKDOWN_LINK_PATTERN.findall(content):
        target = target.strip().strip("<>").split("#", 1)[0]
        if not target or "://" in target or target.startswith(("#", "$", "/")):
            continue
        resolved = (source.parent / target).resolve()
        try:
            resolved.relative_to(destination.resolve())
        except ValueError:
            errors.append(f"{source.relative_to(destination)}: link escapes the skill directory: {target}")
            continue
        if not resolved.exists():
            errors.append(f"{source.relative_to(destination)}: broken local link: {target}")
    return errors


def validate_skill(args: argparse.Namespace) -> None:
    name = normalize_name(args.name)
    destination = skills_root() / name
    skill_md_path = destination / "SKILL.md"
    if not skill_md_path.is_file():
        raise SkillError(f"missing $HOME/dotfiles/skills/{name}/SKILL.md")
    readme_path = destination / "README.md"
    if not readme_path.is_file():
        raise SkillError(f"missing $HOME/dotfiles/skills/{name}/README.md")

    content = skill_md_path.read_text(encoding="utf-8")
    metadata = parse_frontmatter(content)
    if metadata["name"] != name or destination.name != name:
        raise SkillError("folder name and frontmatter name must match")
    if not NAME_PATTERN.fullmatch(name) or len(name) > 64:
        raise SkillError("frontmatter name is invalid")
    if len(metadata["description"]) > 1024:
        raise SkillError("description must not exceed 1024 characters")
    description = metadata["description"].strip()
    if len(description) < 40 or len(description.split()) < 7:
        raise SkillError("description must provide a substantive capability and trigger summary")
    body = FRONTMATTER_PATTERN.sub("", content, count=1).strip()
    if not body:
        raise SkillError("SKILL.md body must not be empty")
    readme = readme_path.read_text(encoding="utf-8").strip()
    if not readme:
        raise SkillError("README.md must not be empty")

    openai_yaml_path = destination / "agents" / "openai.yaml"
    if openai_yaml_path.exists():
        openai_metadata = parse_openai_yaml(openai_yaml_path.read_text(encoding="utf-8"))
        if f"${name}" not in openai_metadata["default_prompt"]:
            raise SkillError(f"agents/openai.yaml default_prompt must mention ${name}")

    errors: list[str] = validate_readme(readme)
    for path in sorted(destination.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(destination)
        if FORBIDDEN_RESOURCE_PATTERN.match(path.name):
            errors.append(f"{relative}: prohibited documentation resource")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"{relative}: is not valid UTF-8")
            continue
        if "tests" not in relative.parts and UNFINISHED_PATTERN.search(text):
            errors.append(f"{relative}: contains an unfinished placeholder")
        if ABSOLUTE_USER_PATH_PATTERN.search(text):
            errors.append(f"{relative}: contains a machine-specific user path")
        if path != skill_md_path and FORBIDDEN_DESTINATION_PATTERN.search(text):
            errors.append(f"{relative}: contains a prohibited vendor-specific skills path")
        if path != readme_path and "tests" not in relative.parts and JAPANESE_PATTERN.search(text):
            errors.append(f"{relative}: agent-facing text must be written in English")
        if path.suffix.lower() == ".md":
            errors.extend(validate_local_links(text, path, destination))

    if errors:
        raise SkillError("\n".join(errors))
    print(f"Valid: $HOME/dotfiles/skills/{name}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    normalize = subparsers.add_parser("normalize-name", help="normalize and prefix a skill name")
    normalize.add_argument("name")

    create = subparsers.add_parser("create", help="create a minimal skill scaffold")
    create.add_argument("name")
    create.add_argument("--description", required=True)
    create.add_argument("--title")
    create.add_argument("--short-description")
    create.add_argument("--dry-run", action="store_true")
    create.set_defaults(handler=create_skill)

    validate = subparsers.add_parser("validate", help="validate a skill in the fixed skills root")
    validate.add_argument("name")
    validate.set_defaults(handler=validate_skill)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "normalize-name":
            print(normalize_name(args.name))
        else:
            args.handler(args)
    except SkillError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    sys.exit(main())
