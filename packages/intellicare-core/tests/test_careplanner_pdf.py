import pytest
import uuid

@pytest.mark.asyncio
async def test_journey_report_pdf_returns_pdf(client, gestor_token, existing_correlation_id):
    """GET /journeys/{id}/report.pdf retorna bytes de PDF válido."""
    resp = await client.get(
        f"/api/v1/careplanner/journeys/{existing_correlation_id}/report.pdf",
        headers={"Authorization": f"Bearer {gestor_token}"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    # PDFs começam com %PDF
    assert resp.content[:4] == b"%PDF"

@pytest.mark.asyncio
async def test_journey_report_pdf_not_found(client, gestor_token):
    """Jornada inexistente retorna 404."""
    resp = await client.get(
        f"/api/v1/careplanner/journeys/{uuid.uuid4()}/report.pdf",
        headers={"Authorization": f"Bearer {gestor_token}"},
    )
    assert resp.status_code == 404
