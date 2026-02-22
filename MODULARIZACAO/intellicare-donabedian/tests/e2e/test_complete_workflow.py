"""
Testes end-to-end do fluxo completo do sistema.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestCompleteWorkflow:
    """Testes E2E do fluxo completo de uso do sistema."""
    
    async def test_complete_quality_assessment_workflow(self, client: AsyncClient):
        """
        Testa o fluxo completo de avaliação de qualidade:
        1. Criar pilar
        2. Criar indicador
        3. Associar indicador ao pilar
        4. Criar medições
        5. Avaliar qualidade
        """
        
        # 1. Criar pilar
        pillar_response = await client.post(
            "/api/v1/pillars",
            json={
                "name": "Eficácia",
                "description": "Capacidade de produzir o efeito desejado",
                "display_order": 1
            }
        )
        assert pillar_response.status_code == 201
        pillar = pillar_response.json()
        pillar_id = pillar["id"]
        
        # 2. Criar indicador
        indicator_response = await client.post(
            "/api/v1/indicators",
            json={
                "name": "Taxa de Ocupação",
                "description": "Percentual de leitos ocupados",
                "formula": "(leitos_ocupados / total_leitos) * 100",
                "unit": "%",
                "target_value": 85.0,
                "target_operator": "<=",
                "triad_dimension": "structure"
            }
        )
        assert indicator_response.status_code == 201
        indicator = indicator_response.json()
        indicator_id = indicator["id"]
        
        # 3. Associar indicador ao pilar
        association_response = await client.post(
            "/api/v1/indicator-pillars",
            json={
                "indicator_id": indicator_id,
                "pillar_id": pillar_id,
                "weight": 1.0
            }
        )
        assert association_response.status_code == 201
        
        # 4. Criar medições
        measurements = [
            {"value": 80.0, "month": "01"},  # Dentro da meta
            {"value": 82.0, "month": "02"},  # Dentro da meta
            {"value": 88.0, "month": "03"},  # Fora da meta
        ]
        
        for measurement in measurements:
            measurement_response = await client.post(
                "/api/v1/measurements",
                json={
                    "indicator_id": indicator_id,
                    "value": measurement["value"],
                    "period_start": f"2024-{measurement['month']}-01T00:00:00",
                    "period_end": f"2024-{measurement['month']}-28T23:59:59",
                    "period_type": "monthly"
                }
            )
            assert measurement_response.status_code == 201
        
        # 5. Avaliar qualidade geral
        assessment_response = await client.get(
            "/api/v1/assessment/quality"
            "?period_start=2024-01-01T00:00:00"
            "&period_end=2024-03-31T23:59:59"
        )
        assert assessment_response.status_code == 200
        assessment = assessment_response.json()
        
        # Validações
        assert assessment["total_indicators"] >= 1
        assert "overall_score" in assessment
        assert "pillars" in assessment
        assert len(assessment["pillars"]) >= 1
        
        # 6. Avaliar pilar específico
        pillar_assessment_response = await client.get(
            f"/api/v1/assessment/pillar/{pillar_id}"
            "?period_start=2024-01-01T00:00:00"
            "&period_end=2024-03-31T23:59:59"
        )
        assert pillar_assessment_response.status_code == 200
        pillar_assessment = pillar_assessment_response.json()
        
        assert pillar_assessment["pillar_id"] == pillar_id
        assert pillar_assessment["pillar_name"] == "Eficácia"
        assert pillar_assessment["total_indicators"] >= 1
        
        # 7. Avaliar indicador específico
        indicator_assessment_response = await client.get(
            f"/api/v1/assessment/indicator/{indicator_id}"
            "?period_start=2024-01-01T00:00:00"
            "&period_end=2024-03-31T23:59:59"
        )
        assert indicator_assessment_response.status_code == 200
        indicator_assessment = indicator_assessment_response.json()
        
        assert indicator_assessment["indicator_id"] == indicator_id
        assert indicator_assessment["measurements_count"] == 3
    
    async def test_crud_operations_workflow(self, client: AsyncClient):
        """
        Testa fluxo completo de operações CRUD:
        1. Create
        2. Read
        3. Update
        4. Delete
        """
        
        # 1. CREATE - Criar pilar
        create_response = await client.post(
            "/api/v1/pillars",
            json={
                "name": "Eficiência",
                "description": "Relação entre resultados e recursos",
                "display_order": 3
            }
        )
        assert create_response.status_code == 201
        pillar = create_response.json()
        pillar_id = pillar["id"]
        
        # 2. READ - Buscar pilar criado
        read_response = await client.get(f"/api/v1/pillars/{pillar_id}")
        assert read_response.status_code == 200
        read_pillar = read_response.json()
        assert read_pillar["name"] == "Eficiência"
        
        # 3. UPDATE - Atualizar pilar
        update_response = await client.put(
            f"/api/v1/pillars/{pillar_id}",
            json={
                "name": "Eficiência Atualizada",
                "description": "Nova descrição",
                "display_order": 4
            }
        )
        assert update_response.status_code == 200
        updated_pillar = update_response.json()
        assert updated_pillar["name"] == "Eficiência Atualizada"
        assert updated_pillar["display_order"] == 4
        
        # 4. DELETE - Deletar pilar
        delete_response = await client.delete(f"/api/v1/pillars/{pillar_id}")
        assert delete_response.status_code == 204
        
        # Verificar que foi deletado
        verify_response = await client.get(f"/api/v1/pillars/{pillar_id}")
        assert verify_response.status_code == 404

