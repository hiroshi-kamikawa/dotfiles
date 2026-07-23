#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function hasAny(record, names) {
  return names.some((name) => Object.hasOwn(record, name));
}

function detectNamedTool(dependencies, candidates) {
  for (const [name, packages] of candidates) {
    if (hasAny(dependencies, packages)) return name;
  }
  return null;
}

export function inspectPackageJson(file) {
  const packageJson = readJson(file);
  const dependencies = {
    ...(packageJson.dependencies ?? {}),
    ...(packageJson.devDependencies ?? {}),
    ...(packageJson.peerDependencies ?? {}),
    ...(packageJson.optionalDependencies ?? {}),
  };
  const scripts = packageJson.scripts ?? {};

  const frameworks = [];
  const frameworkPackages = [
    ["next", ["next"]],
    ["react", ["react"]],
    ["vue", ["vue"]],
    ["nuxt", ["nuxt"]],
    ["svelte", ["svelte", "@sveltejs/kit"]],
    ["astro", ["astro"]],
    ["angular", ["@angular/core"]],
    ["remix", ["@remix-run/react"]],
    ["vite", ["vite"]],
  ];
  for (const [name, packages] of frameworkPackages) {
    if (hasAny(dependencies, packages)) frameworks.push(name);
  }

  const lint = detectNamedTool(dependencies, [
    ["biome", ["@biomejs/biome"]],
    ["eslint", ["eslint"]],
    ["oxlint", ["oxlint"]],
  ]);
  const format = detectNamedTool(dependencies, [
    ["prettier", ["prettier"]],
    ["biome", ["@biomejs/biome"]],
    ["dprint", ["dprint"]],
  ]);
  const unitTest = detectNamedTool(dependencies, [
    ["vitest", ["vitest"]],
    ["jest", ["jest"]],
    ["node:test", []],
  ]) ?? (/\bnode\s+--test\b/.test(scripts.test ?? "") ? "node:test" : null);
  const e2e = detectNamedTool(dependencies, [
    ["playwright", ["@playwright/test", "playwright"]],
    ["cypress", ["cypress"]],
  ]);
  const accessibility = detectNamedTool(dependencies, [
    ["axe", ["axe-core", "@axe-core/playwright", "jest-axe", "vitest-axe"]],
    ["eslint-plugin-jsx-a11y", ["eslint-plugin-jsx-a11y"]],
  ]);
  const secretScan = detectNamedTool(dependencies, [
    ["secretlint", ["secretlint", "@secretlint/secretlint-rule-preset-recommend"]],
  ]) ?? (Object.values(scripts).some((command) => /\bgitleaks\b/.test(command)) ? "gitleaks" : null);

  return {
    name: packageJson.name ?? null,
    private: packageJson.private ?? null,
    packageManager: packageJson.packageManager ?? null,
    engines: packageJson.engines ?? {},
    workspaces: packageJson.workspaces ?? null,
    frameworks,
    typescript: hasAny(dependencies, ["typescript"]) || Object.values(scripts).some((command) => /\btsc\b/.test(command)),
    scripts,
    hooks: {
      huskyDependency: hasAny(dependencies, ["husky"]),
      lintStagedDependency: hasAny(dependencies, ["lint-staged"]),
      otherManagerDependencies: [
        ...(hasAny(dependencies, ["lefthook"]) ? ["lefthook"] : []),
        ...(hasAny(dependencies, ["simple-git-hooks"]) ? ["simple-git-hooks"] : []),
      ],
      prepare: scripts.prepare ?? null,
    },
    quality: {
      lint,
      format,
      stylelint: hasAny(dependencies, ["stylelint"]) ? "stylelint" : null,
      typecheck: Object.hasOwn(scripts, "typecheck") ? "script" : null,
      unitTest,
      e2e,
      accessibility,
      secretScan,
      commitlint: hasAny(dependencies, ["@commitlint/cli"]) ? "commitlint" : null,
      build: Object.hasOwn(scripts, "build") ? "script" : null,
    },
  };
}

function isMainModule() {
  return process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href;
}

if (isMainModule()) {
  const target = path.resolve(process.argv[2] ?? "package.json");
  try {
    process.stdout.write(`${JSON.stringify(inspectPackageJson(target), null, 2)}\n`);
  } catch (error) {
    process.stderr.write(`inspect-package-json: ${error.message}\n`);
    process.exitCode = 1;
  }
}
