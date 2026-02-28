from comunicacao.events.redis_consumer import build_clinical_alert_from_stream


def test_build_clinical_alert_from_stream_success() -> None:
    fields = {
        "type": "alert.created",
        "timestamp": "2026-02-10T12:00:00Z",
        "data": (
            '{"module":"intellicare-oswaldo","patient_id":"pac-10","severity":"alta",'
            '"message":"eGFR em queda","alert_type":"queda-egfr","correlation_id":"corr-10"}'
        ),
    }
    payload = build_clinical_alert_from_stream(fields)
    assert payload is not None
    assert payload["patient_id"] == "pac-10"
    assert payload["source_module"] == "intellicare-oswaldo"
    assert payload["alert_type"] == "queda-egfr"


def test_build_clinical_alert_from_stream_missing_required_fields() -> None:
    fields = {"data": '{"module":"intellicare-oswaldo","severity":"alta"}'}
    payload = build_clinical_alert_from_stream(fields)
    assert payload is None
