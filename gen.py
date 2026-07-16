#!/usr/bin/env python3
"""am-observability CLI: validate | generate | package-release | doctor | compose-view"""

from __future__ import annotations


import argparse
import sys
from pathlib import Path

from am_obs.compose_view import compose_service_view
from am_obs.doctor import cmd_doctor
from am_obs.package import package_release
from am_obs.pipeline import generate
from am_obs.validate import cmd_validate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gen.py", description="am-observability generator")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="Validate catalog/bindings/registry")
    p_validate.add_argument(
        "--binding",
        type=Path,
        default=None,
        help="Bindings file (default: bindings/platform.yaml)",
    )
    p_validate.set_defaults(func=_run_validate)

    p_generate = sub.add_parser("generate", help="Generate dashboard ConfigMaps into dist/")
    p_generate.add_argument("--only", metavar="ID", help="Generate a single service id")
    p_generate.add_argument(
        "--platform-only",
        metavar="ID",
        help="Generate a single platform dashboard (overview, redis, …)",
    )
    p_generate.add_argument(
        "--no-platform",
        action="store_true",
        help="Skip Platform / * dashboards",
    )
    p_generate.add_argument(
        "--continue",
        dest="continue_on_error",
        action="store_true",
        help="Continue on per-service failures",
    )
    p_generate.add_argument(
        "--binding",
        type=Path,
        default=None,
        help="Bindings file (default: bindings/platform.yaml)",
    )
    p_generate.add_argument(
        "--fixture",
        type=Path,
        default=None,
        help="Generate from a fixture/manifest path (bypasses registry)",
    )
    p_generate.set_defaults(func=_run_generate)

    p_pkg = sub.add_parser(
        "package-release",
        help="Zip shared dashboards + catalog-index for am-infra obs-upgrade",
    )
    p_pkg.add_argument(
        "--version",
        required=True,
        help="Release version tag (e.g. v1.4.0)",
    )
    p_pkg.set_defaults(func=_run_package)

    p_doctor = sub.add_parser("doctor", help="Validate a service observability.yaml")
    p_doctor.add_argument("manifest", type=Path, help="Path to observability.yaml")
    p_doctor.add_argument(
        "--index",
        type=Path,
        default=None,
        help="Optional catalog-index.json (default: build from local catalog)",
    )
    p_doctor.set_defaults(func=_run_doctor)

    p_view = sub.add_parser(
        "compose-view",
        help="Plane C: compose filtered tech-view-{service} ConfigMap",
    )
    p_view.add_argument("--manifest", type=Path, required=True)
    p_view.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output dir (default: dist/grafana)",
    )
    p_view.set_defaults(func=_run_compose_view)

    return parser


def _run_validate(args: argparse.Namespace) -> int:
    return cmd_validate(binding=args.binding)


def _run_generate(args: argparse.Namespace) -> int:
    return generate(
        only=args.only,
        continue_on_error=args.continue_on_error,
        binding=args.binding,
        fixture=args.fixture,
        platform=not args.no_platform,
        platform_only=args.platform_only,
    )


def _run_package(args: argparse.Namespace) -> int:
    package_release(args.version)
    return 0


def _run_doctor(args: argparse.Namespace) -> int:
    return cmd_doctor(args.manifest, index=args.index)


def _run_compose_view(args: argparse.Namespace) -> int:
    compose_service_view(args.manifest, out_dir=args.out)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
