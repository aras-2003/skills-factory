import handler from "vinext/server/fetch-handler";
import { runWithConnectorBinding } from "../lib/connector-context";
import type { ConnectorBinding } from "../lib/connector-contract.mjs";
import { handleMcp } from "../lib/skills-factory-adapter/mcp-handler";
import { resolveSiteVersionMetadata } from "../lib/site-version-metadata";

type RuntimeEnvironment = Cloudflare.Env & {
  CF_VERSION_METADATA?: { id?: string; tag?: string; timestamp?: string | number };
  SKILLS_FACTORY_RELEASE_ID?: string;
  SKILLS_FACTORY_SOURCE_REVISION?: string;
  SKILLS_FACTORY_DEPLOYED_AT?: string;
};

export default {
  fetch(request: Request, env: RuntimeEnvironment, ctx: ExecutionContext<{ CONNECTORS?: ConnectorBinding }>) {
    if (new URL(request.url).pathname === "/mcp") {
      return handleMcp(request, resolveSiteVersionMetadata(env));
    }
    let binding = ctx.props?.CONNECTORS;
    // Local preview emulates the same request-scoped capability. This branch and
    // the auxiliary service binding are absent from production builds.
    if (import.meta.env.DEV && !binding && env.CONNECTORS) {
      const preview = env.CONNECTORS;
      const expiresAt = Date.now() + 60_000;
      binding = {
        async getContext() {
          if (Date.now() >= expiresAt) return { status: "request_context_expired" };
          return preview.getContext?.() ?? { status: "binding_unavailable" };
        },
        async invoke(connectorId, actionName, args) {
          if (Date.now() >= expiresAt) {
            return { status: "request_context_expired", message: "This request has expired. Please try again." };
          }
          return preview.invoke(connectorId, actionName, args);
        },
      };
    }
    return runWithConnectorBinding(binding, () => handler.fetch(request, env, ctx));
  },
};
