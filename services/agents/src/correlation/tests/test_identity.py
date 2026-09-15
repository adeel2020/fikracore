from datetime import datetime, timezone

from correlation.identity import IdentityResolver
from correlation.models import AlarmEvent


def test_resolver_enriches_source_component(tmp_path):
    path = tmp_path / "components.json"
    path.write_text('{"components":[{"source_system":"nms","source_object_id":"raw-1","component_id":"canonical-1","component_kind":"router","location":"site-a","service_ids":["voice"]}]}')
    event = AlarmEvent("tenant", "a-1", datetime.now(timezone.utc), "major", "transport", "nms", "raw-1", "LOSS")
    resolved = IdentityResolver.from_file(path).resolve(event)
    assert resolved.object_id == "canonical-1"
    assert resolved.service_ids == ("voice",)
