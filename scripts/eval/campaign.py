from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
PACKAGE_DIR = ROOT / "scripts" / "package"
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from common import load_campaign_cases, load_supplemental_cases, sha256_file
import receipt
import validate_routing
import build_plugin
import artifact_validation

CONFIG_REL = Path("evals/campaigns/runtime-validation-2026-10-r19/campaign.yaml")
CONFIG = ROOT / CONFIG_REL
SEPARATE_META_CAMPAIGN_REL = Path("evals/campaigns/skill-release-review-2026-10/release-review-campaign.yaml")
SKILL_ENGINEERING_CAMPAIGN_REL = Path("evals/campaigns/skill-engineering-2026-10/engineering-campaign.yaml")


def separately_validated_engineering_paths() -> set[str]:
    """Return behavior paths covered by the exact, repository-validated engineering campaign."""
    path = ROOT / SKILL_ENGINEERING_CAMPAIGN_REL
    if not path.is_file():
        return set()
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    declared = cfg.get("out_of_scope_behavior_paths") or []
    expected = {
        "skills/meta/skill-test-design/SKILL.md",
        "skills/meta/skill-evaluation/SKILL.md",
        "workflows/skill-development/WORKFLOW.md",
        "release/package.yaml",
    }
    if cfg.get("campaign") != "skill-engineering-2026-10" or set(declared) != expected:
        return set()
    fixtures = yaml.safe_load((ROOT / "evals/runtime-fixtures.yaml").read_text(encoding="utf-8")) or {}
    targets = fixtures.get("targets") or {}
    declared_targets = cfg.get("runtime_targets") or {}
    for target in ("skill-test-design", "skill-evaluation"):
        skill = ROOT / f"skills/meta/{target}/SKILL.md"
        declared = declared_targets.get(target) or {}
        version = str(declared.get("version") or "")
        if not version or not skill.is_file() or f'version: "{version}"' not in skill.read_text(encoding="utf-8"):
            return set()
        fixture_cases = targets.get(target) or []
        fixture_ids = {str(case.get("id")) for case in fixture_cases}
        if set(declared.get("required_cases") or []) != fixture_ids:
            return set()
        if len(fixture_cases) < 2:
            return set()
        for case in fixture_cases:
            if not (ROOT / str(case.get("input") or "")).is_file() or not (ROOT / str(case.get("rubric") or "")).is_file():
                return set()
    workflow = ROOT / "workflows/skill-development"
    workflow_cases = workflow / "tests/cases.yaml"
    if not (workflow / "WORKFLOW.md").is_file() or not workflow_cases.is_file():
        return set()
    cases_doc = yaml.safe_load(workflow_cases.read_text(encoding="utf-8")) or {}
    repo_workflow = cfg.get("repository_workflow") or {}
    if (
        repo_workflow.get("path") != "workflows/skill-development/WORKFLOW.md"
        or repo_workflow.get("test_cases") != "workflows/skill-development/tests/cases.yaml"
        or len(cases_doc.get("cases") or []) < int(repo_workflow.get("minimum_cases") or 0)
    ):
        return set()
    package = yaml.safe_load((ROOT / "release/package.yaml").read_text(encoding="utf-8")) or {}
    lab = package.get("lab") or {}
    package_cfg = cfg.get("package") or {}
    required_drafts = package_cfg.get("required_draft_targets") or []
    if (
        package_cfg.get("lab_version_source") != "release/package.yaml#lab.version"
        or not isinstance(lab.get("version"), str)
        or not lab.get("version")
        or set(lab.get("draft_test_targets") or []) != set(required_drafts)
    ):
        return set()
    return expected


def config(root: Path = ROOT):
    return yaml.safe_load((root / CONFIG_REL).read_text(encoding="utf-8")) or {}


def filter_behavior_paths(paths: list[str], separately_validated: set[str]) -> list[str]:
    return [path for path in paths if path not in separately_validated]


def behavior_changes(pinned: str, *, require_commit: bool = False) -> list[str]:
    exists = subprocess.run(
        ["git", "cat-file", "-e", pinned + "^{commit}"],
        cwd=ROOT, check=False, capture_output=True, text=True,
    )
    if exists.returncode:
        if require_commit:
            raise ValueError(f"pinned behavior commit is unavailable in this checkout: {pinned}")
        return []
    out = subprocess.check_output(
        ["git", "diff", "--name-only", pinned, "HEAD", "--", "skills", "workflows", "release/package.yaml"],
        cwd=ROOT, text=True,
    ).strip()
    changed = []
    separate_meta_targets = set()
    separate_meta_cfg = ROOT / SEPARATE_META_CAMPAIGN_REL
    if separate_meta_cfg.is_file():
        meta = yaml.safe_load(separate_meta_cfg.read_text(encoding="utf-8")) or {}
        meta_skill = ROOT / "skills/meta/skill-release-review/SKILL.md"
        expected_paths = ["skills/meta/skill-release-review/SKILL.md"]
        if (
            meta.get("campaign") == "skill-release-review-2026-10"
            and meta.get("target") == "skill-release-review"
            and meta.get("out_of_scope_behavior_paths") == expected_paths
            and meta_skill.is_file()
            and f'version: "{meta.get("candidate_version")}"' in meta_skill.read_text(encoding="utf-8")
        ):
            separate_meta_targets = set(expected_paths)
    separate_meta_targets.update(separately_validated_engineering_paths())
    for raw in out.splitlines():
        path = raw.strip()
        if not path:
            continue
        parts = Path(path).parts
        if "tests" in parts or "evals" in parts:
            continue
        if Path(path).name.lower().startswith("readme"):
            continue
        # R16's broad pin intentionally remains intact. A behavior path may be
        # outside its scope only when a separate, dedicated campaign declares
        # and validates that exact path.
        changed.append(path)
    return filter_behavior_paths(changed, separate_meta_targets)


