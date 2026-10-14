#!/usr/bin/env node
import { lstat, readFile, readdir, realpath, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const siteRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const artifactArg = process.argv[2];
const siteRootArg = process.argv[3];
if (!artifactArg) {
  throw new Error("Usage: node scripts/sync-lab-references.mjs <extracted-lab-artifact> [site-root]");
}
const targetRoot = siteRootArg ? path.resolve(siteRootArg) : siteRoot;

const artifactRoot = await realpath(path.resolve(artifactArg));
const skillsRoot = await realpath(path.join(artifactRoot, "skills"));
const catalogPath = path.join(targetRoot, "lib", "skill-catalog.ts");
const source = await readFile(catalogPath, "utf8");
const match = source.match(/export const SKILL_CATALOG = (\[.*\]) as const;/s);
if (!match) throw new Error("Could not parse generated SKILL_CATALOG array");
const catalog = JSON.parse(match[1]);
const allowedExtensions = new Set([".md", ".txt", ".json", ".yaml", ".yml"]);

async function collectReferences(skillName) {
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(skillName)) throw new Error(`Invalid skill name: ${skillName}`);
  const skillPath = path.join(skillsRoot, skillName);
  const skillInfo = await lstat(skillPath);
  if (skillInfo.isSymbolicLink() || !skillInfo.isDirectory()) throw new Error(`Invalid skill directory: ${skillName}`);
  const skillRoot = await realpath(skillPath);
  const relativeSkill = path.relative(skillsRoot, skillRoot);
  if (relativeSkill.startsWith(`..${path.sep}`) || path.isAbsolute(relativeSkill)) throw new Error(`Skill directory escapes artifact: ${skillName}`);
  const referencesRoot = path.join(skillRoot, "references");
  const result = {};

  async function walk(directory, relativeParts = []) {
    const entries = await readdir(directory, { withFileTypes: true });
    for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name))) {
      if (entry.name === "evals") continue;
      const absolute = path.join(directory, entry.name);
      const parts = [...relativeParts, entry.name];
      const info = await lstat(absolute);
      if (info.isSymbolicLink()) continue;
      if (info.isDirectory()) {
        await walk(absolute, parts);
        continue;
      }
      if (!info.isFile() || !allowedExtensions.has(path.extname(entry.name).toLowerCase())) continue;
      const resolved = await realpath(absolute);
      const relativeToSkill = path.relative(skillRoot, resolved);
      if (relativeToSkill.startsWith(`..${path.sep}`) || path.isAbsolute(relativeToSkill)) continue;
      result[path.posix.join("references", ...parts)] = await readFile(resolved, "utf8");
    }
  }

  try {
    const referencesInfo = await lstat(referencesRoot);
    if (referencesInfo.isSymbolicLink() || !referencesInfo.isDirectory()) return result;
  } catch (error) {
    if (error?.code === "ENOENT") return result;
    throw error;
  }
  await walk(referencesRoot);
  return result;
}

for (const skill of catalog) {
  skill.reference_files = await collectReferences(skill.name);
}

const updated = source.replace(match[1], JSON.stringify(catalog));
await writeFile(catalogPath, updated);
const referenceCount = catalog.reduce((sum, skill) => sum + Object.keys(skill.reference_files).length, 0);
console.log(`Synced ${referenceCount} allow-listed references for ${catalog.length} Lab skills; eval fixtures excluded.`);
