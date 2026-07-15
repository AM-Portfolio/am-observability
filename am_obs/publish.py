"""Compatibility re-export — implementation lives in publishers/grafana_configmap.py."""

from publishers.grafana_configmap import publish_grafana_configmap

__all__ = ["publish_grafana_configmap"]
