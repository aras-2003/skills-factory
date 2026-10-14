#!/usr/bin/env node
import { copyFileSync, existsSync, lstatSync, mkdirSync, readFileSync, readdirSync, realpathSync, rmSync } from "node:fs";
import { createHash } from "node:crypto";
import path from "node:path";
import { execFileSync } from "node:child_process";

const sourceRepository = process.argv[2];
if (!sourceRepository) throw new Error("Usage: node scripts/sync-site-source.mjs <skills-factory-repository>");

const repositoryRoot = realpathSync(sourceRepository);
const sourceRoot = realpathSync(path.join(repositoryRoot, "sites", "skills-factory-site"));
const targetRoot = realpathSync(process.cwd());
const targetGitRoot = realpathSync(execFileSync("git", ["-C", targetRoot, "rev-parse", "--show-toplevel"], { encoding: "utf8" }).trim());
if (targetGitRoot !== targetRoot || sourceRoot === targetRoot || sourceRoot.startsWith(`${targetRoot}${path.sep}`) || targetRoot.startsWith(`${sourceRoot}${path.sep}`)) {
  throw new Error("Run this from the separate Site source checkout; source and target must be distinct Git repositories.");
}

const repositoryGitRoot = realpathSync(execFileSync("git", ["-C", repositoryRoot, "rev-parse", "--show-toplevel"], { encoding: "utf8" }).trim());
if (repositoryGitRoot !== repositoryRoot) throw new Error("The source path must be the Skills Factory repository root.");
const sourceRevision = execFileSync("git", ["-C", repositoryRoot, "rev-parse", "HEAD"], { encoding: "utf8" }).trim();
if (!/^[a-f0-9]{40}$/.test(sourceRevision)) throw new Error("Could not resolve the canonical Skills Factory commit.");
const sourceRelativePath = path.relative(repositoryRoot, sourceRoot);
const dirtySource = execFileSync("git", ["-C", repositoryRoot, "status", "--porcelain", "--untracked-files=all", "--", sourceRelativePath], { encoding: "utf8" });
if (dirtySource.trim()) throw new Error("Commit the Site source to Skills Factory before syncing it to the Site repository.");
const adapterRoot = realpathSync(path.join(repositoryRoot, "adapters", "skills-factory-cloud-next"));
const adapterRelativePath = path.relative(repositoryRoot, adapterRoot);
const dirtyAdapter = execFileSync("git", ["-C", repositoryRoot, "status", "--porcelain", "--untracked-files=all", "--", adapterRelativePath], { encoding: "utf8" });
if (dirtyAdapter.trim()) throw new Error("Commit the Cloud Next adapter source before syncing the Site build.");

function git(cwd, args) {
  return execFileSync("git", ["-C", cwd, ...args], { encoding: "utf8" });
}

function readProjectId(root) {
  const manifest = JSON.parse(readFileSync(path.join(root, ".openai", "hosting.json"), "utf8"));
  if (typeof manifest.project_id !== "string" || !manifest.project_id) throw new Error("Site source has no project_id.");
  return manifest.project_id;
}

if (readProjectId(sourceRoot) !== readProjectId(targetRoot)) throw new Error("The monorepo and Site checkout do not identify the same Site.");
const generatedCatalog = readFileSync(path.join(sourceRoot, "lib", "skills-factory-adapter", "skill-catalog.ts"), "utf8");
const releaseMatch = generatedCatalog.match(/export const LAB_RELEASE = (\{.*\}) as const;/);
if (!releaseMatch || JSON.parse(releaseMatch[1]).source_revision !== sourceRevision) {
  throw new Error("Generate the Cloud Next adapter bundle and Site catalog from the Lab artifact built at the current Skills Factory commit before syncing.");
}
const generatedProvenance = readFileSync(path.join(sourceRoot, "lib", "skills-factory-adapter", "canonical-provenance.ts"), "utf8");
if (!generatedProvenance.includes(`CANONICAL_SOURCE_REVISION = "${sourceRevision}"`)) {
  throw new Error("Generate Site provenance from the current Skills Factory commit before syncing.");
}
const adapterManifest = JSON.parse(readFileSync(path.join(sourceRoot, "lib", "skills-factory-adapter", "adapter-manifest.json"), "utf8"));
if (adapterManifest.source_revision !== sourceRevision || adapterManifest.adapter !== "skills-factory-cloud-next") {
  throw new Error("Generate the Cloud Next adapter bundle from the current Skills Factory commit before syncing.");
}
const adapterSourceNames = readdirSync(path.join(adapterRoot, "src"))
  .filter((filename) => filename.endsWith(".ts"))
  .sort();
