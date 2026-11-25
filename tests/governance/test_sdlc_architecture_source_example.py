"""Executable source checks for the worked #766 multi-consumer decision."""

import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
DECISION = ROOT / "docs/architecture/decisions/2026-11-load-skill-source-pin.md"
BASELINE_RE = re.compile(r"^- Baseline source SHA: `([0-9a-f]{40})`$", re.MULTILINE)
EXPECTED_BASELINE = "e0f613cbaf80cf4a278e713794662250dab2b8bc"
CONSUMER_MAP_RE = re.compile(
    r"^- Current consumer-map source SHA: `([0-9a-f]{40})`\.$", re.MULTILINE
)
EXPECTED_CONSUMER_MAP = "242fe4762d2b2c6cc2c602720d222e1276c0cd17"
CONTINUATION_PATH = "evals/campaigns/iteration-07-investing-quality-2026-11/sdlc-source-compatibility-continuation.yaml"
REFRESHED_DIGEST_PATHS = (
    "docs/architecture/decisions/2026-11-load-skill-source-pin.md",
    "tests/governance/test_sdlc_architecture_source_example.py",
)
CONSUMER_MAP_PATHS = (
    "runtime/contracts/mcp-tools-v1.json",
    "runtime/mcp/server.py",
    "runtime/mcp/skill_catalog.py",
    "runtime/mcp/cloud_server.py",
    "adapters/skills-factory-cloud-next/src/mcp-handler.ts",
    "adapters/skills-factory-cloud-next/src/cloud-tools.ts",
    "sites/skills-factory-site/app/mcp/route.ts",
    "sites/skills-factory-site/app/page.tsx",
    "docs/REMOTE-MCP.md",
    "scripts/eval/iteration02_flow_capture.py",
    "scripts/eval/iteration02_route_evidence.py",
    "adapters/skills-factory-cloud-next/scripts/sync-lab-catalog.py",
    "scripts/package/build_cloud_next_site.py",
    "scripts/package/build_utils.py",
    "scripts/package/build_plugin.py",
    "plugins/skills-factory-lab/.codex-plugin/plugin.json",
    "plugins/skills-factory-lab/.mcp.json",
    "plugins/skills-factory-lab/release-manifest.json",
    "plugins/skills-factory-lab/mcp/server.py",
    "plugins/skills-factory-lab/mcp/skill_catalog.py",
    "sites/skills-factory-site/build/sites-worker.ts",
    "sites/skills-factory-site/vite.config.ts",
    "sites/skills-factory-site/scripts/sync-site-source.mjs",
    "adapters/skills-factory-cloud-next/src/tool-receipt.ts",
    "scripts/package/build_lab_plugin.py",
    "docs/catalog.json",
    "workflows/runtime-registry.yaml",
    "runtime/mcp/investment_runtime.py",
    "scripts/eval/iteration02_site_native_receipt.py",
    "scripts/eval/campaign.py",
    CONTINUATION_PATH,
    "scripts/eval/promptfoo/promptfooconfig.yaml",
    "scripts/eval/prepare_closure.py",
    "scripts/eval/release_bundle.py",
)


def normalize_continuation(current: bytes, reviewed: bytes, root: Path) -> bytes:
    """Permit only exact, verified refreshes of the two self-referential digests."""
    for path in REFRESHED_DIGEST_PATHS:
        pattern = re.compile(rb"(?m)^  " + re.escape(path.encode()) + rb": ([0-9a-f]{64})$")
        current_matches = list(pattern.finditer(current))
        reviewed_matches = list(pattern.finditer(reviewed))
        if len(current_matches) != 1 or len(reviewed_matches) != 1:
            raise AssertionError(f"expected one digest entry for {path}")
        digest = hashlib.sha256((root / path).read_bytes()).hexdigest().encode()
        if current_matches[0].group(1) != digest:
            raise AssertionError(f"continuation digest does not match source: {path}")
        start, end = current_matches[0].span(1)
        current = current[:start] + reviewed_matches[0].group(1) + current[end:]
    return current


