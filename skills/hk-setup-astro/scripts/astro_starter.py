#!/usr/bin/env python3
"""Audit and verify the Astro starter managed by this skill."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REQUIRED_PACKAGES = (
    "astro",
    "@tailwindcss/vite",
    "tailwindcss",
    "daisyui",
    "@astrojs/partytown",
    "@astrojs/sitemap",
)


@dataclass
class Check:
    name: str
    status: str
    detail: str


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return ""


def package_versions(root: Path) -> tuple[dict[str, str], list[str]]:
    path = root / "package.json"
    if not path.is_file():
        return {}, ["package.json is missing"]
    try:
        package = json.loads(read(path))
    except json.JSONDecodeError as error:
        return {}, [f"package.json is invalid JSON: {error}"]
    dependencies = {
        **package.get("dependencies", {}),
        **package.get("devDependencies", {}),
    }
    missing = [name for name in REQUIRED_PACKAGES if name not in dependencies]
    return {name: dependencies[name] for name in REQUIRED_PACKAGES if name in dependencies}, missing


def add(checks: list[Check], name: str, passed: bool, detail: str, *, inconsistent: bool = False) -> None:
    status = "pass" if passed else ("inconsistent" if inconsistent else "missing")
    checks.append(Check(name, status, detail))


def audit(root: Path) -> tuple[list[Check], dict[str, str]]:
    checks: list[Check] = []
    versions, missing = package_versions(root)
    add(checks, "dependencies", not missing, "all required packages declared" if not missing else ", ".join(missing))

    add(
        checks,
        "pnpm",
        (root / "pnpm-lock.yaml").is_file(),
        "pnpm-lock.yaml present" if (root / "pnpm-lock.yaml").is_file() else "pnpm-lock.yaml is missing",
        inconsistent=(root / "package-lock.json").exists() or (root / "yarn.lock").exists(),
    )
    git_result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
        check=False,
    )
    add(checks, "Git work tree", git_result.returncode == 0, "Git work tree detected" if git_result.returncode == 0 else "not inside a Git work tree")

    config = read(root / "astro.config.mjs")
    config_requirements = {
        "Tailwind Vite import": '@tailwindcss/vite',
        "Tailwind Vite plugin": "tailwindcss()",
        "Partytown integration": "partytown()",
        "Sitemap integration": "sitemap()",
    }
    absent = [label for label, token in config_requirements.items() if token not in config]
    add(checks, "astro integrations", not absent, "all integrations registered" if not absent else ", ".join(absent))
    site_ok = "SITE_URL" in config and "localhost" in config
    env_example = read(root / ".env.example")
    add(
        checks,
        "site URL",
        site_ok and "SITE_URL=" in env_example,
        "SITE_URL with local fallback and .env.example present"
        if site_ok and "SITE_URL=" in env_example
        else "expected SITE_URL, local fallback, and .env.example",
    )

    tsconfig = read(root / "tsconfig.json")
    ts_tokens = ('astro/tsconfigs/strict', '"baseUrl"', '"."', '"noUnusedLocals"', '"noUnusedParameters"', '"@/*"', '"./src/*"')
    missing_ts = [token for token in ts_tokens if token not in tsconfig]
    add(checks, "TypeScript", not missing_ts, "strict options and alias present" if not missing_ts else ", ".join(missing_ts))

    styles = list((root / "src").rglob("*.css")) if (root / "src").is_dir() else []
    tailwind_styles = [path for path in styles if '@import "tailwindcss"' in read(path)]
    daisy_styles = [path for path in tailwind_styles if '@plugin "daisyui"' in read(path)]
    add(checks, "Tailwind and daisyUI CSS", bool(daisy_styles), ", ".join(str(path.relative_to(root)) for path in daisy_styles) or "directives not found")

    astro_files = list((root / "src").rglob("*.astro")) if (root / "src").is_dir() else []
    imported = []
    for style in daisy_styles:
        if any(style.name in read(path) for path in astro_files):
            imported.append(style)
    add(checks, "stylesheet reachability", bool(imported), "stylesheet imported by an Astro file" if imported else "no matching Astro import found")

    old_tailwind = any((root / name).exists() for name in ("tailwind.config.js", "tailwind.config.cjs", "tailwind.config.mjs"))
    add(checks, "Tailwind 4 configuration", not old_tailwind, "no obsolete Tailwind config found" if not old_tailwind else "legacy tailwind.config file present", inconsistent=old_tailwind)

    calendar_excluded = any(re.search(r"exclude\s*:\s*calendar", read(path)) for path in daisy_styles)
    calendar_candidates = [root / "package.json"]
    if (root / "src").is_dir():
        calendar_candidates.extend(path for path in (root / "src").rglob("*") if path.is_file())
    calendar_used = any(re.search(r"\b(cally|react-day-picker|pikaday|vanilla-calendar)\b", read(path), re.I) for path in calendar_candidates)
    add(
        checks,
        "Calendar exclusion",
        not (calendar_excluded and calendar_used),
        "consistent with detected Calendar usage" if not (calendar_excluded and calendar_used) else "Calendar is excluded but a supported Calendar library appears to be used",
        inconsistent=calendar_excluded and calendar_used,
    )
    return checks, versions


def print_audit(checks: list[Check], versions: dict[str, str]) -> int:
    for check in checks:
        print(f"{check.status.upper():12} {check.name}: {check.detail}")
    print("VERSIONS     " + (", ".join(f"{name}={version}" for name, version in versions.items()) or "unavailable"))
    return 0 if all(check.status == "pass" for check in checks) else 1


def verify(root: Path, site_url: str, run_build: bool) -> int:
    if run_build:
        environment = os.environ.copy()
        environment["SITE_URL"] = site_url
        result = subprocess.run(["pnpm", "build"], cwd=root, env=environment, check=False)
        if result.returncode:
            return result.returncode

    dist = root / "dist"
    index_files = list(dist.rglob("sitemap-index.xml"))
    numbered_maps = list(dist.rglob("sitemap-*.xml"))
    numbered_maps = [path for path in numbered_maps if path.name != "sitemap-index.xml"]
    html_files = list(dist.rglob("*.html"))
    html = "\n".join(read(path) for path in html_files)
    partytown_assets = list(dist.rglob("~partytown"))

    checks = [
        Check("sitemap index", "pass" if index_files else "missing", "sitemap-index.xml"),
        Check("numbered sitemap", "pass" if numbered_maps else "missing", "sitemap-N.xml"),
        Check("sitemap origin", "pass" if index_files and numbered_maps and all(site_url in read(path) for path in index_files + numbered_maps) else "inconsistent", site_url),
        Check("Partytown bootstrap", "pass" if "partytown" in html.lower() else "missing", "generated HTML"),
        Check("Partytown assets", "pass" if partytown_assets else "missing", "dist/**/~partytown"),
    ]
    for check in checks:
        print(f"{check.status.upper():12} {check.name}: {check.detail}")
    return 0 if all(check.status == "pass" for check in checks) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("audit", "verify"):
        child = subparsers.add_parser(command)
        child.add_argument("project", type=Path, help="Astro project directory")
        if command == "verify":
            child.add_argument("--site-url", default="https://example.test")
            child.add_argument("--run-build", action="store_true")
    args = parser.parse_args()
    root = args.project.expanduser().resolve()
    if args.command == "audit":
        return print_audit(*audit(root))
    return verify(root, args.site_url.rstrip("/"), args.run_build)


if __name__ == "__main__":
    sys.exit(main())
