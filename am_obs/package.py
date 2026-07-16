"""Package release assets for Plane B (am-infra obs-upgrade)."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

from am_obs.catalog_index import write_catalog_index
from am_obs.loader import load_context
from am_obs.paths import ROOT


SHARED_DASHBOARD_PREFIXES = (
    "tech-am-services",
    "func-am-services",
    "platform-",
)


def package_release(version: str, *, root: Path | None = None) -> Path:
    """Build dist/release/grafana-dashboards-{version}.zip + sidecars.

    Requires `make generate` (or gen.py generate) to have populated dist/grafana/.
    """
    root = root or ROOT
    grafana_dir = root / "dist" / "grafana"
    if not grafana_dir.is_dir():
        raise FileNotFoundError(f"missing {grafana_dir}; run: python gen.py generate")

    release_dir = root / "dist" / "release"
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True)

    # Shared dashboards only (no per-service tech-am-portfolio products)
    staged = release_dir / "dashboards"
    staged.mkdir()
    copied: list[str] = []
    for path in sorted(grafana_dir.glob("*.yaml")):
        name = path.name
        if name.startswith(SHARED_DASHBOARD_PREFIXES) or any(
            name.startswith(p) for p in SHARED_DASHBOARD_PREFIXES
        ):
            shutil.copy2(path, staged / name)
            copied.append(name)

    if not copied:
        raise RuntimeError(f"no shared dashboard YAML found under {grafana_dir}")

    version_file = staged / "OBSERVABILITY_VERSION"
    version_file.write_text(version.strip() + "\n", encoding="utf-8")

    zip_path = release_dir / f"grafana-dashboards-{version}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(staged.iterdir()):
            zf.write(f, arcname=f.name)

    sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    (release_dir / f"grafana-dashboards-{version}.zip.sha256").write_text(
        f"{sha}  {zip_path.name}\n", encoding="utf-8"
    )

    write_catalog_index(release_dir / "catalog-index.json")

    schema_src = root / "schema" / "service-observability.schema.json"
    schema_dst = release_dir / "schema"
    schema_dst.mkdir()
    shutil.copy2(schema_src, schema_dst / schema_src.name)

    compat = {
        "apiVersion": "am.obs/v1",
        "kind": "ReleaseCompat",
        "version": version,
        "shared_uids": ["tech-am-services", "func-am-services"],
        "min_compose_cli": "1",
        "dashboards_zip": zip_path.name,
        "sha256": sha,
        "files": copied,
    }
    (release_dir / "compat.json").write_text(
        json.dumps(compat, indent=2) + "\n", encoding="utf-8"
    )

    # Also write catalog index under dist/ for local tooling
    write_catalog_index(root / "dist" / "catalog-index.json")

    print(f"release package: {zip_path}")
    print(f"  files: {len(copied)} dashboards + OBSERVABILITY_VERSION")
    print(f"  sha256: {sha}")
    return zip_path