def source_at(revision: str, path: str) -> str:
    return subprocess.check_output(
        ["git", "--no-replace-objects", "show", f"{revision}:{path}"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    )


class ArchitectureSourceExampleTests(unittest.TestCase):
    def test_current_consumer_map_is_pinned_to_reviewed_source_bytes(self):
        self.assertEqual(34, len(CONSUMER_MAP_PATHS))
        self.assertEqual(len(CONSUMER_MAP_PATHS), len(set(CONSUMER_MAP_PATHS)))
        decision = DECISION.read_text(encoding="utf-8")
        matches = CONSUMER_MAP_RE.findall(decision)
        self.assertEqual(1, len(matches), "decision must carry one exact consumer-map source SHA")
        revision = matches[0]
        self.assertEqual(EXPECTED_CONSUMER_MAP, revision)
        self.assertEqual(
            revision,
            subprocess.check_output(
                ["git", "--no-replace-objects", "rev-parse", "--verify", "--end-of-options", f"{revision}^{{commit}}"],
                cwd=ROOT,
                text=True,
            ).strip(),
        )
        subprocess.check_call(
            ["git", "--no-replace-objects", "merge-base", "--is-ancestor", revision, "HEAD"],
            cwd=ROOT,
        )

        for path in CONSUMER_MAP_PATHS:
            with self.subTest(path=path):
                try:
                    reviewed_bytes = subprocess.check_output(
                        ["git", "--no-replace-objects", "show", f"{revision}:{path}"],
                        cwd=ROOT,
                    )
                    current_bytes = (ROOT / path).read_bytes()
                except (OSError, subprocess.CalledProcessError) as error:
                    self.fail(f"consumer-map source could not be verified for {path}: {error}")
                if path == CONTINUATION_PATH:
                    current_bytes = normalize_continuation(current_bytes, reviewed_bytes, ROOT)
                self.assertEqual(
                    reviewed_bytes,
                    current_bytes,
                    f"consumer-map source differs from reviewed commit: {path}",
                )

    def test_continuation_refresh_rejects_stale_digest_and_unrelated_changes(self):
        baseline = subprocess.check_output(
            ["git", "--no-replace-objects", "show", f"{EXPECTED_CONSUMER_MAP}:{CONTINUATION_PATH}"],
            cwd=ROOT,
        )
        current = (ROOT / CONTINUATION_PATH).read_bytes()
        self.assertEqual(baseline, normalize_continuation(current, baseline, ROOT))
        first = REFRESHED_DIGEST_PATHS[0]
        digest = hashlib.sha256((ROOT / first).read_bytes()).hexdigest().encode()
        with self.assertRaises(AssertionError):
            normalize_continuation(current.replace(digest, b"0" * 64, 1), baseline, ROOT)
        with self.assertRaises(AssertionError):
            normalize_continuation(current + b"  " + first.encode() + b": " + digest + b"\n", baseline, ROOT)
        self.assertNotEqual(
            baseline,
            normalize_continuation(
                current.replace(b"state: INTEGRATION_ISOLATED", b"state: ALTERED", 1), baseline, ROOT
            ),
        )

    def test_rollback_requires_caller_compatibility_before_reverting_v1_schema(self):
        decision = DECISION.read_text(encoding="utf-8")
        self.assertIn("## Rollback boundary", decision)
        self.assertRegex(
            decision,
            r"(?is)rollback boundary.*?before any caller sends `expected_source_revision`.*?"
            r"callers? must stop sending the field.*?server must never silently ignore.*?"
            r"exact error shape for invalid or stale revisions remains owner-gated",
        )

    def test_arch02_and_arch03_example_matches_two_pinned_backend_contracts(self):
        decision = DECISION.read_text(encoding="utf-8")
        match = BASELINE_RE.search(decision)
        self.assertIsNotNone(match, "decision must carry an exact baseline SHA")
        baseline = match.group(1)
        self.assertEqual(EXPECTED_BASELINE, baseline)
        self.assertEqual(
            baseline,
            subprocess.check_output(
                ["git", "--no-replace-objects", "rev-parse", "--verify", "--end-of-options", f"{baseline}^{{commit}}"],
                cwd=ROOT,
                text=True,
            ).strip(),
        )

        contract_path = "runtime/contracts/mcp-tools-v1.json"
        contract = json.loads(source_at(baseline, contract_path))
        self.assertEqual(["skill_name"], contract["tools"]["load_skill"])
        self.assertIn(f"{contract_path}#L6-L8", decision)

        python_server_path = "runtime/mcp/server.py"
        python_server = source_at(baseline, python_server_path)
        self.assertIn('def load_skill(skill_name: str', python_server)
        self.assertIn('"load_skill", {"skill_name": skill_name}', python_server)
        self.assertIn(f"{python_server_path}#L297-L303", decision)

        package_path = "runtime/mcp/skill_catalog.py"
        package = source_at(baseline, package_path)
        self.assertIn('def load_skill(skill_name: str)', package)
        self.assertIn('"source_revision": packaged_runtime_value("source_revision")', package)
        self.assertIn(f"{package_path}#L237-L272", decision)

        cloud_path = "adapters/skills-factory-cloud-next/src/cloud-tools.ts"
        cloud = source_at(baseline, cloud_path).splitlines()
        self.assertEqual(
            '  load_skill: z.object({ skill_name: z.string().trim().min(1).max(160) }).strict(),',
            cloud[27],
        )
        self.assertTrue(any('name: "load_skill"' in line and 'required: ["skill_name"]' in line
                            for line in cloud[125:131]))
        self.assertTrue(any("export function loadSkill(skillName: string)" in line for line in cloud))
        self.assertIn(f"{cloud_path}#L25-L29", decision)
        self.assertIn("#L182-L186", decision)
        self.assertIn("cloud-tools.ts#L128-L130", decision)
        self.assertIn("Status: `REVIEW_REQUIRED`", decision)
        self.assertIn("Candidate SHA: `NOT_CREATED`", decision)
        self.assertIn("`ARCH-02` remains `NOT_RUN`", decision)

    def test_current_consumer_map_covers_runtime_ui_evidence_and_catalog_builders(self):
        decision = DECISION.read_text(encoding="utf-8")
        self.assertIn("## Reuse decision", decision)
        self.assertIn("docs/architecture/SOFTWARE-ARCHITECTURE-DECISIONS.md", decision)
        self.assertIn("templates/architecture/software-decision.md", decision)
        current_map = decision.split("## Current source consumer map", 1)[1].split(
            "## Migration, verification, and rollback", 1
        )[0]
        for path in CONSUMER_MAP_PATHS:
            with self.subTest(path=path):
                self.assertIn(path, current_map)
                self.assertTrue((ROOT / path).is_file())

        browser = (ROOT / "sites/skills-factory-site/app/page.tsx").read_text(encoding="utf-8")
        self.assertIn("context.registerTool", browser)
        self.assertIn("callTool(name, args)", browser)
        self.assertIn("callTool(name, JSON.parse(input))", browser)
        self.assertIn('load_skill: { skill_name: "skill-test-design" }', browser)
        self.assertIn("TOOLS.find", browser)

        python_server = (ROOT / "runtime/mcp/server.py").read_text(encoding="utf-8")
        python_wrapper = (ROOT / "runtime/mcp/cloud_server.py").read_text(encoding="utf-8")
        cloud_tools = (ROOT / "adapters/skills-factory-cloud-next/src/cloud-tools.ts").read_text(encoding="utf-8")
        site_route = (ROOT / "sites/skills-factory-site/app/mcp/route.ts").read_text(encoding="utf-8")
        cloud_handler = (ROOT / "adapters/skills-factory-cloud-next/src/mcp-handler.ts").read_text(encoding="utf-8")
        site_builder = (ROOT / "scripts/package/build_cloud_next_site.py").read_text(encoding="utf-8")
        self.assertIn('"load_skill"', python_server)
        self.assertIn('transport="streamable-http"', python_wrapper)
        self.assertIn("expected_source_revision", cloud_tools)
        self.assertIn("handleMcp", site_route)
        self.assertIn('request.method !== "POST"', cloud_handler)
        self.assertIn("{ status: 405", cloud_handler)
        self.assertIn("sync-lab-catalog.py", site_builder)
        self.assertIn("app = mcp.streamable_http_app()", python_server)

        flow_capture = (ROOT / "scripts/eval/iteration02_flow_capture.py").read_text(encoding="utf-8")
        route_evidence = (ROOT / "scripts/eval/iteration02_route_evidence.py").read_text(encoding="utf-8")
        self.assertIn('verify_call(provider, "load_skill", identity["source_revision"])', flow_capture)
        self.assertIn('verify_call(child, "load_skill", receipt_source)', route_evidence)
        self.assertIn("child model execution cannot be inferred from load_skill", route_evidence)

        catalog_builder = (ROOT / "adapters/skills-factory-cloud-next/scripts/sync-lab-catalog.py").read_text(encoding="utf-8")
        self.assertIn("m.load_skill(entry['name'])", catalog_builder)
        self.assertIn("expected_source_revision", current_map)
        self.assertIn("External HTTP/MCP clients", current_map)
        self.assertIn("tools/list", current_map)
        self.assertIn("observed stale-pin rejection", current_map)
        self.assertIn("do not send a pin", current_map)

        plugin_manifest = json.loads((ROOT / "plugins/skills-factory-lab/.codex-plugin/plugin.json").read_text(encoding="utf-8"))
        plugin_mcp = json.loads((ROOT / "plugins/skills-factory-lab/.mcp.json").read_text(encoding="utf-8"))
        plugin_release = json.loads((ROOT / "plugins/skills-factory-lab/release-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("1.38.477", plugin_manifest["version"])
        self.assertEqual("1.38.477+d43250f3982f", plugin_release["release_id"])
        self.assertEqual("d43250f3982f9ea6ae7b5eb4112922135a7add05", plugin_release["source_revision"])
        self.assertEqual("./.mcp.json", plugin_manifest["mcpServers"])
        self.assertIn("${PLUGIN_ROOT}/mcp/server.py", plugin_mcp["mcpServers"]["skills-factory-runtime"]["args"])
        stale_server = (ROOT / "plugins/skills-factory-lab/mcp/server.py").read_text(encoding="utf-8")
        stale_catalog = (ROOT / "plugins/skills-factory-lab/mcp/skill_catalog.py").read_text(encoding="utf-8")
        self.assertIn("def load_skill(skill_name: str, context: Context = None)", stale_server)
        self.assertIn("def load_skill(skill_name: str)", stale_catalog)
        self.assertNotIn("expected_source_revision", stale_server + stale_catalog)

        build_utils = (ROOT / "scripts/package/build_utils.py").read_text(encoding="utf-8")
        self.assertIn('source_dir = root / "runtime" / "mcp"', build_utils)
        self.assertIn("shutil.copyfile(server_src, mcp_out / \"server.py\")", build_utils)
        self.assertIn("shutil.copyfile(catalog_src, mcp_out / \"skill_catalog.py\")", build_utils)


if __name__ == "__main__":
    unittest.main()
