from __future__ import annotations

from pathlib import Path

import yaml


DOMAIN_COLORS = {
    "career": "#FFD18A",
    "commerce": "#FF8B72",
    "investing": "#9588F7",
    "meta": "#94D4B3",
    "oaf": "#83A9FF",
    "presentations": "#F0C982",
    "reports": "#8AB5D7",
    "strategy-ea": "#75D8C1",
    "web-design": "#A998FF",
}
ACRONYMS = {"ai", "cac", "cogs", "cv", "kpi", "oaf", "os", "vat", "xtb"}


def display_name(name: str) -> str:
    return " ".join(
        part.upper() if part.lower() in ACRONYMS else part.capitalize()
        for part in name.split("-")
    )


def short_description(description: str) -> str:
    normalized = " ".join(description.split())
    if len(normalized) <= 64:
        return normalized
    prefix = normalized[:61].rsplit(" ", 1)[0].rstrip(" ,;:")
    return f"{prefix}…"


def repository_root(skill_dir: Path) -> Path:
    for parent in skill_dir.parents:
        if parent.name == "skills":
            return parent.parent
    raise ValueError(f"{skill_dir}: skill is not inside a skills folder")


def skill_domain(root: Path, skill_dir: Path) -> str:
    try:
        domain = skill_dir.relative_to(root / "skills").parts[0]
    except (ValueError, IndexError) as exc:
        raise ValueError(f"{skill_dir}: skill is not inside a domain folder") from exc
    if domain not in DOMAIN_COLORS:
        raise ValueError(f"{skill_dir}: no UI icon is configured for domain {domain!r}")
    return domain


def workflow_domain(name: str) -> str:
    if name.startswith("presentation-"):
        return "presentations"
    if name.startswith("report-"):
        return "reports"
    if name.startswith("commerce-"):
        return "commerce"
    if name.startswith(("investment-", "investing-")):
        return "investing"
    if name.startswith("oaf-"):
        return "oaf"
    return "meta"


def write_skill_interface(
    root: Path,
    skill_dir: Path,
    *,
    name: str,
    description: str,
    domain: str,
) -> list[str]:
    if domain not in DOMAIN_COLORS:
        raise ValueError(f"{name}: no UI icon is configured for domain {domain!r}")

    icon_source = root / "assets" / "skill-icons" / f"{domain}.svg"
    if not icon_source.is_file():
        return []

    config_path = skill_dir / "agents" / "openai.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if config_path.exists():
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        if not isinstance(config, dict):
            raise ValueError(f"{config_path}: expected a YAML mapping")
    else:
        config = {}

    interface = config.get("interface") or {}
    if not isinstance(interface, dict):
        raise ValueError(f"{config_path}: interface must be a YAML mapping")
    interface.setdefault("display_name", display_name(name))
    interface.setdefault("short_description", short_description(description))
    interface["icon_small"] = "./assets/skills-factory-domain-icon.svg"
    interface["brand_color"] = DOMAIN_COLORS[domain]
    config["interface"] = interface

    icon_relative = "assets/skills-factory-domain-icon.svg"
    icon_target = skill_dir / icon_relative
    icon_target.parent.mkdir(parents=True, exist_ok=True)
    icon_target.write_bytes(icon_source.read_bytes())
    config_path.write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return ["agents/openai.yaml", icon_relative]
