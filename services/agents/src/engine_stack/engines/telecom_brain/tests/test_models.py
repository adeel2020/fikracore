from __future__ import annotations

from engine_stack.engines.telecom_brain.models import (
    AlarmEvidence,
    FCAPSClassification,
    TelecomRequest,
    TelecomResult,
)


def test_request_and_result_keep_spoken_text_separate_from_written_text() -> None:
    request = TelecomRequest(
        query="tell the incident story",
        alarms=[AlarmEvidence(name="AMF overload", severity="critical")],
    )
    result = TelecomResult(
        text="# Detailed incident story",
        spoken_response="AMF overload is the leading incident story.",
        alarm_evidence=request.alarms,
        fcaps=[FCAPSClassification.FAULT],
    )

    assert request.alarms[0].name == "AMF overload"
    assert result.response_for_mark() == "AMF overload is the leading incident story."
    assert result.text != result.spoken_response