def explicit_fallback_input_errors(case: dict, input_text: str) -> list[str]:
    if case.get("suite") != "production-fallback" or case.get("mode") != "explicit":
        return []
    target = str(case.get("target") or "").strip()
    if not target:
        return ["explicit production fallback has no target"]
    if target.lower() not in input_text.lower():
        return [f"explicit production fallback input must name target workflow {target}"]
    return []


def validate_campaign() -> list[str]:
    errors = []
    cfg = config()
    cases = load_campaign_cases(ROOT, config()["campaign"])
    expected = {"commerce": 6, "routing": 22, "executive-role": 14}
    counts = {k: 0 for k in expected}
    known = validate_routing.known_capability_names(ROOT)

    if len(cases) != 42:
        errors.append(f"expected 42 Lab core cases, got {len(cases)}")

    if cfg.get("execution_channel") != "lab":
        errors.append("Active campaign execution_channel must be lab")
    excluded = {str(item.get("id")) for item in cfg.get("excluded_production_only_cases") or [] if isinstance(item, dict)}
    active_production_fallbacks = {cid for cid, case in cases.items() if case.get("suite") == "production-fallback"}
    if active_production_fallbacks:
        errors.append("Production-only fallback cases cannot run in the Lab campaign: " + ", ".join(sorted(active_production_fallbacks)))
    expected_excluded = {"fallback-strategy-production-002", "fallback-interface-explicit-production-002"}
    if excluded != expected_excluded:
        errors.append("Active campaign must preserve both Production-only fallback IDs in excluded_production_only_cases")

    for cid, case in cases.items():
        suite = str(case.get("suite") or "")
        if suite not in counts:
            errors.append(f"{cid}: unknown suite {suite}")
            continue
        counts[suite] += 1
        ip = ROOT / str(case.get("input") or "")
        rp = ROOT / str(case.get("rubric") or "")
        if not ip.is_file() or not ip.name.endswith(".input.md"):
            errors.append(f"{cid}: missing/invalid executor input")
            continue
        if not rp.is_file() or not rp.name.endswith(".rubric.yaml"):
            errors.append(f"{cid}: missing/invalid evaluator rubric")
            continue
        input_text = ip.read_text(encoding="utf-8")
        if case.get("mode") == "natural-routing":
            leaked = validate_routing.leaked_capabilities(input_text, known)
            if leaked:
                errors.append(f"{cid}: executor input leaks capability names: {', '.join(leaked)}")
        for error in explicit_fallback_input_errors(case, input_text):
            errors.append(f"{cid}: {error}")

    for suite, count in expected.items():
        if counts[suite] != count:
            errors.append(f"{suite}: expected {count}, got {counts[suite]}")

    supplemental = load_supplemental_cases(ROOT, config()["campaign"])
    expected_supplemental = len(cfg.get("supplemental_routing_case_ids") or [])
    if len(supplemental) != expected_supplemental:
        errors.append(
            f"supplemental routing: expected {expected_supplemental} cases, got {len(supplemental)}"
        )
    for cid, case in supplemental.items():
        ip = ROOT / str(case.get("input") or "")
        rp = ROOT / str(case.get("rubric") or "")
        if not ip.is_file() or not ip.name.endswith(".input.md"):
            errors.append(f"{cid}: missing/invalid supplemental executor input")
            continue
        if not rp.is_file() or not rp.name.endswith(".rubric.yaml"):
            errors.append(f"{cid}: missing/invalid supplemental evaluator rubric")
            continue
        leaked = validate_routing.leaked_capabilities(ip.read_text(encoding="utf-8"), known)
        if leaked:
            errors.append(f"{cid}: supplemental input leaks capability names: {', '.join(leaked)}")

    source = yaml.safe_load((ROOT / cfg["executive_source"]).read_text(encoding="utf-8")) or {}
    source_by_id = {str(x["id"]): x for x in source.get("cases", []) if isinstance(x, dict) and x.get("id")}
    for cid in cfg.get("executive_case_ids", []):
        case = cases.get(cid)
        original = source_by_id.get(cid)
        if not case or not original:
            errors.append(f"{cid}: missing split/source case")
            continue
        split_input = (ROOT / case["input"]).read_text(encoding="utf-8").strip()
        if split_input != str(original.get("input") or "").strip():
            errors.append(f"{cid}: executor split drifted from source")
        rub = yaml.safe_load((ROOT / case["rubric"]).read_text(encoding="utf-8")) or {}
        exp = original.get("expected") or {}
        if rub.get("should_trigger") != exp.get("should_trigger"):
            errors.append(f"{cid}: should_trigger drift")
        if list((rub.get("assertions") or {}).get("manual") or []) != list(exp.get("must") or []):
            errors.append(f"{cid}: must assertion drift")
        if list((rub.get("assertions") or {}).get("manual_not") or []) != list(exp.get("must_not") or []):
            errors.append(f"{cid}: must_not assertion drift")

    pinned = str(cfg.get("behavior_source_revision") or "")
    pinned_exists = bool(pinned) and subprocess.run(
        ["git", "cat-file", "-e", pinned + "^{commit}"],
        cwd=ROOT, check=False, capture_output=True, text=True,
    ).returncode == 0
    if not pinned:
        errors.append("behavior_source_revision is missing")
    elif not pinned_exists:
        errors.append(
            "behavior_source_revision is unavailable in this checkout; pin a reachable commit "
            "from the target branch (squash merges can discard PR-only SHAs): " + pinned
        )
    else:
        changed = behavior_changes(pinned, require_commit=False)
        if changed:
            errors.append("behavior changed after pinned SHA: " + ", ".join(changed))
    return errors


