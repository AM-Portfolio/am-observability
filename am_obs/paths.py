"""Shared path helpers and YAML/JSON loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def dump_yaml(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, default_flow_style=False)


def env_from_namespace(namespace: str) -> str:
    if namespace.startswith("am-apps-"):
        return namespace.removeprefix("am-apps-")
    return namespace
