import { readFile } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, resolve as resolvePath } from 'node:path';
import ts from 'typescript';
const site = resolvePath(dirname(fileURLToPath(import.meta.url)), '..');
const stubs = {
  'cloudflare:workers': 'export const env = new Proxy({}, { get: (_, key) => globalThis.__pic.env[key] });',
  '@/app/chatgpt-auth': 'export async function getChatGPTUser() { return globalThis.__pic.user; }',
  '@/lib/skills-factory-adapter/cloud-tools': 'export const SOURCE = new Proxy({}, { get: (_, key) => globalThis.__pic.source[key] }); export async function callTool(...args) { return globalThis.__pic.callTool(...args); }',
};
export async function resolve(specifier, context, nextResolve) {
  if (Object.hasOwn(stubs, specifier)) return { url: `data:text/javascript,${encodeURIComponent(stubs[specifier])}`, shortCircuit: true };
  if (specifier.startsWith('@/')) return { url: pathToFileURL(resolvePath(site, specifier.slice(2) + (specifier.endsWith('.mjs') ? '' : '.ts'))).href, shortCircuit: true };
  return nextResolve(specifier, context);
}
export async function load(url, context, nextLoad) {
  if (new URL(url).pathname.endsWith('.ts')) {
    const source = await readFile(fileURLToPath(url), 'utf8');
    return { format: 'module', source: ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText, shortCircuit: true };
  }
  return nextLoad(url, context);
}
