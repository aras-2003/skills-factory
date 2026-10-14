import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

const projectId = "appgprj_6ac56f2116588191a4a1ebc682c97865";
const scriptPath = fileURLToPath(new URL("../scripts/sync-site-source.mjs", import.meta.url));

function git(cwd, args) {
  const result = spawnSync("git", ["-C", cwd, ...args], { encoding: "utf8" });
  assert.equal(result.status, 0, result.stderr);
  return result.stdout.trim();
}

function initRepository(root) {
  mkdirSync(root, { recursive: true });
  git(root, ["init", "-q"]);
  git(root, ["config", "user.name", "Site Sync Test"]);
  git(root, ["config", "user.email", "site-sync-test@example.invalid"]);
}

function writeFile(root, relative, content) {
  const file = path.join(root, relative);
  mkdirSync(path.dirname(file), { recursive: true });
  writeFileSync(file, content);
}

test("sync mirrors only the clean, same-Site canonical source and preserves checkout Git metadata", () => {
  const temporary = mkdtempSync(path.join(os.tmpdir(), "skills-factory-site-sync-"));
  try {
    const monorepo = path.join(temporary, "skills-factory");
    const siteSource = path.join(monorepo, "sites", "skills-factory-cloud-next");
    const target = path.join(temporary, "provider-site-checkout");
    initRepository(monorepo);
    writeFile(monorepo, "sites/skills-factory-cloud-next/.openai/hosting.json", JSON.stringify({ project_id: projectId }));
    writeFile(monorepo, "sites/skills-factory-cloud-next/.gitignore", "lib/skill-catalog.ts\nlib/canonical-provenance.ts\n");
    writeFile(monorepo, "sites/skills-factory-cloud-next/lib/cloud-tools.ts", "export const canonical = true;\n");
    git(monorepo, ["add", "sites/skills-factory-cloud-next"]);
    git(monorepo, ["commit", "-qm", "Add canonical Site source"]);
    const sourceRevision = git(monorepo, ["rev-parse", "HEAD"]);
    writeFile(siteSource, "lib/skill-catalog.ts", `export const LAB_RELEASE = {"source_revision":"${sourceRevision}","release_id":"test+1"} as const;\n`);
    writeFile(siteSource, "lib/canonical-provenance.ts", `export const CANONICAL_SOURCE_REVISION = "${sourceRevision}" as const;\n`);

    initRepository(target);
    writeFile(target, ".openai/hosting.json", JSON.stringify({ project_id: projectId }));
    writeFile(target, "old-site-code.ts", "stale\n");
    writeFile(target, "RELEASE-R20.md", "private provider release notes\n");
    git(target, ["add", ".openai/hosting.json", "old-site-code.ts", "RELEASE-R20.md"]);
    git(target, ["commit", "-qm", "Existing provider mirror"]);
    const targetHead = git(target, ["rev-parse", "HEAD"]);

    const result = spawnSync(process.execPath, [scriptPath, monorepo], { cwd: target, encoding: "utf8" });
    assert.equal(result.status, 0, result.stderr);
    assert.deepEqual(JSON.parse(result.stdout), {
      project_id: projectId,
      canonical_source_revision: sourceRevision,
      lab_release: "test+1",
      files_synced: 5,
    });
    assert.equal(readFileSync(path.join(target, "lib/cloud-tools.ts"), "utf8"), "export const canonical = true;\n");
    assert.equal(existsSync(path.join(target, "old-site-code.ts")), false);
    assert.equal(readFileSync(path.join(target, "lib/canonical-provenance.ts"), "utf8").includes(sourceRevision), true);
    assert.equal(readFileSync(path.join(target, "RELEASE-R20.md"), "utf8"), "private provider release notes\n");
    assert.equal(git(target, ["rev-parse", "HEAD"]), targetHead);
    assert.equal(git(target, ["status", "--porcelain", "--", ".gitignore"]).includes(".gitignore"), true);
  } finally {
    rmSync(temporary, { recursive: true, force: true });
  }
});
