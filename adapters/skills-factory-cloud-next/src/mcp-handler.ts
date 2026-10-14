import { ZodError } from "zod";
import { CHART_UI_HTML, CHART_UI_URI } from "./chart-ui";
import { toolReceipt } from "./tool-receipt";
import { callTool, TOOLS, type SiteVersionMetadata } from "./cloud-tools";

const LIMIT = 128 * 1024;
const versions = ["2026-07-28", "2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05"];
const json = (v: unknown, status = 200) => Response.json(v, { status, headers: { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" } });
const error = (id: unknown, code: number, message: string, status = 200) => {
  const headers = status === 401 ? { "WWW-Authenticate": "Bearer" } : undefined;
  return Response.json({ jsonrpc: "2.0", id: id ?? null, error: { code, message } }, {
    status,
    headers: { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", ...(headers ?? {}) },
  });
};
export async function handleMcp(request: Request, versionMetadata?: SiteVersionMetadata): Promise<Response> {
  if (request.method !== "POST") return new Response(null, { status: 405, headers: { Allow: "POST" } });
  const origin = request.headers.get("origin");
  if (origin && origin !== new URL(request.url).origin) return error(null, -32000, "Origin not allowed", 403);
  if (!request.headers.get("content-type")?.toLowerCase().startsWith("application/json")) return error(null, -32600, "application/json required", 415);
  const protocol = request.headers.get("mcp-protocol-version");
  if (protocol && !versions.includes(protocol)) return error(null, -32600, "Unsupported protocol version", 400);
  if (Number(request.headers.get("content-length")) > LIMIT) return error(null, -32600, "Request too large", 413);
  let body: Record<string, unknown>;
  try {
    const reader = request.body?.getReader();
    if (!reader) return error(null, -32700, "Empty body", 400);
    let bytes = 0; const decoder = new TextDecoder(); let data = "";
    while (true) { const { done, value } = await reader.read(); if (done) break; bytes += value.byteLength; if (bytes > LIMIT) { await reader.cancel(); return error(null, -32600, "Request too large", 413); } data += decoder.decode(value, { stream: true }); }
    data += decoder.decode(); body = JSON.parse(data);
  } catch { return error(null, -32700, "Invalid JSON", 400); }
  if (!body || typeof body !== "object" || Array.isArray(body) || body.jsonrpc !== "2.0" || typeof body.method !== "string") return error(null, -32600, "Invalid JSON-RPC request", 400);
  const id = body.id;
  if (id !== undefined && typeof id !== "string" && typeof id !== "number") return error(null, -32600, "Invalid request id", 400);
  if (id === undefined) return new Response(null, { status: 202 });
  const params = body.params as Record<string, unknown> | undefined;
  if (params !== undefined && (!params || typeof params !== "object" || Array.isArray(params))) return error(id, -32602, "Invalid params");
  let result: unknown;
  switch (body.method) {
    case "initialize":
      if (typeof params?.protocolVersion !== "string" || !params.clientInfo || !params.capabilities) return error(id, -32602, "Missing initialization parameters");
      result = { protocolVersion: versions.includes(params.protocolVersion) ? params.protocolVersion : versions[0], capabilities: { tools: { listChanged: false }, resources: { subscribe: false, listChanged: false } }, serverInfo: { name: "skills-factory-runtime", version: "site-mcp-v2" }, instructions: "Skills Factory Site MCP runtime v2. For source/backlog reconciliation, request the exact source revision and ID sets before identifying a missing item. Catalog counts do not prove GitHub Project membership, native fields/dependencies, or runtime acceptance. Missing revision means BLOCKED_SOURCE_REVISION for that comparison; never invent a source match. list_skills exposes the exact packaged Lab catalog; load_skill returns packaged SKILL.md instructions and allow-listed supporting references, excluding eval fixtures. The host model executes loaded instructions. runtime_info identifies this Site deployment when platform metadata is available. For investment requests, call route_investment_request before analysis, retain its routing_receipt, then call load_skill for the exact returned child_workflow and execute the loaded workflow. Do not substitute another specialist or claim execution without an actual child load/execution trace. The routed_only receipt describes only the router call; after loading the exact child workflow, follow its instructions. If a required child or provider is unavailable, stop that dependent work and report the missing capability. Do not route unrelated editing, proofreading, security, governance or accounting tasks. Routing selects a workflow; it does not execute it or provide investment advice. Chart calls require original expected count fields; if a connector omits counts or truncates values, the server rejects the chart without rendering. Charts use explicit finite caller numbers only. Interactive chart widgets use self-contained HTML/CSS/SVG and only the data returned by the chart call; other hosts retain accessible structured data. No persistence, repository fetching, trading, filesystem or secrets." }; break;
    case "ping": result = {}; break;
    case "tools/list": result = { tools: TOOLS }; break;
    case "resources/list": result = { resources: [{ uri: CHART_UI_URI, name: "Interactive charts", description: "Self-contained HTML/CSS/SVG chart view for bar and line chart tools.", mimeType: "text/html;profile=mcp-app" }] }; break;
    case "resources/read": {
      if (params?.uri !== CHART_UI_URI) return error(id, -32602, "Unknown resource URI");
      result = { contents: [{ uri: CHART_UI_URI, mimeType: "text/html;profile=mcp-app", text: CHART_UI_HTML, _meta: { ui: { prefersBorder: true, csp: { connectDomains: [], resourceDomains: [] } }, "openai/widgetDescription": "Interactive charts built from caller-supplied data. Click marks for values; line-chart series can be toggled.", "openai/ui": { availableDisplayModes: ["inline", "fullscreen"] } } }] };
      break;
    }
    case "tools/call": {
      // Sites authenticates and authorizes visitors at its boundary. No local auth bypass.
      if (!request.headers.get("oai-authenticated-user-id")) return error(id, -32001, "Sites authenticated identity required", 401);
      if (typeof params?.name !== "string") return error(id, -32602, "Tool name required");
      if (!TOOLS.some(t => t.name === params.name)) return error(id, -32602, "Unknown tool");
      try {
        const value = await callTool(params.name, params.arguments, versionMetadata);
        const output = { ...value, tool_receipt: await toolReceipt(params.name, params.arguments, value, versionMetadata) };
        const summary = "svg" in output ? { ...output, svg: "[interactive MCP App; exact SVG retained in structuredContent]" } : output;
        const content: unknown[] = [{ type: "text", text: JSON.stringify(summary) }];
        result = { content, structuredContent: output, isError: false };
      } catch (e) {
        const message = e instanceof Error ? e.message : "Invalid tool arguments";
        const failure = e instanceof ZodError ? "FAIL_VALIDATION" : params.name.startsWith("render_") ? "FAIL_RENDERER_INVOCATION" : "FAIL_TOOL_INVOCATION";
        const output = { error: message, tool_receipt: await toolReceipt(params.name, params.arguments, { error: message }, versionMetadata, failure) };
        result = { content: [{ type: "text", text: JSON.stringify(output) }], structuredContent: output, isError: true };
      }
      break;
    }
    default: return error(id, -32601, "Method not found");
  }
  return json({ jsonrpc: "2.0", id, result });
}