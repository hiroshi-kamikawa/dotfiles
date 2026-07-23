#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { inspectPackageJson } from "./inspect-package-json.mjs";

const IGNORED_DIRECTORIES = new Set([
  ".git",
  ".hg",
  ".svn",
  ".tox",
  ".venv",
  "build",
  "coverage",
  "dist",
  "node_modules",
  "target",
  "vendor",
]);

const MANIFEST_ECOSYSTEMS = new Map([
  ["package.json", "node"],
  ["pyproject.toml", "python"],
  ["requirements.txt", "python"],
  ["Pipfile", "python"],
  ["composer.json", "php"],
  ["go.mod", "go"],
  ["Cargo.toml", "rust"],
  ["Gemfile", "ruby"],
]);

const QUALITY_CONFIG_PATTERNS = [
  /^eslint\.config\./,
  /^\.eslintrc/,
  /^biome\.jsonc?$/,
  /^\.?prettier(rc|\.)/,
  /^stylelint\.config\./,
  /^\.stylelintrc/,
  /^vitest\.config\./,
  /^jest\.config\./,
  /^playwright\.config\./,
  /^cypress\.config\./,
  /^commitlint\.config\./,
  /^lint-staged\.config\./,
  /^\.lintstagedrc/,
  /^\.gitleaks\.toml$/,
  /^ruff\.toml$/,
  /^\.ruff\.toml$/,
  /^mypy\.ini$/,
  /^pytest\.ini$/,
  /^tox\.ini$/,
  /^phpstan(\.baseline)?\.neon(\.dist)?$/,
  /^phpunit\.xml(\.dist)?$/,
  /^phpcs\.xml(\.dist)?$/,
  /^\.golangci\.ya?ml$/,
  /^rustfmt\.toml$/,
];

const DEPENDENCY_MANAGER_FILES = {
  node: [
    ["pnpm", "pnpm-lock.yaml"],
    ["npm", "package-lock.json"],
    ["yarn", "yarn.lock"],
    ["bun", "bun.lock"],
    ["bun", "bun.lockb"],
  ],
  python: [
    ["uv", "uv.lock"],
    ["poetry", "poetry.lock"],
    ["pipenv", "Pipfile.lock"],
    ["pip-tools/pip", "requirements.txt"],
  ],
  php: [["composer", "composer.lock"]],
  go: [["go modules", "go.sum"]],
  rust: [["cargo", "Cargo.lock"]],
  ruby: [["bundler", "Gemfile.lock"]],
};

function toPosix(relative) {
  return relative.split(path.sep).join("/");
}

function scanRepository(root, maxDepth = 6, maxDirectories = 5000) {
  const manifests = [];
  const qualityConfigs = [];
  let visitedDirectories = 0;
  let truncated = false;

  function visit(relativeDirectory, depth) {
    if (depth > maxDepth || visitedDirectories >= maxDirectories) {
      truncated = true;
      return;
    }

    const absoluteDirectory = path.join(root, relativeDirectory);
    let entries;
    try {
      entries = fs.readdirSync(absoluteDirectory, { withFileTypes: true });
    } catch {
      return;
    }
    visitedDirectories += 1;

    for (const entry of entries) {
      const relative = path.join(relativeDirectory, entry.name);
      if (entry.isFile() && MANIFEST_ECOSYSTEMS.has(entry.name)) {
        manifests.push({
          file: toPosix(relative),
          ecosystem: MANIFEST_ECOSYSTEMS.get(entry.name),
        });
      }
      if (entry.isFile() && QUALITY_CONFIG_PATTERNS.some((pattern) => pattern.test(entry.name))) {
        qualityConfigs.push(toPosix(relative));
      } else if (entry.isDirectory() && !IGNORED_DIRECTORIES.has(entry.name)) {
        visit(relative, depth + 1);
      }
    }
  }

  visit("", 0);
  manifests.sort((a, b) => a.file.localeCompare(b.file));
  qualityConfigs.sort();
  return { manifests, qualityConfigs, visitedDirectories, truncated, maxDepth, maxDirectories };
}

