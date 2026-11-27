export type SiteVersionMetadata = {
  id?: string | null;
  tag?: string | null;
  timestamp?: string | number | null;
  source?: "cloudflare_version_metadata" | "site_environment";
};

export type SiteMetadataEnvironment = {
  CF_VERSION_METADATA?: SiteVersionMetadata;
  SKILLS_FACTORY_RELEASE_ID?: string;
  SKILLS_FACTORY_SOURCE_REVISION?: string;
  SKILLS_FACTORY_DEPLOYED_AT?: string;
};

/** Keep the MCP route and server-side Site readers on the same identity inputs. */
export function resolveSiteVersionMetadata(environment: SiteMetadataEnvironment): SiteVersionMetadata | undefined {
  const platform = environment.CF_VERSION_METADATA;
  const configured = environment.SKILLS_FACTORY_RELEASE_ID || environment.SKILLS_FACTORY_SOURCE_REVISION || environment.SKILLS_FACTORY_DEPLOYED_AT
    ? {
        id: environment.SKILLS_FACTORY_RELEASE_ID,
        tag: environment.SKILLS_FACTORY_SOURCE_REVISION,
        timestamp: environment.SKILLS_FACTORY_DEPLOYED_AT,
        source: "site_environment" as const,
      }
    : undefined;

  return platform?.id || platform?.tag || platform?.timestamp
    ? {
        id: platform.id || configured?.id,
        tag: platform.tag || configured?.tag,
        timestamp: platform.timestamp || configured?.timestamp,
        source: "cloudflare_version_metadata",
      }
    : configured;
}
