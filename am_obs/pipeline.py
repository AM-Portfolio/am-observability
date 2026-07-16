"""End-to-end generate pipeline and report.json."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from am_obs.adapt import adapt
from am_obs.compose import compose, compose_shared, target_from_manifest
from am_obs.loader import Context, load_context
from am_obs.paths import ROOT, load_yaml
from am_obs.publish import publish_grafana_configmap
from am_obs.render import render_grafana
from am_obs.validate import validate_manifest


@dataclass
class ServiceResult:
    id: str
    ok: bool
    path: str | None = None
    uid: str | None = None
    warnings: list[str] = field(default_factory=list)
    error: str | None = None


def resolve_manifest_path(entry: dict[str, Any], ctx: Context) -> Path | None:
    """Resolve sibling checkout ../{repo}/{path}, else fixture fallback for prep."""
    repo = entry["repo"]
    rel = entry["path"]
    sibling = ctx.root.parent / repo / rel
    if sibling.is_file():
        return sibling
    fixture = ctx.root / "testdata" / "fixtures" / f"{entry['id']}.yaml"
    if fixture.is_file():
        return fixture
    return None


def _publish_dashboard(
    dashboard: dict[str, Any],
    ctx: Context,
) -> Path:
    out_ns = (
        ((ctx.bindings.get("outputs") or {}).get("dashboards") or {}).get("namespace")
        or "monitoring"
    )
    out_dir = ctx.root / "dist" / "grafana"
    return publish_grafana_configmap(dashboard, namespace=out_ns, out_dir=out_dir)


def generate_one(
    manifest: dict[str, Any],
    ctx: Context,
    *,
    source: str,
) -> tuple[dict[str, Any] | None, Path | None, list[str], str | None]:
    warnings: list[str] = []
    errors = validate_manifest(manifest, ctx, source=source)
    if errors:
        return None, None, warnings, "; ".join(errors)

    ir, w1 = compose(manifest, ctx)
    warnings.extend(w1)
    adapted, w2 = adapt(ir, ctx)
    warnings.extend(w2)
    dashboard = render_grafana(adapted)
    path = _publish_dashboard(dashboard, ctx)
    return dashboard, path, warnings, None


def generate_shared(
    ctx: Context,
    *,
    entries: list[dict[str, Any]],
    continue_on_error: bool = False,
) -> tuple[dict[str, Any] | None, Path | None, list[ServiceResult]]:
    """Build one Technical / Services dashboard from registry manifests."""
    results: list[ServiceResult] = []
    targets: list[dict[str, str]] = []
    default_enabled: dict[str, str] | None = None
    default_first: dict[str, str] | None = None
    warnings_all: list[str] = []

    for entry in entries:
        sid = entry["id"]
        mpath = resolve_manifest_path(entry, ctx)
        if mpath is None:
            results.append(
                ServiceResult(
                    id=sid,
                    ok=False,
                    error=(
                        f"manifest not found for {sid} "
                        f"(sibling repo or testdata/fixtures/{sid}.yaml)"
                    ),
                )
            )
            if not continue_on_error:
                return None, None, results
            continue

        manifest = load_yaml(mpath)
        if not isinstance(manifest, dict):
            results.append(ServiceResult(id=sid, ok=False, error=f"invalid YAML: {mpath}"))
            if not continue_on_error:
                return None, None, results
            continue

        errors = validate_manifest(manifest, ctx, source=str(mpath))
        if errors:
            results.append(ServiceResult(id=sid, ok=False, error="; ".join(errors)))
            if not continue_on_error:
                return None, None, results
            continue

        target = target_from_manifest(manifest)
        targets.append(target)
        if default_first is None:
            default_first = target
        if entry.get("enabled") and default_enabled is None:
            default_enabled = target

        warn: list[str] = []
        sibling = ctx.root.parent / entry["repo"] / entry["path"]
        if mpath != sibling:
            warn.append(f"using fixture {mpath.relative_to(ctx.root)}")
        results.append(ServiceResult(id=sid, ok=True, warnings=warn))

    if not targets:
        return None, None, results

    default = default_enabled or default_first

    ir, w1 = compose_shared(targets, ctx, default=default)
    warnings_all.extend(w1)
    if not ir:
        return None, None, results

    adapted, w2 = adapt(ir, ctx)
    warnings_all.extend(w2)
    dashboard = render_grafana(adapted)
    path = _publish_dashboard(dashboard, ctx)

    # Attach shared artifact to a synthetic result
    results.append(
        ServiceResult(
            id="tech-am-services",
            ok=True,
            path=str(path),
            uid=dashboard.get("uid"),
            warnings=warnings_all,
        )
    )
    return dashboard, path, results


def write_report(results: list[ServiceResult], report_path: Path) -> None:
    payload = {
        "results": [
            {
                "id": r.id,
                "ok": r.ok,
                "path": r.path,
                "uid": r.uid,
                "warnings": r.warnings,
                "error": r.error,
            }
            for r in results
        ],
        "failed": [r.id for r in results if not r.ok],
        "passed": [r.id for r in results if r.ok],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _print_results(results: list[ServiceResult], report_path: Path) -> None:
    for r in results:
        status = "OK" if r.ok else "FAIL"
        print(f"[{status}] {r.id}" + (f" -> {r.path}" if r.path else ""))
        for w in r.warnings:
            print(f"  warn: {w}")
        if r.error:
            print(f"  error: {r.error}", file=sys.stderr)
    print(f"report: {report_path}")


def generate(
    *,
    only: str | None = None,
    continue_on_error: bool = False,
    binding: Path | None = None,
    fixture: Path | None = None,
    root: Path | None = None,
    shared: bool = True,
) -> int:
    """
    Generate dashboards.

    Default: one shared Technical / Services dashboard (Service dropdown).
    --only / --fixture: per-service ConfigMap (compose ∩ signals.uses).
    """
    ctx = load_context(binding=binding, root=root or ROOT)
    results: list[ServiceResult] = []

    if fixture:
        shared = False
    if only:
        shared = False

    if fixture:
        manifest = load_yaml(fixture)
        if not isinstance(manifest, dict):
            print(f"invalid fixture: {fixture}", file=sys.stderr)
            return 1
        sid = str(manifest.get("service") or fixture.stem)
        dashboard, path, warnings, err = generate_one(manifest, ctx, source=str(fixture))
        results.append(
            ServiceResult(
                id=sid,
                ok=err is None,
                path=str(path) if path else None,
                uid=(dashboard or {}).get("uid") if dashboard else None,
                warnings=warnings,
                error=err,
            )
        )
    elif only:
        services = ctx.registry.get("services") or []
        selected = [e for e in services if e["id"] == only]
        if not selected:
            fixture_path = ctx.root / "testdata" / "fixtures" / f"{only}.yaml"
            if fixture_path.is_file():
                selected = [
                    {
                        "id": only,
                        "repo": only,
                        "path": "observability.yaml",
                        "ref": "main",
                        "enabled": False,
                    }
                ]
            else:
                print(f"unknown service id: {only}", file=sys.stderr)
                return 1

        entry = selected[0]
        mpath = resolve_manifest_path(entry, ctx)
        if mpath is None:
            print(f"manifest not found for {only}", file=sys.stderr)
            return 1
        manifest = load_yaml(mpath)
        if not isinstance(manifest, dict):
            print(f"invalid YAML: {mpath}", file=sys.stderr)
            return 1
        warnings_prefix: list[str] = []
        sibling = ctx.root.parent / entry["repo"] / entry["path"]
        if mpath != sibling:
            warnings_prefix.append(f"using fixture {mpath.relative_to(ctx.root)}")
        dashboard, path, warnings, err = generate_one(manifest, ctx, source=str(mpath))
        results.append(
            ServiceResult(
                id=only,
                ok=err is None,
                path=str(path) if path else None,
                uid=(dashboard or {}).get("uid") if dashboard else None,
                warnings=warnings_prefix + warnings,
                error=err,
            )
        )
    elif shared:
        # All registry entries with a resolvable manifest feed the Service dropdown
        entries = list(ctx.registry.get("services") or [])
        if not entries:
            print("no services in registry")
            write_report(results, ctx.root / "dist" / "report.json")
            return 0
        _, _, results = generate_shared(
            ctx, entries=entries, continue_on_error=continue_on_error
        )
    else:
        # Legacy: enabled-only per-service ConfigMaps
        services = ctx.registry.get("services") or []
        selected = [e for e in services if e.get("enabled")]
        if not selected:
            print("no enabled services to generate")
            write_report(results, ctx.root / "dist" / "report.json")
            return 0
        for entry in selected:
            sid = entry["id"]
            mpath = resolve_manifest_path(entry, ctx)
            if mpath is None:
                results.append(
                    ServiceResult(
                        id=sid,
                        ok=False,
                        error=f"manifest not found for {sid}",
                    )
                )
                if not continue_on_error:
                    break
                continue
            manifest = load_yaml(mpath)
            if not isinstance(manifest, dict):
                results.append(ServiceResult(id=sid, ok=False, error=f"invalid YAML: {mpath}"))
                if not continue_on_error:
                    break
                continue
            dashboard, path, warnings, err = generate_one(manifest, ctx, source=str(mpath))
            results.append(
                ServiceResult(
                    id=sid,
                    ok=err is None,
                    path=str(path) if path else None,
                    uid=(dashboard or {}).get("uid") if dashboard else None,
                    warnings=warnings,
                    error=err,
                )
            )
            if err and not continue_on_error:
                break

    report_path = ctx.root / "dist" / "report.json"
    write_report(results, report_path)
    _print_results(results, report_path)
    failed = [r for r in results if not r.ok]
    return 1 if failed else 0
