#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ENDPOINTS_PATH = ROOT / "framework" / "endpoints.json"
CATALOG_PATH = ROOT / "use-cases" / "CATALOG.md"
REQUIRED_FIELDS = {"id", "title", "endpoint", "attack_vector", "target_task", "artifacts", "mcp", "modes"}
SEVERITIES = {"low", "medium", "high", "critical"}
STATUSES = {"draft", "validated", "published"}


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def scenario_paths() -> list[Path]:
    return sorted(path for path in (ROOT / "use-cases").glob("**/scenario.json") if "_template" not in path.parts)


def validate_scenario(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        manifest = load_json(path)
        registry = load_json(ENDPOINTS_PATH)
    except ValueError as error:
        return [str(error)]

    missing = sorted(REQUIRED_FIELDS - manifest.keys())
    if missing:
        errors.append(f"missing fields: {', '.join(missing)}")

    endpoint = manifest.get("endpoint")
    if endpoint not in registry.get("endpoints", {}):
        errors.append(f"unknown endpoint: {endpoint!r}")
    source_endpoint = manifest.get("source_endpoint", endpoint)
    if source_endpoint not in registry.get("endpoints", {}):
        errors.append(f"unknown source endpoint: {source_endpoint!r}")

    mcp = manifest.get("mcp", {})
    servers = mcp.get("servers", []) if isinstance(mcp, dict) else []
    registered_servers = registry.get("servers", {})
    for server in servers:
        config = registered_servers.get(server)
        if config is None:
            errors.append(f"unknown MCP server: {server!r}")
        elif endpoint not in config.get("endpoints", []):
            errors.append(f"MCP server {server!r} does not support {endpoint!r}")

    scenario_root = path.parent.resolve()
    artifacts = manifest.get("artifacts", [])
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("artifacts must contain at least one entry")
    else:
        for artifact in artifacts:
            if not isinstance(artifact, dict) or not artifact.get("path"):
                errors.append("each artifact requires a path")
                continue
            artifact_path = (scenario_root / artifact["path"]).resolve()
            if scenario_root not in artifact_path.parents:
                errors.append(f"artifact escapes scenario directory: {artifact['path']}")
            elif not artifact_path.is_file():
                errors.append(f"artifact does not exist: {artifact['path']}")

    modes = manifest.get("modes", {})
    dry_run = modes.get("dry-run", {}) if isinstance(modes, dict) else {}
    if dry_run.get("writes_allowed") is not False:
        errors.append("dry-run must set writes_allowed to false")
    impact = modes.get("lab-impact") if isinstance(modes, dict) else None
    if impact:
        if impact.get("writes_allowed") is not True:
            errors.append("lab-impact must set writes_allowed to true")
        if impact.get("requires_operator_approval") is not True:
            errors.append("lab-impact requires operator approval")
        if not impact.get("canary_targets"):
            errors.append("lab-impact requires at least one canary target")

    severity = manifest.get("severity")
    if severity is not None and severity not in SEVERITIES:
        errors.append(f"invalid severity: {severity!r}")
    status = manifest.get("status")
    if status is not None and status not in STATUSES:
        errors.append(f"invalid status: {status!r}")
    references = manifest.get("references", [])
    if references and not all(
        isinstance(ref, dict) and ref.get("title") and ref.get("url") for ref in references
    ):
        errors.append("each reference requires a title and url")
    return errors


def build_plan(path: Path, mode: str) -> dict[str, Any]:
    errors = validate_scenario(path)
    if errors:
        raise ValueError("; ".join(errors))
    manifest = load_json(path)
    selected_mode = manifest["modes"].get(mode)
    if selected_mode is None:
        raise ValueError(f"scenario {manifest['id']} does not define mode {mode!r}")
    registry = load_json(ENDPOINTS_PATH)
    return {
        "scenario": manifest["id"],
        "title": manifest["title"],
        "source_endpoint": manifest.get("source_endpoint", manifest["endpoint"]),
        "endpoint": manifest["endpoint"],
        "attack_vector": manifest["attack_vector"],
        "severity": manifest.get("severity"),
        "status": manifest.get("status"),
        "mode": mode,
        "target_task": manifest["target_task"],
        "artifacts": manifest["artifacts"],
        "mcp": manifest["mcp"],
        "evidence": registry["endpoints"][manifest["endpoint"]]["evidence"],
        "safety": selected_mode,
    }


SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, None: 4}


