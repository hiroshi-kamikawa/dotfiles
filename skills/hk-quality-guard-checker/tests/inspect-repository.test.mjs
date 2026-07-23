import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { inspectRepository } from "../scripts/inspect-repository.mjs";
import { renderSummary } from "../scripts/summarize-quality-config.mjs";

function createFixture(t, files) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "quality-guard-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  for (const [relative, contents] of Object.entries(files)) {
    const target = path.join(root, relative);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, contents);
  }
  return root;
}

test("detects multiple ecosystems and nested workspace manifests", (t) => {
  const root = createFixture(t, {
    "pyproject.toml": "[project]\nname = \"service\"\n",
    "uv.lock": "",
    "ruff.toml": "line-length = 100\n",
    "packages/web/package.json": JSON.stringify({
      name: "web",
      packageManager: "npm@11.0.0",
      devDependencies: { eslint: "^9.0.0" },
    }),
    "packages/web/package-lock.json": "{}\n",
    "packages/web/eslint.config.mjs": "export default [];\n",
  });

  const report = inspectRepository(root);

  assert.deepEqual(report.ecosystems, ["node", "python"]);
  assert.deepEqual(
    report.manifests.map(({ file }) => file),
    ["packages/web/package.json", "pyproject.toml"],
  );
  assert.deepEqual(report.workspaceManifests, [
    { file: "packages/web/package.json", ecosystem: "node" },
  ]);
  assert.equal(report.monorepo, false);
  assert.equal(report.monorepoStatus, "candidate");
  assert.ok(report.monorepoSignals.includes("nested manifests"));
  assert.deepEqual(report.dependencyManagers.python.managers, ["uv"]);
  assert.equal(report.quality.lint, "ruff");
  assert.ok(report.qualityConfigs.includes("packages/web/eslint.config.mjs"));
  assert.equal(report.workspaceProjects[0].declaredManager, "npm");
  assert.deepEqual(report.workspaceProjects[0].dependencyManagers, ["npm"]);
  assert.equal(report.workspaceProjects[0].quality.lint, "eslint");
});

test("confirms a monorepo only when an explicit workspace signal exists", (t) => {
  const root = createFixture(t, {
    "package.json": JSON.stringify({
      private: true,
      workspaces: ["packages/*"],
    }),
    "packages/app/package.json": JSON.stringify({ name: "app" }),
  });

  const report = inspectRepository(root);

  assert.equal(report.monorepo, true);
  assert.equal(report.monorepoStatus, "detected");
  assert.ok(report.monorepoSignals.includes("package.json#workspaces"));
});

test("preserves Node package-manager output and reports lockfile conflicts", (t) => {
  const root = createFixture(t, {
    "package.json": JSON.stringify({
      name: "conflicted",
      packageManager: "pnpm@10.0.0",
      scripts: { typecheck: "tsc --noEmit", build: "vite build" },
      devDependencies: { typescript: "^5.0.0", vite: "^7.0.0" },
    }),
    "package-lock.json": "{}\n",
    "pnpm-lock.yaml": "lockfileVersion: '9.0'\n",
  });

  const report = inspectRepository(root);

  assert.equal(report.packageManager.selected, "pnpm");
  assert.equal(report.packageManager.declared, "pnpm");
  assert.equal(report.packageManager.conflict, true);
  assert.equal(report.dependencyManagers.node.conflict, true);
  assert.equal(report.quality.typecheck, "script");
  assert.equal(report.quality.build, "script");
});

test("does not infer merge enforcement from workflow files", (t) => {
  const withCi = createFixture(t, {
    ".github/workflows/quality.yml": "name: quality\non: [push]\njobs: {}\n",
  });
  const withoutCi = createFixture(t, {});

  const ciReport = inspectRepository(withCi);
  const noCiReport = inspectRepository(withoutCi);

  assert.equal(ciReport.ci.workflowPresent, true);
  assert.equal(ciReport.ci.mergeEnforcement.status, "unknown");
  assert.equal(ciReport.ci.mergeEnforcement.verificationRequired, true);
  assert.match(ciReport.ci.mergeEnforcement.reason, /do not prove/);
  assert.equal(noCiReport.ci.workflowPresent, false);
  assert.equal(noCiReport.ci.mergeEnforcement.status, "absent");
});

test("summary exposes ecosystems, nested manifests, and CI enforcement", () => {
  const summary = renderSummary({
    ecosystems: ["python"],
    manifests: [{ file: "pyproject.toml", ecosystem: "python" }],
    workspaceManifests: [],
    ci: {
      providers: ["github-actions"],
      workflows: [".github/workflows/quality.yml"],
      workflowPresent: true,
      mergeEnforcement: { status: "unknown", reason: "Verify provider settings." },
    },
  });

  assert.match(summary, /\| Ecosystems \| python \|/);
  assert.match(summary, /Merge enforcement: unknown/);
  assert.match(summary, /Verify provider settings/);
});

test("rejects a non-directory target", (t) => {
  const root = createFixture(t, { "repository.txt": "not a directory\n" });
  assert.throws(() => inspectRepository(path.join(root, "repository.txt")), /not a directory/);
});

test("records a malformed nested package without aborting the repository scan", (t) => {
  const root = createFixture(t, {
    "pyproject.toml": "[project]\nname = \"service\"\n",
    "examples/broken/package.json": "{ invalid json",
  });

  const report = inspectRepository(root);
  const brokenProject = report.workspaceProjects.find(({ ecosystem }) => ecosystem === "node");

  assert.ok(brokenProject);
  assert.match(brokenProject.inspectionError, /JSON/);
  assert.deepEqual(report.ecosystems, ["node", "python"]);
});