def ordered_cases(include_supplemental: bool = False):
    cfg = config()
    rank = {name: i for i, name in enumerate(cfg.get("execution_order", []))}
    cases = list(load_campaign_cases(ROOT, config()["campaign"]).values())
    if include_supplemental:
        cases.extend(load_supplemental_cases(ROOT, config()["campaign"]).values())
    return sorted(cases, key=lambda x: (rank.get(x.get("suite"), 98 if x.get("suite") == "supplemental-routing" else 99), x["id"]))


def queue_text(include_supplemental: bool = False) -> str:
    out = [
        "# Runtime validation queue",
        "",
        "Executor-only inputs. Never provide the referenced rubric to the executor session.",
        "",
    ]
    for i, case in enumerate(ordered_cases(include_supplemental), 1):
        prompt = (ROOT / case["input"]).read_text(encoding="utf-8").rstrip()
        out += [
            f"## {i:02d}. {case['id']}",
            f"- suite: {case['suite']}",
            f"- subject: {case['target']}",
            f"- mode: {case['mode']}",
            "",
            "~~~text",
            prompt,
            "~~~",
            "",
        ]
    return "\n".join(out)


LOCK_SCHEMA_VERSION = "2.0"
HISTORICAL_RECEIPT_COMPATIBILITY = {
    "ff012e494f5b2f71803f850d71d20f54a3315e2b": "runtime-validation-2026-10",
    "c0772e2e3727971b2e3fe8f9d56eccf6bdd87129": "runtime-validation-2026-10-r2",
    "cde46f59c20a0d4313528185e5df079335633b10": "runtime-validation-2026-10-r3",
    "28a7681cf024bb7aaad7a979e7ce7253139d5bd4": "runtime-validation-2026-10-r4",
    "a5c4001d28f45d3fb799f07a2c880f406f58cc65": "runtime-validation-2026-10-r5",
    "a924f3ba9fe964ff3aeaa2e5570b7a718d29d38c": "runtime-validation-2026-10-r6",
    "008c9944cf3a8bc3e2d7231a4862aaf00e722889": "runtime-validation-2026-10-r7",
    "6a598a036133284852c1dcb9f295aaefbb69686d": "runtime-validation-2026-10-r8",
    "e301e7af458a2fb2461c7576960ba8415bf3435f": "runtime-validation-2026-10-r9",
    "0900bca7816341b1727285669fac88148ebc4174": "runtime-validation-2026-10-r10",
    "5a9968dc72fb21d2f36e4b9dbc76642cb11916a0": "runtime-validation-2026-10-r11",
    "63fd3fda0ab4931cc0652f0565aa29fc59b3b67d": "runtime-validation-2026-10-r12",
    "22219cae549a0588e08a887675f8cfc3c6758745": "runtime-validation-2026-10-r13",
    "a21dc626afe744bfb48dd96e29b9c7bda7cddf19": "runtime-validation-2026-10-r14",
    "9c66f5987afbd5717047d0a5107383c0b75df73d": "runtime-validation-2026-10-r15",
}


