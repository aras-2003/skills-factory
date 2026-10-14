// Development-only verification; never imported by the Worker.
import { createRequire } from "node:module";
import { mkdir } from "node:fs/promises";
import { spawnSync } from "node:child_process";
const require = createRequire(import.meta.url);
const toolRequire = createRequire(require.resolve("wrangler"));
const { build } = await import(toolRequire.resolve("esbuild"));
await mkdir(".sites-runtime", { recursive: true });
await build({ entryPoints: ["tests/contracts.test.ts"], bundle: true, platform: "node", format: "esm", outfile: ".sites-runtime/contracts.test.mjs" });
const result = spawnSync(process.execPath, ["--test", ".sites-runtime/contracts.test.mjs"], { stdio: "inherit" });
process.exit(result.status ?? 1);
