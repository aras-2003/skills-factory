"""Executable source checks for the worked #766 multi-consumer decision."""

import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest
from unittest.mock import patch


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
    "adapters/skills-factory-cloud-next/scripts/check-contracts.mjs",
    "adapters/skills-factory-cloud-next/src/cloud-tools.ts",
    "docs/architecture/decisions/2026-11-load-skill-source-pin.md",
    "docs/governance/CODEX-SUBAGENT-PILOT.md",
    "scripts/engineering/delegation_handoff.py",
    "scripts/engineering/developer_scope.py",
    "tests/test_developer_scope.py",
    "tests/governance/test_sdlc_architecture_source_example.py",
    "tests/test_delegation_handoff.py",
)
SUCCESSOR_DELTA_SHA256 = {
    "runtime/contracts/mcp-tools-v1.json": "972f2051373d3617d7d8229f1aeeaed7a23ecf960be87e09b7077a25b398d4b7",
    "adapters/skills-factory-cloud-next/src/cloud-tools.ts": "96a304438bb9f2ce59ce875220ffc43329efcb15f84a7f866aa42377ad155d81",
    "sites/skills-factory-site/app/page.tsx": "d948900f4b75c4c4b28956442ba5788e0431e886ddf7f0464a8e9a5455eeac2c",
    "sites/skills-factory-site/build/sites-worker.ts": "316c8a61ee8f319757638600a41a8ea03ed760b48a94670a427fd1d74e9a7f34",
}
SUCCESSOR_SUPPORT_SHA256 = {
    "sites/skills-factory-site/lib/site-version-metadata.ts": "620c05cee291e0ebb3cdbef1e0b270f5c55db907df64e52feffb4dd3763759fa",
}
APPROVED_REFRESHED_SOURCE_SHA256 = {
    "adapters/skills-factory-cloud-next/scripts/check-contracts.mjs": "55591650298c304b8d5df8cd46390f8d2c1fff5b62264e67d360805380c2b699",
    "adapters/skills-factory-cloud-next/src/cloud-tools.ts": SUCCESSOR_DELTA_SHA256[
        "adapters/skills-factory-cloud-next/src/cloud-tools.ts"
    ],
    "scripts/engineering/delegation_handoff.py": "afce4a42c6da52c4d95efc68a38becc6443eeebcb77911d2734af71a523529b8",
    "scripts/engineering/developer_scope.py": "ee2c765e22b47ddfdaaa9a51b92f9fb56d8829be23285ed40b21a24c8ab99496",
    "tests/test_developer_scope.py": "c860db45d5073d0d5f14a6b245a0119805180b6f34944e9c7deae9ba96b35b89",
    "docs/governance/CODEX-SUBAGENT-PILOT.md": "e3ca2df547e4277a092260003baea9f2dd8de14d4a8b815342a2d6e6c94a32fe",
    "tests/test_delegation_handoff.py": "f4e4da504f11e8d201addb7a47e0726b7b7e6895c0e960f829a9a8564dbd7ae9",
}
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
        approved = APPROVED_REFRESHED_SOURCE_SHA256.get(path)
        if approved is not None and digest.decode() != approved:
            raise AssertionError(f"unapproved refreshed source digest: {path}")
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
                elif path in SUCCESSOR_DELTA_SHA256:
                    self.assertEqual(SUCCESSOR_DELTA_SHA256[path], hashlib.sha256(current_bytes).hexdigest(),
                                     f"unreviewed successor delta: {path}")
                    continue
                self.assertEqual(reviewed_bytes, current_bytes,
                                 f"consumer-map source differs from reviewed commit: {path}")

        for path, expected_digest in SUCCESSOR_SUPPORT_SHA256.items():
            with self.subTest(successor_support=path):
                self.assertEqual(expected_digest, hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
                                 f"unreviewed successor support source: {path}")

        contract = json.loads((ROOT / "runtime/contracts/mcp-tools-v1.json").read_text(encoding="utf-8"))
        reviewed_contract = json.loads(source_at(revision, "runtime/contracts/mcp-tools-v1.json"))
        self.assertEqual(reviewed_contract["tools"], contract["tools"], "shared MCP tool contract changed")
        self.assertEqual(["skill_name"], contract["tools"]["load_skill"])
        self.assertEqual({"evaluate_investment_decision_fixture": ["expected_source_revision", "fixture_id"]},
                         contract.get("cloud_next_extensions"))

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

    def test_handoff_parser_source_refresh_is_exact_and_approved(self):
        baseline = subprocess.check_output(
            ["git", "--no-replace-objects", "show", f"{EXPECTED_CONSUMER_MAP}:{CONTINUATION_PATH}"],
            cwd=ROOT,
        )
        current = (ROOT / CONTINUATION_PATH).read_bytes()
        handoff_paths = (
            "scripts/engineering/delegation_handoff.py",
            "tests/test_delegation_handoff.py",
        )

        self.assertEqual(len(REFRESHED_DIGEST_PATHS), len(set(REFRESHED_DIGEST_PATHS)))
        self.assertEqual(baseline, normalize_continuation(current, baseline, ROOT))
        for path in handoff_paths:
            with self.subTest(path=path):
                digest = hashlib.sha256((ROOT / path).read_bytes()).hexdigest().encode()
                pattern = re.compile(rb"(?m)^  " + re.escape(path.encode()) + rb": ([0-9a-f]{64})$")
                matches = list(pattern.finditer(current))
                self.assertEqual(1, len(matches))
                stale = current[:matches[0].start(1)] + b"0" * 64 + current[matches[0].end(1):]
                with self.assertRaisesRegex(AssertionError, "continuation digest does not match source"):
                    normalize_continuation(stale, baseline, ROOT)
                self.assertEqual(APPROVED_REFRESHED_SOURCE_SHA256[path].encode(), digest)
                with patch.dict(APPROVED_REFRESHED_SOURCE_SHA256, {path: "0" * 64}):
                    with self.assertRaisesRegex(AssertionError, "unapproved refreshed source digest"):
                        normalize_continuation(current, baseline, ROOT)

    def test_subagent_runbook_refresh_is_exact_and_approved(self):
        baseline = subprocess.check_output(
            ["git", "--no-replace-objects", "show", f"{EXPECTED_CONSUMER_MAP}:{CONTINUATION_PATH}"],
            cwd=ROOT,
        )
        current = (ROOT / CONTINUATION_PATH).read_bytes()
        path = "docs/governance/CODEX-SUBAGENT-PILOT.md"
        digest = hashlib.sha256((ROOT / path).read_bytes()).hexdigest().encode()
        pattern = re.compile(rb"(?m)^  " + re.escape(path.encode()) + rb": ([0-9a-f]{64})$")
        matches = list(pattern.finditer(current))
        self.assertEqual(1, len(matches))
        stale = current[:matches[0].start(1)] + b"0" * 64 + current[matches[0].end(1):]
        with self.assertRaisesRegex(AssertionError, "continuation digest does not match source"):
            normalize_continuation(stale, baseline, ROOT)
        self.assertEqual(APPROVED_REFRESHED_SOURCE_SHA256[path].encode(), digest)
        with patch.dict(APPROVED_REFRESHED_SOURCE_SHA256, {path: "0" * 64}):
            with self.assertRaisesRegex(AssertionError, "unapproved refreshed source digest"):
                normalize_continuation(current, baseline, ROOT)

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