def build_catalog() -> str:
    rows: list[dict[str, Any]] = []
    for path in scenario_paths():
        manifest = load_json(path)
        manifest["_dir"] = path.parent.relative_to(ROOT).as_posix()
        rows.append(manifest)
    rows.sort(key=lambda m: (SEVERITY_RANK.get(m.get("severity")), m["id"]))

    lines = [
        "# SkillVenom Scenario Catalog",
        "",
        "> Generated by `python3 framework/scripts/scenario.py catalog --write`. Do not edit by hand.",
        "",
        f"Total scenarios: **{len(rows)}**",
        "",
        "| ID | Scenario | Source -> Impact | Vector | Severity | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for m in rows:
        source = m.get("source_endpoint", m["endpoint"])
        link = f"[{m['id']}]({Path(m['_dir']).relative_to('use-cases').as_posix()}/README.md)"
        lines.append(
            f"| {link} | {m['title']} | {source} -> {m['endpoint']} | "
            f"{m['attack_vector']} | {m.get('severity', '-')} | {m.get('status', '-')} |"
        )

    lines += ["", "## Coverage", ""]
    endpoints = sorted({m["endpoint"] for m in rows} | {m.get("source_endpoint", m["endpoint"]) for m in rows})
    lines.append("| Endpoint | As source | As impact |")
    lines.append("| :--- | :--- | :--- |")
    for endpoint in endpoints:
        as_source = sum(1 for m in rows if m.get("source_endpoint", m["endpoint"]) == endpoint)
        as_impact = sum(1 for m in rows if m["endpoint"] == endpoint)
        lines.append(f"| {endpoint} | {as_source} | {as_impact} |")

    lines += ["", "## Vectors", ""]
    vectors: dict[str, int] = {}
    for m in rows:
        vectors[m["attack_vector"]] = vectors.get(m["attack_vector"], 0) + 1
    lines.append("| Vector | Scenarios |")
    lines.append("| :--- | :--- |")
    for vector, count in sorted(vectors.items()):
        lines.append(f"| {vector} | {count} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and plan SkillVenom scenarios")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("path", nargs="?", type=Path)
    validate_parser.add_argument("--all", action="store_true")
    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("path", type=Path)
    plan_parser.add_argument("--mode", choices=("dry-run", "lab-impact"), default="dry-run")
    catalog_parser = subparsers.add_parser("catalog")
    catalog_parser.add_argument("--write", action="store_true", help="write use-cases/CATALOG.md")
    catalog_parser.add_argument("--check", action="store_true", help="fail if CATALOG.md is stale")
    args = parser.parse_args()

    if args.command == "validate":
        paths = scenario_paths() if args.all else [args.path]
        if not paths or paths == [None]:
            parser.error("provide a scenario path or --all")
        failed = False
        for path in paths:
            errors = validate_scenario(path)
            if errors:
                failed = True
                for error in errors:
                    print(f"FAIL {path}: {error}", file=sys.stderr)
            else:
                print(f"PASS {path}")
        return int(failed)

    if args.command == "catalog":
        content = build_catalog()
        if args.check:
            current = CATALOG_PATH.read_text(encoding="utf-8") if CATALOG_PATH.is_file() else ""
            if current != content:
                print("FAIL CATALOG.md is stale; run: scenario.py catalog --write", file=sys.stderr)
                return 1
            print("PASS CATALOG.md is up to date")
            return 0
        if args.write:
            CATALOG_PATH.write_text(content, encoding="utf-8")
            print(f"wrote {CATALOG_PATH.relative_to(ROOT)}")
        else:
            print(content)
        return 0

    try:
        print(json.dumps(build_plan(args.path, args.mode), indent=2))
    except ValueError as error:
        print(f"FAIL {args.path}: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())