def current_case_definitions(root: Path = ROOT) -> list[dict]:
    all_cases = {**load_campaign_cases(root, config(root)["campaign"]), **load_supplemental_cases(root, config(root)["campaign"])}
    definitions = []
    for case in all_cases.values():
        input_path = root / case["input"]
        rubric_path = root / case["rubric"]
        definitions.append({
            "id": case["id"],
            "suite": case["suite"],
            "mode": case["mode"],
            "target": case["target"],
            "input_path": case["input"],
            "input_sha256": sha256_file(input_path),
            "rubric_path": case["rubric"],
            "rubric_sha256": sha256_file(rubric_path),
        })
    return sorted(definitions, key=lambda x: x["id"])


def validate_lock_data(lock: dict, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    cfg = config(root)

    required_top = {
        "schema_version",
        "campaign",
        "campaign_definition_sha256",
        "behavior_source_revision",
        "case_definitions",
        "case_channels",
        "packages",
        "expected_catalogs",
        "components",
    }
    missing = sorted(required_top - set(lock))
    if missing:
        errors.append("lock missing required fields: " + ", ".join(missing))
        return errors

    if lock.get("schema_version") != LOCK_SCHEMA_VERSION:
        errors.append(
            f"unsupported lock schema_version: {lock.get('schema_version')!r}; expected {LOCK_SCHEMA_VERSION}"
        )
    if lock.get("campaign") != cfg.get("campaign"):
        errors.append("lock campaign identity mismatch")
    if lock.get("behavior_source_revision") != cfg.get("behavior_source_revision"):
        errors.append("lock behavior source mismatch")
    if lock.get("execution_channel") != cfg.get("execution_channel"):
        errors.append("lock execution channel mismatch")
    expected_excluded = sorted(
        str(item.get("id"))
        for item in cfg.get("excluded_production_only_cases") or []
        if isinstance(item, dict) and item.get("id")
    )
    if lock.get("excluded_production_only_cases") != expected_excluded:
        errors.append("lock Production-only exclusions mismatch")

    expected_campaign_digest = sha256_file(root / CONFIG_REL)
    if lock.get("campaign_definition_sha256") != expected_campaign_digest:
        errors.append("lock campaign definition digest mismatch")

    raw_defs = lock.get("case_definitions")
    if not isinstance(raw_defs, list):
        errors.append("lock case_definitions must be a list")
        return errors

    required_case_fields = {
        "id", "suite", "mode", "target",
        "input_path", "input_sha256", "rubric_path", "rubric_sha256",
    }
    seen: set[str] = set()
    normalized: list[dict] = []
    for index, item in enumerate(raw_defs):
        if not isinstance(item, dict):
            errors.append(f"lock case_definitions[{index}] must be an object")
            continue
        missing_case = sorted(required_case_fields - set(item))
        if missing_case:
            errors.append(
                f"lock case_definitions[{index}] missing fields: {', '.join(missing_case)}"
            )
            continue
        cid = str(item.get("id"))
        if cid in seen:
            errors.append(f"lock has duplicate case definition: {cid}")
        seen.add(cid)
        normalized.append({key: item.get(key) for key in sorted(required_case_fields)})

    expected_defs = current_case_definitions(root)
    expected_by_id = {item["id"]: item for item in expected_defs}
    actual_by_id = {item["id"]: item for item in raw_defs if isinstance(item, dict) and item.get("id")}
    expected_ids = set(expected_by_id)
    actual_ids = set(actual_by_id)
    missing_ids = sorted(expected_ids - actual_ids)
    unknown_ids = sorted(actual_ids - expected_ids)
    if missing_ids:
        errors.append("lock missing case definitions: " + ", ".join(missing_ids))
    if unknown_ids:
        errors.append("lock contains unknown case definitions: " + ", ".join(unknown_ids))

    for cid in sorted(expected_ids & actual_ids):
        expected = expected_by_id[cid]
        actual = actual_by_id[cid]
        for field in (
            "suite", "mode", "target",
            "input_path", "input_sha256", "rubric_path", "rubric_sha256",
        ):
            if actual.get(field) != expected.get(field):
                errors.append(f"lock case {cid} {field} mismatch")

    channels = lock.get("case_channels")
    if not isinstance(channels, dict):
        errors.append("lock case_channels must be an object")
    else:
        channel_ids = set(channels)
        if channel_ids != expected_ids:
            missing_channels = sorted(expected_ids - channel_ids)
            unknown_channels = sorted(channel_ids - expected_ids)
            if missing_channels:
                errors.append("lock case_channels missing cases: " + ", ".join(missing_channels))
            if unknown_channels:
                errors.append("lock case_channels contains unknown cases: " + ", ".join(unknown_channels))
        required_channel = cfg.get("execution_channel")
        if required_channel and any(channel != required_channel for channel in channels.values()):
            errors.append(f"lock contains cases outside required {required_channel} channel")
        if required_channel in ("lab", "production"):
            catalog = lock.get("expected_catalogs", {}).get(required_channel, [])
            for item in raw_defs:
                if isinstance(item, dict) and item.get("target") not in catalog:
                    errors.append(
                        f"lock case {item.get('id')} target is absent from {required_channel} catalog"
                    )

    return errors


def validate_lock_file(path: Path, root: Path = ROOT) -> dict:
    try:
        lock = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"invalid lock JSON: {exc}") from exc
    if not isinstance(lock, dict):
        raise ValueError("lock must be a JSON object")
    errors = validate_lock_data(lock, root=root)
    if errors:
        raise ValueError("invalid campaign lock: " + "; ".join(errors))
    return lock


