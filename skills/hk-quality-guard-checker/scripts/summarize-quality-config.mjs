#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

function readInput(inputPath) {
  if (inputPath) return fs.readFileSync(inputPath, "utf8");
  return fs.readFileSync(0, "utf8");
}

function label(value) {
  if (value === null || value === undefined || value === false || value === "") return "not detected";
  if (value === true) return "detected";
  if (Array.isArray(value)) return value.length ? value.join(", ") : "none";
  return String(value);
}

export function renderSummary(report) {
  const quality = report.quality ?? {};
  const hooks = report.hooks ?? {};
  const ci = report.ci ?? {};
  const rows = [
    ["Ecosystems", report.ecosystems],
    ["Manifests", report.manifests?.map(({ file }) => file)],
    ["Workspace manifests", report.workspaceManifests?.map(({ file }) => file)],
    ["Quality configs", report.qualityConfigs],
    ["Package manager", report.packageManager?.selected],
    ["Frameworks", report.frameworks],
    ["TypeScript", report.typescript],
    ["Monorepo", report.monorepo],
    ["Monorepo status", report.monorepoStatus],
    ["Lint", quality.lint],
    ["Format", quality.format],
    ["Style lint", quality.stylelint],
    ["Type check script", quality.typecheck],
    ["Unit test", quality.unitTest],
    ["E2E", quality.e2e],
    ["Accessibility", quality.accessibility],
    ["Secret scan", quality.secretScan],
    ["Commit lint", quality.commitlint],
    ["Build script", quality.build],
  ];

  const lines = [
    "# Repository Quality Summary",
    "",
    "## Detected Configuration",
    "",
    "| Area | Result |",
    "|---|---|",
    ...rows.map(([name, value]) => `| ${name} | ${label(value)} |`),
    "",
    "## Hook Management",
    "",
    `- Husky: ${label(hooks.husky)}`,
    `- Other managers: ${label(hooks.otherManagers)}`,
    `- Mixed configuration: ${label(hooks.mixed)}`,
    "",
    "## CI",
    "",
    `- Providers: ${label(ci.providers)}`,
    `- Workflows: ${label(ci.workflows)}`,
    `- Workflow present: ${label(ci.workflowPresent)}`,
    `- Merge enforcement: ${label(ci.mergeEnforcement?.status)}`,
    `- Enforcement evidence: ${label(ci.mergeEnforcement?.reason)}`,
    "",
    "This summary is heuristic. Inspect source configuration and run existing commands before proposing changes.",
  ];
  return `${lines.join("\n")}\n`;
}

function isMainModule() {
  return process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href;
}

if (isMainModule()) {
  try {
    process.stdout.write(renderSummary(JSON.parse(readInput(process.argv[2]))));
  } catch (error) {
    process.stderr.write(`summarize-quality-config: ${error.message}\n`);
    process.exitCode = 1;
  }
}
