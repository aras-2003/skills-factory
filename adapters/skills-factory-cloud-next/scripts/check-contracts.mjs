// Development-only verification; never imported by the Worker.
import { createRequire } from "node:module";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
const siteRoot = process.cwd();
const require = createRequire(path.join(siteRoot, "package.json"));
const toolRequire = createRequire(require.resolve("wrangler"));
const { build } = await import(toolRequire.resolve("esbuild"));
const outputRoot = path.join(siteRoot, ".sites-runtime");
const testEntries = ["contracts.test.ts", "catalog-provenance.test.ts", "load-skill-source-revision.test.ts"].map((name) => fileURLToPath(new URL(`../tests/${name}`, import.meta.url)));
const outputs = testEntries.map((_, index) => path.join(outputRoot, `contracts-${index}.test.mjs`));
await mkdir(outputRoot, { recursive: true });
for (let index = 0; index < testEntries.length; index++) {
  await build({
    entryPoints: [testEntries[index]], bundle: true, platform: "node", format: "esm", outfile: outputs[index],
    nodePaths: [path.join(siteRoot, "node_modules")],
    plugins: [{
      name: "generated-adapter-data",
      setup(build) {
        build.onResolve({ filter: /^\.\/(skill-catalog|canonical-provenance)$/ }, (args) => {
          if (!args.importer.includes(`${path.sep}adapters${path.sep}skills-factory-cloud-next${path.sep}src${path.sep}`)) return;
          return { path: path.join(siteRoot, "lib", "skills-factory-adapter", `${args.path.slice(2)}.ts`) };
        });
      },
    }],
  });
}
const result = spawnSync(process.execPath, ["--test", ...outputs], { stdio: "inherit" });
process.exit(result.status ?? 1);