def prepare(out: Path, *, require_pinned_commit: bool = True) -> None:
    errors = validate_campaign()
    if errors:
        raise ValueError("; ".join(errors))
    cfg = config()
    pinned = cfg["behavior_source_revision"]
    changed = behavior_changes(pinned, require_commit=require_pinned_commit)
    if changed:
        raise ValueError("behavior changed after pinned SHA: " + ", ".join(changed))
    production = out / "production-plugin"
    lab = out / "lab-plugin"
    out.mkdir(parents=True, exist_ok=True)

    old = os.environ.get("SOURCE_REVISION")
    os.environ["SOURCE_REVISION"] = pinned
    try:
        build_plugin.build(ROOT, production, "production")
        env = dict(os.environ)
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/package/build_lab_plugin.py"), "--output", str(lab)],
            cwd=ROOT, env=env, check=True,
        )
    finally:
        if old is None:
            os.environ.pop("SOURCE_REVISION", None)
        else:
            os.environ["SOURCE_REVISION"] = old

    for package_path, is_lab in ((production, False), (lab, True)):
        artifact_errors = artifact_validation.validate_tree(package_path, allow_lab_evals=is_lab)
        if artifact_errors:
            raise ValueError("; ".join(artifact_errors))

    packages = {}
    catalogs = {}
    components = []
    for channel, package_path in (("production", production), ("lab", lab)):
        caps = json.loads((package_path / "capabilities.json").read_text(encoding="utf-8"))
        rel = json.loads((package_path / "release-manifest.json").read_text(encoding="utf-8"))
        plugin = json.loads((package_path / "plugin.json").read_text(encoding="utf-8"))
        by_name = {x["name"]: x for x in caps.get("capabilities", [])}
        catalogs[channel] = by_name
        packages[channel] = {
            "name": plugin.get("name"),
            "version": plugin.get("version"),
            "release_id": rel.get("release_id"),
            "source_revision": rel.get("source_revision"),
            "payload_content_sha256": rel.get("payload_content_sha256"),
        }
        for item in by_name.values():
            components.append({
                "channel": channel,
                "name": item.get("name"),
                "kind": item.get("kind"),
                "version": item.get("version"),
                "maturity": item.get("maturity"),
                "content_sha256": item.get("content_sha256"),
            })

    if config().get("execution_channel") != "lab":
        for unavailable in ("strategy-to-execution-diagnostic", "organizational-interface-review"):
            if unavailable in catalogs["production"]:
                raise ValueError(f"fallback campaign precondition changed: {unavailable} is now in production")

    all_cases = {**load_campaign_cases(ROOT, config()["campaign"]), **load_supplemental_cases(ROOT, config()["campaign"])}
    case_channels = {}
    execution_channel = config().get("execution_channel")
    if execution_channel not in (None, "lab", "production"):
        raise ValueError(f"unsupported execution_channel: {execution_channel}")
    for case in all_cases.values():
        target = case["target"]
        if execution_channel:
            if target not in catalogs[execution_channel]:
                raise ValueError(f"{case['id']} target {target} is absent from {execution_channel} catalog")
            case_channels[case["id"]] = execution_channel
        elif target in catalogs["production"]:
            case_channels[case["id"]] = "production"
        elif target in catalogs["lab"]:
            case_channels[case["id"]] = "lab"
        else:
            raise ValueError(f"campaign subject absent from both package catalogs: {target}")

    case_definitions = current_case_definitions(ROOT)

    lock = {
        "schema_version": LOCK_SCHEMA_VERSION,
        "campaign": cfg["campaign"],
        "campaign_definition_sha256": sha256_file(CONFIG),
        "behavior_source_revision": pinned,
        "execution_channel": config().get("execution_channel"),
        "excluded_production_only_cases": sorted(
            item.get("id") for item in config().get("excluded_production_only_cases") or []
        ),
        "packages": packages,
        "expected_catalogs": {name: sorted(items) for name, items in catalogs.items()},
        "case_channels": case_channels,
        "core_case_count": len(load_campaign_cases(ROOT, config()["campaign"])),
        "supplemental_case_ids": sorted(load_supplemental_cases(ROOT, config()["campaign"])),
        "case_definitions": sorted(case_definitions, key=lambda x: x["id"]),
        "components": components,
    }
    (out / "lock.json").write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "QUEUE.md").write_text(queue_text(), encoding="utf-8")
    for channel in ("production", "lab"):
        package_info = packages[channel]
        smoke = {
            "channel": channel,
            "package": {
                "name": package_info["name"],
                "version": package_info["version"],
                "release_id": None,
                "source_revision": None,
                "payload_content_sha256": None,
            },
            "components": [],
            "enabled_packages": [package_info["name"]],
            "catalog": [],
            "runtime": {
                "provider": None,
                "model_id": None,
                "reasoning": None,
                "available_tools": [],
            },
        }
        (out / f"smoke-{channel}-template.json").write_text(
            json.dumps(smoke, indent=2) + "\n", encoding="utf-8"
        )


