from __future__ import annotations

import pytest

from engine_stack.engines.telecom_brain.canonicalization import CanonicalResolver, load_default_resolver


def test_default_resolver_maps_known_sgi_aliases() -> None:
    resolver = load_default_resolver()

    result = resolver.resolve(
        "mobile-core/incidents/sgi-throughput-drop",
        exists=lambda slug: slug == "incidents/mobile-core/sgi-data-a154bb7a3997859c",
    )

    assert result.resolved_slug == "incidents/mobile-core/sgi-data-a154bb7a3997859c"
    assert result.source == "canonical-resolver"
    assert "mobile-core/incidents/sgi-throughput-drop" in result.candidates


def test_default_resolver_keeps_exact_historical_page_reachable() -> None:
    resolver = load_default_resolver()

    result = resolver.resolve(
        "mobile-core/incidents/amf-overload-2026-08-09",
        exists=lambda slug: slug == "mobile-core/incidents/amf-overload-2026-08-09",
    )

    assert result.resolved_slug == "mobile-core/incidents/amf-overload-2026-08-09"
    assert result.source == "exact"
    assert "incidents/mobile-core/amf-overload-2026-08-09" in result.candidates


def test_resolver_rejects_alias_cycles() -> None:
    with pytest.raises(ValueError, match="cycle"):
        CanonicalResolver([
            {"legacy_slug": "a", "canonical_slug": "b", "action": "alias"},
            {"legacy_slug": "b", "canonical_slug": "a", "action": "alias"},
        ])
