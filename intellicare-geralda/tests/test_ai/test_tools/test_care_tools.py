"""Testes para care tools LangChain."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import date, datetime

from geralda.ai.tools.care_tools import (
    create_care_plan_tool,
    get_care_plan_tool,
    add_care_task_tool,
    complete_task_tool,
    get_adherence_tool,
)
from geralda.engine.models import TaskCategory, TaskStatus


class TestCreateCarePlanTool:
    """Testes para tool de criar plano."""

    @pytest.mark.asyncio
    async def test_create_plan_basic(self):
        """Testa criação básica de plano."""
        from geralda.engine.care_manager import CareManager

        care_manager = CareManager()
        tool = create_care_plan_tool(care_manager)

        result = await tool.arun(
            patient_id="pac-001",
            conditions=["DRC estágio 3"],
            goals=["Controlar creatinina"],
            patient_name="Maria Silva",
        )

        assert result["success"] is True
        assert "plan_id" in result
        assert result["plan_id"] is not None

    @pytest.mark.asyncio
    async def test_create_plan_with_multiple_conditions(self):
        """Testa criação com múltiplas condições."""
        from geralda.engine.care_manager import CareManager

        care_manager = CareManager()
        tool = create_care_plan_tool(care_manager)

        result = await tool.arun(
            patient_id="pac-002",
            conditions=["DRC", "Diabetes", "Hipertensão"],
            goals=["Controlar todos os parâmetros"],
        )

        assert result["success"] is True
        assert len(result["conditions"]) == 3

    @pytest.mark.asyncio
    async def test_create_plan_without_patient_name(self):
        """Testa criação sem nome do paciente."""
        from geralda.engine.care_manager import CareManager

        care_manager = CareManager()
        tool = create_care_plan_tool(care_manager)

        result = await tool.arun(
            patient_id="pac-003",
            conditions=["DRC"],
            goals=["Controle"],
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_create_plan_tool_has_metadata(self):
        """Testa que tool tem metadados LangChain."""
        from geralda.engine.care_manager import CareManager

        care_manager = CareManager()
        tool = create_care_plan_tool(care_manager)

        assert hasattr(tool, "name")
        assert hasattr(tool, "description")
        assert tool.name == "create_care_plan"


class TestGetCarePlanTool:
    """Testes para tool de buscar plano."""

    @pytest.mark.asyncio
    async def test_get_existing_plan(self):
        """Testa buscar plano existente."""
        from geralda.engine.care_manager import CareManager

        care_manager = CareManager()

        # Criar plano primeiro
        plan = care_manager.create_plan(
            patient_id="pac-004",
            conditions=["DRC"],
            goals=["Controle"],
        )

        # Buscar
        tool = get_care_plan_tool(care_manager)
        result = await tool.arun(plan_id=plan.id)

        assert result["success"] is True
        assert result["plan"]["patient_id"] == "pac-004"

    @pytest.mark.asyncio
    async def test_get_nonexistent_plan(self):
        """Testa buscar plano inexistente."""
        from geralda.engine.care_manager import CareManager

        care_manager = CareManager()
        tool = get_care_plan_tool(care_manager)

        result = await tool.arun(plan_id="plano-inexistente")

        assert result["success"] is False
        assert "error" in result


class TestAddCareTaskTool:
    """Testes para tool de adicionar tarefa."""

    @pytest.mark.asyncio
    async def test_add_task_to_plan(self):
        """Testa adicionar tarefa a plano."""
        from geralda.engine.care_manager import CareManager

        care_manager = CareManager()

        # Criar plano
        plan = care_manager.create_plan(
            patient_id="pac-005",
            conditions=["DRC"],
            goals=["Controle"],
        )

        # Adicionar tarefa
        tool = add_care_task_tool(care_manager)
        result = await tool.arun(
            plan_id=plan.id,
            description="Tomar Losartana 50mg",
            category="medication",
            due_time="08:00",
        )

        assert result["success"] is True
        assert result["task"]["description"] == "Tomar Losartana 50mg"
        assert result["task"]["category"] == TaskCategory.MEDICATION

    @pytest.mark.asyncio
    async def test_add_task_with_due_date(self):
        """Testa adicionar tarefa com data de vencimento."""
        from geralda.engine.care_manager import CareManager

        care_manager = CareManager()

        plan = care_manager.create_plan(
            patient_id="pac-006",
            conditions=["DRC"],
            goals=["Controle"],
        )

        tool = add_care_task_tool(care_manager)
        due_date = date(2026, 3, 1)

        result = await tool.arun(
            plan_id=plan.id,
            description="Consulta com nefrologista",
            category="appointment",
            due_date=str(due_date),
        )

        assert result["success"] is True
        assert result["task"]["due_date"] == due_date

    @pytest.mark.asyncio
    async def test_add_task_invalid_category(self):
        """Testa adicionar tarefa com categoria inválida."""
        from geralda.engine.care_manager import CareManager

        care_manager = CareManager()

        plan = care_manager.create_plan(
            patient_id="pac-007",
            conditions=["DRC"],
            goals=["Controle"],
        )

        tool = add_care_task_tool(care_manager)

        # Categoria inválida deve ser tratada como "other"
        result = await tool.arun(
            plan_id=plan.id,
            description="Tarefa genérica",
            category="invalid_category",
        )

        assert result["success"] is True
        # Deve fallback para OTHER
        assert result["task"]["category"] == TaskCategory.OTHER


class TestCompleteTaskTool:
    """Testes para tool de completar tarefa."""

    @pytest.mark.asyncio
    async def test_complete_task(self):
        """Testa completar tarefa."""
        from geralda.engine.care_manager import CareManager

        care_manager = CareManager()

        # Criar plano e tarefa
        plan = care_manager.create_plan(
            patient_id="pac-008",
            conditions=["DRC"],
            goals=["Controle"],
        )

        task = care_manager.add_task(
            plan_id=plan.id,
            description="Tomar medicamento",
            category=TaskCategory.MEDICATION,
        )

        # Completar
        tool = complete_task_tool(care_manager)
        result = await tool.arun(task_id=task.id)

        assert result["success"] is True
        assert result["task"]["status"] == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_complete_nonexistent_task(self):
        """Testa completar tarefa inexistente."""
        from geralda.engine.care_manager import CareManager

        care_manager = CareManager()
        tool = complete_task_tool(care_manager)

        result = await tool.arun(task_id="task-inexistente")

        assert result["success"] is False
        assert "error" in result


class TestGetAdherenceTool:
    """Testes para tool de buscar adesão."""

    @pytest.mark.asyncio
    async def test_get_adherence_with_tasks(self):
        """Testa buscar adesão com tarefas."""
        from geralda.engine.care_manager import CareManager

        care_manager = CareManager()

        # Criar plano
        plan = care_manager.create_plan(
            patient_id="pac-009",
            conditions=["DRC"],
            goals=["Controle"],
        )

        # Adicionar tarefas
        care_manager.add_task(
            plan_id=plan.id,
            description="Tarefa 1",
            category=TaskCategory.MEDICATION,
        )
        care_manager.add_task(
            plan_id=plan.id,
            description="Tarefa 2",
            category=TaskCategory.MONITORING,
        )

        # Completar uma
        tasks = care_manager.get_tasks(plan.id)
        care_manager.complete_task(tasks[0].id)

        # Buscar adesão
        tool = get_adherence_tool(care_manager)
        result = await tool.arun(plan_id=plan.id)

        assert result["success"] is True
        assert "adherence" in result
        assert result["adherence"]["completion_rate"] == 50.0

    @pytest.mark.asyncio
    async def test_get_adherence_no_tasks(self):
        """Testa adesão sem tarefas."""
        from geralda.engine.care_manager import CareManager

        care_manager = CareManager()

        plan = care_manager.create_plan(
            patient_id="pac-010",
            conditions=["DRC"],
            goals=["Controle"],
        )

        tool = get_adherence_tool(care_manager)
        result = await tool.arun(plan_id=plan.id)

        assert result["success"] is True
        assert result["adherence"]["completion_rate"] == 0.0


class TestToolIntegration:
    """Testes de integração entre tools."""

    @pytest.mark.asyncio
    async def test_full_care_workflow(self):
        """Testa fluxo completo de cuidado com tools."""
        from geralda.engine.care_manager import CareManager

        care_manager = CareManager()

        # 1. Criar plano
        create_tool = create_care_plan_tool(care_manager)
        plan_result = await create_tool.arun(
            patient_id="pac-011",
            conditions=["DRC"],
            goals=["Controle"],
        )
        plan_id = plan_result["plan_id"]

        # 2. Adicionar tarefas
        add_tool = add_care_task_tool(care_manager)
        task1 = await add_tool.arun(
            plan_id=plan_id,
            description="Tarefa 1",
            category="medication",
        )
        task2 = await add_tool.arun(
            plan_id=plan_id,
            description="Tarefa 2",
            category="monitoring",
        )

        # 3. Completar uma tarefa
        complete_tool = complete_task_tool(care_manager)
        await complete_tool.arun(task_id=task1["task"]["id"])

        # 4. Verificar adesão
        adherence_tool = get_adherence_tool(care_manager)
        adherence = await adherence_tool.arun(plan_id=plan_id)

        assert adherence["adherence"]["completion_rate"] == 50.0
        assert adherence["adherence"]["total_tasks"] == 2

    @pytest.mark.asyncio
    async def test_all_tools_have_proper_metadata(self):
        """Testa que todas as tools têm metadados adequados."""
        from geralda.engine.care_manager import CareManager

        care_manager = CareManager()

        tools = [
            create_care_plan_tool(care_manager),
            get_care_plan_tool(care_manager),
            add_care_task_tool(care_manager),
            complete_task_tool(care_manager),
            get_adherence_tool(care_manager),
        ]

        for tool in tools:
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert len(tool.name) > 0
            assert len(tool.description) > 0
            assert hasattr(tool, "arun") or hasattr(tool, "run")
