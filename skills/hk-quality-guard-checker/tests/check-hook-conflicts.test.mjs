import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

const script = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../scripts/check-hook-conflicts.sh",
);

function createRepository(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "quality-hooks-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return root;
}

function run(root) {
  return spawnSync("sh", [script, root], { encoding: "utf8" });
}

test("reports no manager for an empty repository", (t) => {
  const result = run(createRepository(t));

  assert.equal(result.status, 0);
  assert.match(result.stdout, /hook-managers: none detected/);
});

test("reports multiple hook-management signals", (t) => {
  const root = createRepository(t);
  fs.mkdirSync(path.join(root, ".husky"));
  fs.writeFileSync(path.join(root, "lefthook.yml"), "pre-commit:\n  commands: {}\n");

  const result = run(root);

  assert.equal(result.status, 0);
  assert.match(result.stdout, /husky: .husky directory detected/);
  assert.match(result.stdout, /lefthook: configuration detected/);
  assert.match(result.stdout, /conflict: multiple hook-management signals require manual review/);
});
