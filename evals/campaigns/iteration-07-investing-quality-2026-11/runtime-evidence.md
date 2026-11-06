# Iteration 07 candidate runtime evidence — 2026-11-06

## Identity and scope

- Canonical source / merged PR #587: `854117b7128dcc88e5c46407b8bee71309af7357`.
- Cloud Next Site: `Skills Factory Cloud Next`, private owner-only audience preserved.
- Site runtime: attestation `verified`; Lab `1.38.464`; release `1.38.464+854117b7128d`; canonical source `854117b7128dcc88e5c46407b8bee71309af7357`; deployed `2026-11-06T20:24:21Z`.
- Runtime mode: `host_model_executes_loaded_instructions`. Python helpers are packaged but the runtime reports `supporting_code_execution=not_executed`; the figures below were calculated from reviewed inputs using the displayed formulas. No claim that a packaged Python helper ran on Site.
- Release approval remains false. No canonical reads/writes, portfolio mutation, trade, maturity change, or production promotion was performed.

Runtime tool-call receipts are unsigned records. They identify calls and package/source hashes; they do not certify semantic correctness of the model response.

| Call | Result / identity | Completed (UTC) | Input SHA-256 | Output SHA-256 |
|---|---|---|---|---|
| `runtime_info` | `verified`, exact source and Lab above | 20:48:29.324 | `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a` | `53a259a6c242e5d405cdc6b91d04c5a29a7447f14bc6ab47b129fae2a7ab4613` |
| `load_skill: security-underwriting` | v0.5.3, content `733f6ea72cc857d4977536cbac747f643cdec0a13d297e2e67885f5ec2f98c61` | 20:48:29.321 | `af41cbe400ff54bb0e6357300fd4b738fe17fb72b112a2035935faa344d5ef3f` | `591ad3d8265fdc512347cdb3de719a5d8e6e201a7f2d51d1d158fc7e2a99b093` |
| `load_skill: valuation-scenario-review` | v0.3.1, content `cd9bdb6e1738874eca5ab79b4ad4b92d9d993b0f3733d808ea33592f6782f53d` | 20:48:29.174 | `852741e448df6cfcd19556fd7de0cbcca74d3ab8168fb75915c295f5a62a61e2` | `32cf0c9eb6cad96d6c222c6bf7795a7cad30731dffdeefc4b57a812290aa912e` |
| `load_skill: thesis-challenge` | v0.1.2, content `850c9ae554346b3c0acecf37d968026e2e9390c5c0ff098e8d6a670c975532b2` | 20:48:29.237 | `8417dd7d74f0339e0b1d66b8936a821f5ac04306b0c6531f213327f700f3fc50` | `bf61691bc41160fd782358afcbbcb25a6da6e131ac7d4efb04a3ca396e5fab57` |
| `route_investment_request` | `security-review` → `investment-security-review`; routed only | 20:47:34.082 | `355900207b8163943d1bf78ce859573cd510ecfd58693091d3aff4dee549344d` | `e21959c733cbd9648b3d1bd1bae373360c1618765e714171656457f0e1acd062` |
| `load_skill: investment-security-review` | v0.4.4, content `cea0256cabe61c35573b006dc24d280d2e1adced9210cdb288fd83a51afbe074` | 20:48:29.203 | `95524b2c75374b6cfce3ded2fbdae97a908541e91b3b81f34b0f84808aabb0bf` | `fcce1277ff15ed852f641c7236f8301dd2800aa1ef06ba7d12976dd2a85f15b1` |

The route's `workflow_executed=false` is significant. The exact workflow declares `investment-record-store` a required dependency and says a missing/inaccessible canonical read must return `BLOCKED_CANONICAL_READ`, never an assumed empty history. That tool is absent from this runtime's capabilities. In accordance with Iteration 07's exclusion of live portfolio reads/writes, the workflow was stopped at that gate. This is an integration blocker, not a successful end-to-end workflow result.

## #318 — source-backed financial quality probe (AMD)

**Probe input:** assess source/as-of gates, periods, units, FCF and conversion, working capital, debt/cash, dilution and cycle flags for AMD using public filings available by 2026-11-06. Do not value or size.

**Source contract:** USD millions unless stated; GAAP consolidated continuing operations for cash flow and income where available; FYs ended Dec 30, 2023, Dec 28, 2024, and Dec 27, 2025; latest YTD ended Sep 26, 2026 compared with same nine months ended Sep 27, 2025. The 2026 10-Q was signed Nov 3, 2026. The 2025 10-K contains the three annual periods and was filed in February 2026. No FX conversion or missing-value backfill.

### Period-aligned facts and derived values

| Period | Revenue | Gross margin | Continuing net income | Continuing CFO | PP&E purchases | FCF = CFO − capex | FCF / positive continuing NI |
|---|---:|---:|---:|---:|---:|---:|---:|
| FY2023 | 22,680 | 46.1% | 854 | 1,667 | 546 | 1,121 | 131.3% |
| FY2024 | 25,785 | 49.4% | 1,641 | 3,041 | 636 | 2,405 | 146.6% |
| FY2025 | 34,639 | 49.5% | 4,269 | 6,493 | 974 | 5,519 | 129.3% |
| 9M ended 2025-09-27 | 24,369 | 47.5% | 2,649 | 4,189 | 752 | 3,437 | 129.7% |
| 9M ended 2026-09-26 | 35,166 | 53.5% | 6,105 | 6,523 | 1,845 | 4,678 | 76.6% |

Annual values are reported in AMD's 2025 10-K; interim facts in the Q3 2026 10-Q. Gross margins for 9M are gross profit divided by revenue (11,575/24,369 and 18,829/35,166). FCF values use continuing CFO less cash PP&E purchases; this is not adjusted for leases or other capital commitments. Continuing income avoids mixing FY2025 discontinued ZT income ($66m) and 9M 2025 discontinued income ($175m) into the conversion denominator.

The YTD profile is mixed: revenue +44.3% YoY; continuing CFO +55.7%; PP&E cash purchases +145.3%; FCF +36.1%; and FCF conversion fell from 129.7% to …23627 tokens truncated…e"]: x for x in caps.get("capabilities", [])}
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
    prep.add_argument("--production-plugin", type=Path, help="Reuse a production package built from this exact source.")
    prep.add_argument("--lab-plugin", type=Path, help="Reuse a Lab package built from this exact source.")
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
        prepare(args.output, production_plugin=args.production_plugin, lab_plugin=args.lab_plugin)
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