const attestedSourceNames = Object.keys(adapterManifest.source_files ?? {}).sort();
if (JSON.stringify(attestedSourceNames) !== JSON.stringify(adapterSourceNames)) {
  throw new Error("The Cloud Next adapter manifest must attest to every canonical TypeScript source file.");
}
for (const [filename, digest] of Object.entries(adapterManifest.source_files)) {
  if (!/^[a-z0-9-]+\.ts$/.test(filename) || typeof digest !== "string") throw new Error("Invalid adapter source manifest.");
  const sourcePath = path.join(adapterRoot, "src", filename);
  if (!existsSync(sourcePath)) throw new Error(`Missing Cloud Next adapter source: ${filename}`);
  const actual = createHash("sha256").update(readFileSync(sourcePath)).digest("hex");
  if (actual !== digest) throw new Error(`Generated Cloud Next adapter is stale: ${filename}`);
  const generatedPath = path.join(sourceRoot, "lib", "skills-factory-adapter", filename);
  if (!existsSync(generatedPath) || createHash("sha256").update(readFileSync(generatedPath)).digest("hex") !== digest) {
    throw new Error(`Bundled Cloud Next adapter does not match canonical source: ${filename}`);
  }
}

if (git(targetRoot, ["status", "--porcelain", "--untracked-files=all"]).trim()) {
  throw new Error("The Site checkout has local changes. Preserve or reconcile them before syncing canonical source.");
}

const excludedDirectories = new Set([".git", ".agents", ".codex", ".next", ".sites-checkout", ".sites-runtime", ".wrangler", "dist", "node_modules", "outputs", "__pycache__"]);
function collectFiles(root) {
  const files = new Set();
  function walk(directory, relative = "") {
    for (const entry of readdirSync(directory, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      if (excludedDirectories.has(entry.name)) continue;
      if (entry.name === ".env" || entry.name.startsWith(".env.") || entry.name.endsWith(".tsbuildinfo") || entry.name.endsWith(".pyc") || entry.name.endsWith(".tar.gz")) continue;
      const absolute = path.join(directory, entry.name);
      const child = relative ? path.join(relative, entry.name) : entry.name;
      const info = lstatSync(absolute);
      if (info.isSymbolicLink()) throw new Error(`Refusing a symlink in Site source: ${child}`);
      if (info.isDirectory()) walk(absolute, child);
      else if (info.isFile()) files.add(child.split(path.sep).join("/"));
      else throw new Error(`Unsupported Site source entry: ${child}`);
    }
  }
  walk(root);
  return files;
}

const sourceFiles = collectFiles(sourceRoot);
if (!sourceFiles.has("lib/skills-factory-adapter/cloud-tools.ts")
  || !sourceFiles.has("lib/skills-factory-adapter/mcp-handler.ts")
  || !sourceFiles.has("lib/skills-factory-adapter/skill-catalog.ts")
  || !sourceFiles.has("lib/skills-factory-adapter/canonical-provenance.ts")) {
  throw new Error("The generated Cloud Next adapter bundle must be present in the canonical Site build source.");
}
const trackedTarget = git(targetRoot, ["ls-files", "-z"]).split("\0").filter(Boolean);
const providerOnlyReleaseNotes = new Set([
  "PRIVATE-DRAFT-EXTENSION.md",
  "RELEASE-2026-10-10.md",
  "RELEASE-R18-ATTENTION.md",
  "RELEASE-R20.md",
]);
for (const relative of trackedTarget) {
  if (!sourceFiles.has(relative) && !providerOnlyReleaseNotes.has(relative)) {
    const absolute = path.join(targetRoot, relative);
    if (existsSync(absolute) && lstatSync(absolute).isFile()) rmSync(absolute);
  }
}
for (const relative of sourceFiles) {
  const from = path.join(sourceRoot, relative);
  const to = path.join(targetRoot, relative);
  mkdirSync(path.dirname(to), { recursive: true });
  copyFileSync(from, to);
}

console.log(JSON.stringify({ project_id: readProjectId(targetRoot), canonical_source_revision: sourceRevision, lab_release: JSON.parse(releaseMatch[1]).release_id, files_synced: sourceFiles.size }));
