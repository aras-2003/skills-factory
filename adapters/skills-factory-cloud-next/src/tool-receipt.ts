import type { SiteVersionMetadata } from "./cloud-tools";

// Sorted JSON binds this unsigned receipt to input/output content, not model reasoning.
function canonical(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonical);
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0).map(([key, item]) => [key, canonical(item)]));
  }
  return value;
}
async function digest(value: unknown) {
  const bytes = new TextEncoder().encode(JSON.stringify(canonical(value ?? null)));
  const hash = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2, "0")).join("");
}
export async function toolReceipt(name: string, input: unknown, output: unknown, metadata?: SiteVersionMetadata, failure?: "FAIL_VALIDATION" | "FAIL_RENDERER_INVOCATION" | "FAIL_TOOL_INVOCATION") {
  const chart = name === "render_bar_chart" || name === "render_line_chart";
  return {
    schema_version: "1.0",
    kind: "unsigned_mcp_tool_call_receipt",
    tool_name: name,
    status: failure ? "FAILURE" : "SUCCESS",
    execution_state: failure === "FAIL_VALIDATION" ? "not_executed" : "executed",
    completed_at: new Date().toISOString(),
    source_revision: metadata?.tag && /^[a-f0-9]{40}$/i.test(metadata.tag) ? metadata.tag : "unattested",
    input_sha256: await digest(input),
    output_sha256: await digest(output),
    ...(failure ? { failure_state: failure } : {}),
    ...(chart ? { artifact_state: failure ?? "rendered", client_display_state: failure ? "not_applicable" : "not_observable" } : {}),
  };
}