export function inspectRepository(repository = ".") {
  const root = path.resolve(repository);

  function exists(relative) {
    return fs.existsSync(path.join(root, relative));
  }

  function readText(relative) {
    try {
      return fs.readFileSync(path.join(root, relative), "utf8");
    } catch {
      return null;
    }
  }

  function listFiles(relative, predicate = () => true) {
    const directory = path.join(root, relative);
    if (!fs.existsSync(directory)) return [];
    return fs
      .readdirSync(directory, { withFileTypes: true })
      .filter((entry) => entry.isFile() && predicate(entry.name))
      .map((entry) => path.posix.join(relative, entry.name));
  }

  function detectNodePackageManager(packageInfo) {
    const declared = packageInfo?.packageManager?.split("@")[0] ?? null;
    const lockfiles = [
      ["pnpm", "pnpm-lock.yaml"],
      ["npm", "package-lock.json"],
      ["yarn", "yarn.lock"],
      ["bun", "bun.lock"],
      ["bun", "bun.lockb"],
    ].filter(([, file]) => exists(file));
    return {
      selected: declared ?? (lockfiles.length === 1 ? lockfiles[0][0] : null),
      declared,
      lockfiles: lockfiles.map(([, file]) => file),
      conflict: new Set(lockfiles.map(([manager]) => manager)).size > 1,
    };
  }

  function detectDependencyManagers() {
    return Object.fromEntries(
      Object.entries(DEPENDENCY_MANAGER_FILES).map(([ecosystem, candidates]) => {
        const detected = candidates
          .filter(([, file]) => exists(file))
          .map(([manager, file]) => ({ manager, file }));
        return [
          ecosystem,
          {
            managers: [...new Set(detected.map(({ manager }) => manager))],
            files: detected.map(({ file }) => file),
            conflict: ecosystem === "node" && new Set(detected.map(({ manager }) => manager)).size > 1,
          },
        ];
      }),
    );
  }

  function inspectProjects(manifests) {
    const groups = new Map();
    for (const manifest of manifests) {
      const directory = path.posix.dirname(manifest.file);
      const key = `${directory}\0${manifest.ecosystem}`;
      const group = groups.get(key) ?? {
        directory,
        ecosystem: manifest.ecosystem,
        manifests: [],
      };
      group.manifests.push(manifest.file);
      groups.set(key, group);
    }

    return [...groups.values()]
      .map((project) => {
        const candidates = DEPENDENCY_MANAGER_FILES[project.ecosystem] ?? [];
        const detected = candidates
          .filter(([, filename]) => {
            const relative = project.directory === "." ? filename : path.posix.join(project.directory, filename);
            return exists(relative);
          })
          .map(([manager, filename]) => ({
            manager,
            file: project.directory === "." ? filename : path.posix.join(project.directory, filename),
          }));
        let declaredManager = null;
        let packageInspection = null;
        let inspectionError = null;
        if (project.ecosystem === "node") {
          const packageManifest = project.manifests.find((file) => path.posix.basename(file) === "package.json");
          if (packageManifest) {
            try {
              packageInspection = inspectPackageJson(path.join(root, packageManifest));
              declaredManager = packageInspection.packageManager?.split("@")[0] ?? null;
            } catch (error) {
              inspectionError = error.message;
            }
          }
        }
        return {
          ...project,
          declaredManager,
          dependencyManagers: [...new Set(detected.map(({ manager }) => manager))],
          dependencyFiles: detected.map(({ file }) => file),
          dependencyManagerConflict:
            project.ecosystem === "node" && new Set(detected.map(({ manager }) => manager)).size > 1,
          quality: packageInspection?.quality ?? null,
          frameworks: packageInspection?.frameworks ?? [],
          inspectionError,
        };
      })
      .sort((a, b) => `${a.directory}/${a.ecosystem}`.localeCompare(`${b.directory}/${b.ecosystem}`));
  }

  function detectRuntimes(packageInfo) {
    const versionFiles = [
      ".node-version",
      ".nvmrc",
      ".python-version",
      ".ruby-version",
      ".tool-versions",
      "mise.toml",
      "rust-toolchain",
      "rust-toolchain.toml",
      "go.work",
    ]
      .filter(exists)
      .map((file) => ({ file, value: readText(file)?.trim() ?? "" }));
    return {
      node: { engines: packageInfo?.engines?.node ?? null },
      files: versionFiles,
    };
  }

  function detectHooks(packageInfo) {
    const otherManagers = [];
    if (
      exists("lefthook.yml") ||
      exists("lefthook.yaml") ||
      packageInfo?.hooks.otherManagerDependencies.includes("lefthook")
    ) {
      otherManagers.push("lefthook");
    }
    if (exists(".pre-commit-config.yaml") || exists(".pre-commit-config.yml")) otherManagers.push("pre-commit");
    if (exists(".githooks")) otherManagers.push("custom .githooks");
    if (packageInfo?.hooks.otherManagerDependencies.includes("simple-git-hooks")) {
      otherManagers.push("simple-git-hooks");
    }

    return {
      husky: exists(".husky") || Boolean(packageInfo?.hooks.huskyDependency),
      huskyDirectory: exists(".husky"),
      prepare: packageInfo?.hooks.prepare ?? null,
      otherManagers: [...new Set(otherManagers)],
      mixed: (exists(".husky") || Boolean(packageInfo?.hooks.huskyDependency)) && otherManagers.length > 0,
    };
  }

  function detectCi() {
    const githubWorkflows = listFiles(".github/workflows", (name) => /\.ya?ml$/i.test(name));
    const providers = [];
    if (githubWorkflows.length) providers.push("github-actions");
    if (exists(".gitlab-ci.yml")) providers.push("gitlab-ci");
    if (exists("circle.yml") || exists(".circleci")) providers.push("circleci");
    if (exists("azure-pipelines.yml")) providers.push("azure-pipelines");
    if (exists("bitbucket-pipelines.yml")) providers.push("bitbucket-pipelines");
    const workflowPresent = providers.length > 0;
    return {
      providers,
      workflows: githubWorkflows,
      workflowPresent,
      mergeEnforcement: {
        status: workflowPresent ? "unknown" : "absent",
        reason: workflowPresent
          ? "Workflow files do not prove that required checks or protected-branch rules are enabled; verify provider settings."
          : "No supported CI workflow was detected, so merge enforcement is absent.",
        verificationRequired: workflowPresent,
      },
    };
  }

  function detectQuality(packageInfo) {
    const configs = scan.qualityConfigs;
    const rootConfigs = configs.filter((file) => path.posix.dirname(file) === ".");
    const quality = { ...(packageInfo?.quality ?? {}) };
    if (!quality.lint) {
      if (rootConfigs.some((file) => file.startsWith("biome."))) quality.lint = "biome";
      else if (rootConfigs.some((file) => /eslint/.test(file))) quality.lint = "eslint";
      else if (rootConfigs.some((file) => /ruff/.test(file))) quality.lint = "ruff";
      else if (rootConfigs.some((file) => /phpstan|phpcs/.test(file))) quality.lint = "phpstan/phpcs";
      else if (rootConfigs.some((file) => /golangci/.test(file))) quality.lint = "golangci-lint";
      else if (rootConfigs.includes("rustfmt.toml")) quality.lint = "rustfmt";
    }
    if (!quality.format) {
      if (rootConfigs.some((file) => /prettier/.test(file))) quality.format = "prettier";
      else if (rootConfigs.some((file) => file.startsWith("biome."))) quality.format = "biome";
      else if (rootConfigs.includes("rustfmt.toml")) quality.format = "rustfmt";
    }
    if (!quality.secretScan && rootConfigs.includes(".gitleaks.toml")) quality.secretScan = "gitleaks";
    return { ...quality, configs };
  }

  if (!fs.statSync(root).isDirectory()) {
    throw new Error(`repository is not a directory: ${root}`);
  }

  const scan = scanRepository(root);
  const packagePath = path.join(root, "package.json");
  const packageInfo = fs.existsSync(packagePath) ? inspectPackageJson(packagePath) : null;
  const ecosystems = [...new Set(scan.manifests.map(({ ecosystem }) => ecosystem))].sort();
  const workspaceManifests = scan.manifests.filter(({ file }) => path.posix.dirname(file) !== ".");
  const projects = inspectProjects(scan.manifests);
  const explicitMonorepoSignals = [
    ...(packageInfo?.workspaces ? ["package.json#workspaces"] : []),
    ...(exists("pnpm-workspace.yaml") ? ["pnpm-workspace.yaml"] : []),
    ...(exists("turbo.json") ? ["turbo.json"] : []),
    ...(exists("nx.json") ? ["nx.json"] : []),
    ...(exists("lerna.json") ? ["lerna.json"] : []),
    ...(exists("go.work") ? ["go.work"] : []),
  ];
  const monorepoSignals = [
    ...explicitMonorepoSignals,
    ...(workspaceManifests.length > 0 ? ["nested manifests"] : []),
  ];
  const monorepoStatus =
    explicitMonorepoSignals.length > 0 ? "detected" : workspaceManifests.length > 0 ? "candidate" : "absent";
  const runtimes = detectRuntimes(packageInfo);

  return {
    repository: root,
    git: exists(".git"),
    packageJson: exists("package.json"),
    manifests: scan.manifests,
    workspaceManifests,
    projects,
    workspaceProjects: projects.filter(({ directory }) => directory !== "."),
    qualityConfigs: scan.qualityConfigs,
    ecosystems,
    scan: {
      visitedDirectories: scan.visitedDirectories,
      truncated: scan.truncated,
      maxDepth: scan.maxDepth,
      maxDirectories: scan.maxDirectories,
    },
    packageManager: detectNodePackageManager(packageInfo),
    dependencyManagers: detectDependencyManagers(),
    node: {
      engines: runtimes.node.engines,
      files: runtimes.files.filter(({ file }) =>
        [".node-version", ".nvmrc", ".tool-versions", "mise.toml"].includes(file),
      ),
    },
    runtimes,
    frameworks: packageInfo?.frameworks ?? [],
    typescript: Boolean(packageInfo?.typescript || exists("tsconfig.json")),
    monorepo: monorepoStatus === "detected",
    monorepoStatus,
    monorepoSignals,
    hooks: detectHooks(packageInfo),
    quality: detectQuality(packageInfo),
    scripts: packageInfo?.scripts ?? {},
    ci: detectCi(),
  };
}

function isMainModule() {
  return process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href;
}

if (isMainModule()) {
  try {
    process.stdout.write(`${JSON.stringify(inspectRepository(process.argv[2] ?? "."), null, 2)}\n`);
  } catch (error) {
    process.stderr.write(`inspect-repository: ${error.message}\n`);
    process.exitCode = 1;
  }
}
