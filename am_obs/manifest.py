"""Manifest signal resolution (bundle + domain + legacy fields)."""

from __future__ import annotations

from dataclasses import dataclass

from am_obs.catalog import expand_bundle
from am_obs.loader import Context


@dataclass(frozen=True)
class ResolvedSignals:
    technical: frozenset[str]
    functional: frozenset[str]


def resolve_manifest_signals(manifest: dict, ctx: Context) -> ResolvedSignals:
    sig = manifest.get("signals") or {}
    technical: set[str] = set()
    functional: set[str] = set()

    bundle = sig.get("bundle")
    if bundle:
        technical |= expand_bundle(str(bundle), ctx.root)

    # include: extra signal ids, or additional bundle ids (hybrid)
    for item in sig.get("include") or []:
        name = str(item)
        if name in (ctx.signal_bundles or {}):
            technical |= expand_bundle(name, ctx.root)
        else:
            technical.add(name)

    for name, ids in (sig.get("groups") or {}).items():
        if name == "domain":
            functional |= set(ids or [])
        else:
            technical |= set(ids or [])

    technical |= set(sig.get("uses") or [])
    functional |= set(sig.get("domain") or [])
    functional |= set(manifest.get("functional") or [])

    return ResolvedSignals(technical=frozenset(technical), functional=frozenset(functional))
