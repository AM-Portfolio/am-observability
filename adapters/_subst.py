"""Variable substitution that leaves Grafana dashboard $vars intact."""

from __future__ import annotations

from string import Template

# These become Grafana template variables (visible dropdowns / text boxes).
GRAFANA_TEMPLATE_VARS = frozenset({"namespace", "service", "app", "application", "env"})


def subst_for_grafana(template: str, vars_: dict[str, str]) -> str:
    """Substitute only non-Grafana keys; leave $namespace/$app/... for the UI."""
    frozen = {k: v for k, v in vars_.items() if k not in GRAFANA_TEMPLATE_VARS}
    return Template(template).safe_substitute(**frozen)