def verify_smoke(lock_path: Path, observed_path: Path) -> list[str]:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    obs = json.loads(observed_path.read_text(encoding="utf-8"))
    errors = []
    channel = obs.get("channel")
    if channel not in lock.get("packages", {}):
        return [f"unknown smoke channel: {channel}"]
    expected_package = lock["packages"][channel]
    pkg = obs.get("package") or {}
    runtime = obs.get("runtime") or {}
    enabled = list(obs.get("enabled_packages") or [])
    catalog = list(obs.get("catalog") or [])
    observed_components = obs.get("components")
    if not isinstance(observed_components, list):
        observed_components = []

    for field in ("name", "version", "release_id", "source_revision", "payload_content_sha256"):
        value = pkg.get(field)
        if not value:
            errors.append(f"installed artifact identity is not observed: package.{field}")
        elif value != expected_package.get(field):
            errors.append(f"installed artifact identity mismatch: package.{field}")

    if expected_package["name"] not in enabled:
        errors.append(f"{channel} package is not enabled")
    if "skills-factory" in enabled and "skills-factory-lab" in enabled:
        errors.append("production and Lab are simultaneously enabled")
    if len(catalog) != len(set(catalog)):
        errors.append("observed catalog contains duplicate capability names")
    if set(catalog) != set(lock.get("expected_catalogs", {}).get(channel, [])):
        errors.append(f"observed catalog differs from locked {channel} catalog")

    expected_components = {
        x["name"]: x for x in lock.get("components", []) if x.get("channel") == channel
    }
    observed_by_name = {
        str(x.get("name")): x for x in observed_components
        if isinstance(x, dict) and x.get("name")
    }
    if set(observed_by_name) != set(expected_components):
        errors.append("observed component identity set differs from locked artifact")
    else:
        for name, expected in expected_components.items():
            observed = observed_by_name[name]
            for field in ("version", "content_sha256"):
                value = observed.get(field)
                if not value:
                    errors.append(f"installed artifact identity is not observed: component {name}.{field}")
                elif value != expected.get(field):
                    errors.append(f"installed artifact identity mismatch: component {name}.{field}")

    for field in ("provider", "model_id", "reasoning"):
        if not runtime.get(field):
            errors.append(f"runtime metadata missing {field}")
    available_tools = runtime.get("available_tools")
    if not isinstance(available_tools, list):
        errors.append("runtime available_tools must be a list")
    else:
        rendered = [str(item) for item in available_tools]
        for fragment in config().get("required_runtime_tool_fragments") or []:
            if not any(str(fragment) in tool for tool in rendered):
                errors.append(f"required runtime tool capability not observed: {fragment}")
    return errors


def client_display_evidence_errors(case_id: str, trace: dict, requested_status: str) -> list[str]:
    if requested_status != "PASS":
        return []

    cfg = config()
    required_cases = {str(x) for x in (cfg.get("client_display_validation_case_ids") or [])}
    if case_id not in required_cases:
        return []

    evidence = trace.get("client_display_evidence")
    if not isinstance(evidence, dict):
        return ["external client-display evidence is required for visual PASS"]

    if str(evidence.get("status") or "").upper() != "CONFIRMED":
        return ["client-display evidence status must be CONFIRMED"]

    evidence_type = str(evidence.get("type") or "")
    allowed = {str(x) for x in (cfg.get("client_display_evidence_types") or [])}
    if evidence_type not in allowed:
        return [f"unsupported client-display evidence type: {evidence_type or '<missing>'}"]

    if not str(evidence.get("reference") or "").strip():
        return ["client-display evidence requires a reference"]

    return []


