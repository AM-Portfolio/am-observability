#!/usr/bin/env python3
"""am-observability CLI: validate | generate [--only ID] [--continue] [--binding PATH] [--fixture PATH]"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

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
        help="Bindings file (default: bindings/preprod.yaml)",
    )
    p_validate.set_defaults(func=_run_validate)

    p_generate = sub.add_parser("generate", help="Generate dashboard ConfigMaps into dist/")
    p_generate.add_argument("--only", metavar="ID", help="Generate a single service id")
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
        help="Bindings file (default: bindings/preprod.yaml)",
    )
    p_generate.add_argument(
        "--fixture",
        type=Path,
        default=None,
        help="Generate from a fixture/manifest path (bypasses registry)",
    )
    p_generate.set_defaults(func=_run_generate)

    return parser


def _run_validate(args: argparse.Namespace) -> int:
    return cmd_validate(binding=args.binding)


def _run_generate(args: argparse.Namespace) -> int:
    return generate(
        only=args.only,
        continue_on_error=args.continue_on_error,
        binding=args.binding,
        fixture=args.fixture,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
