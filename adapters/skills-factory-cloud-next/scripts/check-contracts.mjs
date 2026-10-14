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
const output = path.join(siteRoot, ".sites-runtime", "contracts.test.mjs");
await mkdir(path.dirname(output), { recursive: true });
await build({ entryPoints: [fileURLToPath(new URL("../tests/contracts.test.ts", import.meta.url))], bundle: true, platform: "node", format: "esm", outfile: output });
const result = spawnSync(process.execPath, ["--test", output], { stdio: "inherit" });
process.exit(result.status ?? 1);