def trace_schema_errors(trace: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(trace, dict):
        return ["runtime trace must be an object"]

    selected = trace.get("selected_capabilities")
    if not isinstance(selected, list):
        errors.append("selected_capabilities must be a list")
        selected = []
    elif not all(isinstance(item, str) and item.strip() for item in selected):
        errors.append("selected_capabilities must contain only non-empty capability names")

    known = validate_routing.known_capability_names(ROOT)
    unknown = sorted({
        str(item) for item in selected
        if isinstance(item, str) and item.strip() and item not in known
    })
    if unknown:
        errors.append(
            "selected_capabilities contains non-capability/tool names: " + ", ".join(unknown)
        )

    tool_calls = trace.get("tool_calls")
    if not isinstance(tool_calls, list):
        errors.append("tool_calls must be a list")

    return errors


def selection_errors(case: dict, trace: dict) -> list[str]:
    selected = list(trace.get("selected_capabilities") or [])
    rubric = yaml.safe_load((ROOT / case["rubric"]).read_text(encoding="utf-8")) or {}
    suite = case["suite"]
    if suite == "executive-role":
        should = bool(rubric.get("should_trigger"))
        present = "executive-role-evaluator" in selected
        if should and not present:
            return ["expected executive-role-evaluator selection is absent"]
        if not should and present:
            return ["negative executive-role case selected executive-role-evaluator"]
        return []
    if suite in {"routing", "supplemental-routing"}:
        errors: list[str] = []
        expected = rubric.get("expected_target")
        if expected not in selected:
            errors.append(f"expected routing target absent: {expected}")
        for required in rubric.get("required_selected_capabilities") or []:
            if required not in selected:
                errors.append(f"required child capability absent: {required}")
        for forbidden in rubric.get("forbidden_selected_capabilities") or []:
            if forbidden in selected:
                errors.append(f"forbidden capability selected: {forbidden}")

        tool_calls_text = json.dumps(trace.get("tool_calls") or [], ensure_ascii=False)
        for fragment in rubric.get("required_tool_fragments") or []:
            if str(fragment) not in tool_calls_text:
                errors.append(f"required routing tool call absent: {fragment}")
        return errors
    return [] if case["target"] in selected else [f"invoked subject absent from trace: {case['target']}"]


def import_run(args) -> Path:
    cfg = config()
    lock = validate_lock_file(Path(args.lock), root=ROOT)
    cases = {**load_campaign_cases(ROOT, config()["campaign"]), **load_supplemental_cases(ROOT, config()["campaign"])}
    if args.case_id not in cases:
        raise ValueError(f"unknown active campaign case: {args.case_id}")
    case = cases[args.case_id]

    # Lock validation is intentionally separate from installed-artifact smoke.
    smoke_errors = verify_smoke(Path(args.lock), Path(args.smoke))
    if smoke_errors:
        raise ValueError("; ".join(smoke_errors))
    obs = json.loads(Path(args.smoke).read_text(encoding="utf-8"))
    required_channel = lock["case_channels"][args.case_id]
    if obs.get("channel") != required_channel:
        raise ValueError(f"case {args.case_id} requires {required_channel} session")
    trace = json.loads(Path(args.trace).read_text(encoding="utf-8"))
    schema_errors = trace_schema_errors(trace)
    sel_errors = schema_errors + selection_errors(case, trace)
    if sel_errors and args.status == "PASS":
        raise ValueError("PASS forbidden when runtime trace/selection findings exist: " + "; ".join(sel_errors))

    display_errors = client_display_evidence_errors(args.case_id, trace, args.status)
    if display_errors:
        raise ValueError(
            "PASS forbidden without external client-display evidence: " + "; ".join(display_errors)
        )

    component = {
        (x["channel"], x["name"]): x for x in lock["components"]
    }[(required_channel, case["target"])]
    source_version, source_digest = receipt.current_component_identity(ROOT, case["target"])
    dest = ROOT / cfg["evidence_root"] / args.case_id / args.run_id
    dest.mkdir(parents=True, exist_ok=False)
    out_dest = dest / "output.md"
    trace_dest = dest / "trace.json"
    shutil.copyfile(args.output, out_dest)
    shutil.copyfile(args.trace, trace_dest)

    runtime = obs["runtime"]
    ns = argparse.Namespace(
        case_id=args.case_id,
        status=args.status,
        evidence_scope="current-version",
        source_revision=lock["behavior_source_revision"],
        component=case["target"],
        component_version=source_version,
        component_digest=source_digest,
        provider=runtime["provider"],
        model_id=runtime["model_id"],
        reasoning=runtime["reasoning"],
        catalog=list(obs["catalog"]),
        tools=list(runtime.get("available_tools") or []),
        prompt=(ROOT / case["input"]).read_text(encoding="utf-8"),
        output=str(out_dest),
        tool_trace=str(trace_dest),
        reviewer=args.reviewer,
        assisted=args.assisted,
        runtime_artifact={
            "channel": required_channel,
            "package_name": obs["package"]["name"],
            "package_version": obs["package"]["version"],
            "release_id": obs["package"]["release_id"],
            "source_revision": obs["package"]["source_revision"],
            "payload_content_sha256": obs["package"]["payload_content_sha256"],
            "component_content_sha256": component["content_sha256"],
        },
        selection_findings=sel_errors,
        evidence_origin=str(getattr(args, "evidence_origin", "runtime")),
        note=args.note,
    )
    old = os.environ.get("SOURCE_REVISION")
    os.environ["SOURCE_REVISION"] = lock["behavior_source_revision"]
    try:
        rec = receipt.create_receipt(ns)
    finally:
        if old is None:
            os.environ.pop("SOURCE_REVISION", None)
        else:
            os.environ["SOURCE_REVISION"] = old
    path = dest / "receipt.json"
    path.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def evidence_compatibility_profile(source_revision: str, root: Path = ROOT) -> str:
    active_revision = str(config(root).get("behavior_source_revision") or "")
    if source_revision == active_revision:
        return "active-r2"
    historical_campaign = HISTORICAL_RECEIPT_COMPATIBILITY.get(source_revision)
    if historical_campaign:
        historical_config = root / "evals" / "campaigns" / historical_campaign / "campaign.yaml"
        if not historical_config.is_file():
            raise ValueError(
                f"historical compatibility campaign is missing: {historical_campaign}"
            )
        if historical_campaign == "runtime-validation-2026-10":
            return "historical-r1"
        if historical_campaign == "runtime-validation-2026-10-r2":
            return "historical-r2"
        if historical_campaign == "runtime-validation-2026-10-r3":
            return "historical-r3"
        if historical_campaign == "runtime-validation-2026-10-r4":
            return "historical-r4"
        if historical_campaign == "runtime-validation-2026-10-r5":
            return "historical-r5"
        if historical_campaign == "runtime-validation-2026-10-r6":
            return "historical-r6"
        if historical_campaign == "runtime-validation-2026-10-r7":
            return "historical-r7"
        if historical_campaign == "runtime-validation-2026-10-r8":
            return "historical-r8"
        if historical_campaign == "runtime-validation-2026-10-r9":
            return "historical-r9"
        if historical_campaign == "runtime-validation-2026-10-r10":
            return "historical-r10"
        if historical_campaign == "runtime-validation-2026-10-r11":
            return "historical-r11"
        if historical_campaign == "runtime-validation-2026-10-r12":
            return "historical-r12"
        if historical_campaign == "runtime-validation-2026-10-r13":
            return "historical-r13"
        if historical_campaign == "runtime-validation-2026-10-r14":
            return "historical-r14"
        if historical_campaign == "runtime-validation-2026-10-r15":
            return "historical-r15"
        return "historical-r14"
    raise ValueError(f"unsupported evidence source revision: {source_revision}")


def validate_evidence() -> list[str]:
    root = ROOT / config()["evidence_root"]
    if not root.exists():
        return []
    errors = []
    for path in sorted(root.rglob("receipt.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        source_revision = str(data.get("source_revision") or "")
        try:
            compatibility = evidence_compatibility_profile(source_revision, root=ROOT)
        except ValueError as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue
        for err in receipt.validate_receipt_data(
            data, root=ROOT, current_revision=source_revision
        ):
            errors.append(f"{path.relative_to(ROOT)} [{compatibility}]: {err}")
    return errors


def main() -> int:
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest="cmd", required=True)
    s.add_parser("validate")
    q = s.add_parser("queue")
    q.add_argument("--output", type=Path)
    q.add_argument("--include-supplemental", action="store_true")
    prep = s.add_parser("prepare")
    prep.add_argument("--output", type=Path, default=ROOT / ".tmp/runtime-campaign")
    lock_cmd = s.add_parser("validate-lock")
    lock_cmd.add_argument("--lock", required=True, type=Path)
    smoke = s.add_parser("verify-smoke")
    smoke.add_argument("--lock", required=True, type=Path)
    smoke.add_argument("--observed", required=True, type=Path)
    imp = s.add_parser("import-run")
    imp.add_argument("--case-id", required=True)
    imp.add_argument("--run-id", required=True)
    imp.add_argument("--lock", required=True)
    imp.add_argument("--smoke", required=True)
    imp.add_argument("--output", required=True)
    imp.add_argument("--trace", required=True)
    imp.add_argument("--status", required=True, choices=["REVIEW_REQUIRED", "PASS", "FAIL"])
    imp.add_argument("--reviewer", required=True)
    imp.add_argument("--assisted", action="store_true")
    imp.add_argument("--evidence-origin", choices=["runtime", "offline"], default="runtime")
    imp.add_argument("--note")
    s.add_parser("validate-evidence")
    args = p.parse_args()

    if args.cmd == "validate":
        errors = validate_campaign()
        for e in errors:
            print("[BLOCKER]", e)
        if not errors:
            print(f"Runtime campaign definition: OK ({len(load_campaign_cases(ROOT, config()["campaign"]))} core cases)")
        return 1 if errors else 0
    if args.cmd == "queue":
        text = queue_text(args.include_supplemental)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0
    if args.cmd == "prepare":
        prepare(args.output)
        print(args.output)
        return 0
    if args.cmd == "validate-lock":
        try:
            validate_lock_file(args.lock, root=ROOT)
        except ValueError as exc:
            print("[BLOCKER]", exc)
            return 1
        print("Campaign lock: OK")
        return 0
    if args.cmd == "verify-smoke":
        errors = verify_smoke(args.lock, args.observed)
        for e in errors:
            print("[BLOCKER]", e)
        if not errors:
            print("Runtime smoke evidence: OK")
        return 1 if errors else 0
    if args.cmd == "import-run":
        print(import_run(args))
        return 0
    errors = validate_evidence()
    for e in errors:
        print("[BLOCKER]", e)
    if not errors:
        print("Runtime campaign evidence: OK")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
