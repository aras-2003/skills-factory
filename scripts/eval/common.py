from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry(root: Path | None = None) -> dict[str, list[dict[str, Any]]]:
    root = root or repo_root()
    path = root / "evals" / "runtime-fixtures.yaml"
    data = load_yaml(path) or {}
    targets = data.get("targets")
    if not isinstance(targets, dict):
        raise ValueError(f"{path}: targets must be a mapping")
    return targets


ACTIVE_CAMPAIGN = "runtime-validation-2026-10-r6"


def load_campaign_config(root: Path | None = None, campaign: str | None = None) -> dict[str, Any]:
    root = root or repo_root()
    name = campaign or ACTIVE_CAMPAIGN
    path = root / "evals" / "campaigns" / name / "campaign.yaml"
    if not path.is_file():
        return {}
    data = load_yaml(path) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: campaign config must be a mapping")
    return data


def _routing_cases(root: Path, registry_rel: str, wanted: set[str] | None, suite: str) -> dict[str, dict[str, Any]]:
    path = root / registry_rel
    data = load_yaml(path) or {}
    result: dict[str, dict[str, Any]] = {}
    for case in data.get("cases") or []:
        if not isinstance(case, dict):
            continue
        cid = str(case.get("id") or "")
        if not cid or (wanted is not None and cid not in wanted):
            continue
        rubric_path = root / str(case.get("rubric") or "")
        rubric = load_yaml(rubric_path) or {}
        result[cid] = {
            "id": cid,
            "target": str(rubric.get("expected_target") or "runtime-routing"),
            "mode": "natural-routing",
            "input": str(case.get("input") or ""),
            "rubric": str(case.get("rubric") or ""),
            "suite": suite,
        }
    return result


def load_campaign_cases(root: Path | None = None, campaign: str | None = None) -> dict[str, dict[str, Any]]:
    root = root or repo_root()
    config = load_campaign_config(root, campaign)
    if not config:
        return {}
    result: dict[str, dict[str, Any]] = {}

    runtime_targets = load_registry(root)
    wanted = set(config.get("commerce_case_ids") or [])
    for target, cases in runtime_targets.items():
        for case in cases:
            if case.get("id") in wanted:
                result[str(case["id"])] = {
                    **case,
                    "target": target,
                    "suite": "commerce",
                }

    routing_ids_raw = config.get("routing_case_ids")
    routing_registry = config.get("routing_registry")
    if routing_registry:
        if not isinstance(routing_registry, str):
            raise ValueError("routing_registry must be a relative file path")
        routing_ids = set(routing_ids_raw) if isinstance(routing_ids_raw, list) else None
        result.update(_routing_cases(root, routing_registry, routing_ids, "routing"))
    elif routing_ids_raw:
        raise ValueError("routing_case_ids set without a routing_registry")

    campaign_name = str(config.get("campaign") or campaign or ACTIVE_CAMPAIGN)
    base_rel = config.get("executive_case_dir") or f"evals/campaigns/{campaign_name}/executive"
    base = root / str(base_rel)
    for cid in config.get("executive_case_ids") or []:
        cid = str(cid)
        result[cid] = {
            "id": cid,
            "target": "executive-role-evaluator",
            "mode": "natural-routing",
            "input": (base / f"{cid}.input.md").relative_to(root).as_posix(),
            "rubric": (base / f"{cid}.rubric.yaml").relative_to(root).as_posix(),
            "suite": "executive-role",
        }

    for case in config.get("fallback_cases") or []:
        if not isinstance(case, dict):
            continue
        cid = str(case.get("id") or "")
        if cid:
            result[cid] = {
                "id": cid,
                "target": str(case.get("target") or ""),
                "mode": str(case.get("mode") or "explicit"),
                "input": str(case.get("input") or ""),
                "rubric": str(case.get("rubric") or ""),
                "suite": "production-fallback",
            }
    return result


def load_supplemental_cases(root: Path | None = None, campaign: str | None = None) -> dict[str, dict[str, Any]]:
    root = root or repo_root()
    config = load_campaign_config(root, campaign)
    registry = config.get("supplemental_routing_registry")
    if not registry:
        return {}
    wanted_raw = config.get("supplemental_routing_case_ids")
    wanted = set(wanted_raw) if isinstance(wanted_raw, list) else None
    return _routing_cases(root, str(registry), wanted, "supplemental-routing")


def find_campaign_case(root: Path, case_id: str) -> dict[str, Any] | None:
    active = load_campaign_cases(root)
    if case_id in active:
        return active[case_id]
    supplemental = load_supplemental_cases(root)
    if case_id in supplemental:
        return supplemental[case_id]
    campaigns_root = root / "evals" / "campaigns"
    if not campaigns_root.is_dir():
        return None
    found: dict[str, Any] | None = None
    for path in sorted(campaigns_root.glob("*/campaign.yaml")):
        name = path.parent.name
        if name == ACTIVE_CAMPAIGN:
            continue
        cases = load_campaign_cases(root, name)
        case = cases.get(case_id)
        if case is None:
            continue
        if found is None:
            found = case
            continue
        signature = ("target", "mode", "input", "rubric")
        if any(found.get(k) != case.get(k) for k in signature):
            raise ValueError(f"ambiguous historical campaign case: {case_id}")
    return found
