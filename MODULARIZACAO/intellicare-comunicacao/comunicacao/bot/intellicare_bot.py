"""Bot @intellicare para Rocket.Chat - Command Processor."""

from __future__ import annotations

import logging
from typing import Any

from comunicacao.rocketchat.client import RocketChatClient
from comunicacao.rocketchat.config import RocketChatConfig

logger = logging.getLogger(__name__)


class IntelliCareBot:
    """
    Bot @intellicare para Rocket.Chat.
    
    Processa comandos clínicos enviados via mensagens no RC:
    - /paciente {patient_id} - Mostra informações do paciente
    - /alerta {alert_id} - Mostra detalhes do alerta
    - /lab {patient_id} - Mostra resultados de laboratório
    - /teleconsulta {patient_id} - Cria sala Jitsi para teleconsulta
    - /escalar {alert_id} - Escala alerta para nível superior
    - /ajuda - Mostra comandos disponíveis
    """
    
    def __init__(
        self,
        rc_client: RocketChatClient | None = None,
        rc_config: RocketChatConfig | None = None,
    ):
        """
        Inicializa bot.
        
        Args:
            rc_client: Cliente RC (se None, cria novo)
            rc_config: Config RC (se None, usa from_env())
        """
        config = rc_config or RocketChatConfig.from_env()
        self.rc_client = rc_client or RocketChatClient(config)
        
        # Mapeamento de roles permitidas por comando
        self.command_permissions = {
            "paciente": ["doctor", "nurse", "care_coordinator", "admin"],
            "alerta": ["doctor", "nurse", "care_coordinator", "admin"],
            "lab": ["doctor", "nurse", "admin"],
            "teleconsulta": ["doctor", "nurse", "care_coordinator", "admin"],
            "escalar": ["doctor", "care_coordinator", "admin"],
            "ajuda": ["user"],  # Todos podem ver ajuda
        }
        
        logger.info("IntelliCareBot inicializado")
    
    def _check_permission(self, command: str, user_roles: list[str]) -> bool:
        """
        Verifica se usuário tem permissão para executar comando.
        
        Args:
            command: Nome do comando
            user_roles: Roles do usuário
        
        Returns:
            True se tem permissão
        """
        allowed_roles = self.command_permissions.get(command, [])
        
        # Admin sempre tem permissão
        if "admin" in user_roles or "intellicare_admin" in user_roles:
            return True
        
        # Verificar se alguma role do usuário está na lista de permitidas
        return any(role in allowed_roles for role in user_roles)
    
    async def handle_ajuda(self, args: list[str], context: dict[str, Any]) -> str:
        """
        Handler para comando /ajuda.
        
        Args:
            args: Argumentos do comando
            context: Contexto da mensagem (user_id, channel_id, etc.)
        
        Returns:
            Texto de resposta
        """
        logger.info("Comando /ajuda executado por %s", context["user_name"])
        
        help_text = """
🤖 **IntelliCare Bot - Comandos Disponíveis**

**Pacientes**:
• `/paciente {patient_id}` - Mostra informações do paciente
• `/lab {patient_id}` - Mostra resultados de laboratório recentes

**Alertas**:
• `/alerta {alert_id}` - Mostra detalhes do alerta clínico
• `/escalar {alert_id}` - Escala alerta para nível superior

**Teleconsulta**:
• `/teleconsulta {patient_id}` - Cria sala Jitsi para teleconsulta

**Ajuda**:
• `/ajuda` - Mostra esta mensagem

---
💡 **Dica**: Use os comandos em canais de caso ou alertas para acesso rápido às informações.
        """.strip()
        
        return help_text
    
    async def handle_paciente(self, args: list[str], context: dict[str, Any]) -> str:
        """
        Handler para comando /paciente {patient_id}.
        
        Args:
            args: [patient_id]
            context: Contexto da mensagem
        
        Returns:
            Texto de resposta
        """
        logger.info("Comando /paciente executado por %s", context["user_name"])
        
        # Validar argumentos
        if not args:
            return "❌ **Uso**: `/paciente {patient_id}`\n\nExemplo: `/paciente patient-123`"
        
        patient_id = args[0]
        
        # TODO: Integrar com módulo oswaldo para buscar dados do paciente
        # Por enquanto, retornar resposta simulada
        
        response = f"""
📋 **Informações do Paciente**

**ID**: `{patient_id}`
**Nome**: Maria Santos (exemplo)
**Idade**: 65 anos
**Condições**: Hipertensão, Diabetes Tipo 2
**Última Consulta**: 2026-02-15

**Alertas Ativos**: 2
• Glicemia elevada (120 mg/dL)
• Pressão arterial alta (150/95 mmHg)

---
💡 Use `/lab {patient_id}` para ver resultados de laboratório.
        """.strip()

        return response

    async def handle_lab(self, args: list[str], context: dict[str, Any]) -> str:
        """
        Handler para comando /lab {patient_id}.

        Args:
            args: [patient_id]
            context: Contexto da mensagem

        Returns:
            Texto de resposta
        """
        logger.info("Comando /lab executado por %s", context["user_name"])

        # Validar argumentos
        if not args:
            return "❌ **Uso**: `/lab {patient_id}`\n\nExemplo: `/lab patient-123`"

        patient_id = args[0]

        # TODO: Integrar com módulo oswaldo para buscar resultados de lab

        response = f"""
🔬 **Resultados de Laboratório**

**Paciente**: `{patient_id}`
**Data**: 2026-02-16

**Glicemia**:
• Jejum: 120 mg/dL ⚠️ (ref: 70-100)
• Pós-prandial: 180 mg/dL ⚠️ (ref: <140)

**Hemograma**:
• Hemoglobina: 13.5 g/dL ✅
• Leucócitos: 7.200/mm³ ✅
• Plaquetas: 250.000/mm³ ✅

**Função Renal**:
• Creatinina: 1.1 mg/dL ✅
• Ureia: 35 mg/dL ✅

---
⚠️ **Atenção**: Glicemia elevada - considerar ajuste de medicação.
        """.strip()

        return response

    async def handle_alerta(self, args: list[str], context: dict[str, Any]) -> str:
        """
        Handler para comando /alerta {alert_id}.

        Args:
            args: [alert_id]
            context: Contexto da mensagem

        Returns:
            Texto de resposta
        """
        logger.info("Comando /alerta executado por %s", context["user_name"])

        # Validar argumentos
        if not args:
            return "❌ **Uso**: `/alerta {alert_id}`\n\nExemplo: `/alerta alert-456`"

        alert_id = args[0]

        # TODO: Integrar com módulo florence para buscar detalhes do alerta

        response = f"""
🚨 **Detalhes do Alerta Clínico**

**ID**: `{alert_id}`
**Severidade**: 🔴 **ALTA**
**Status**: Ativo
**Criado em**: 2026-02-17 09:30

**Paciente**: Maria Santos (patient-123)
**Tipo**: Glicemia Crítica
**Valor**: 250 mg/dL (ref: 70-100)

**Protocolo Sugerido**:
1. Verificar sintomas de hiperglicemia
2. Ajustar dose de insulina
3. Agendar consulta urgente
4. Monitorar glicemia a cada 2h

**Responsável**: Dr. João Silva
**Equipe**: UBS Centro

---
💡 Use `/escalar {alert_id}` para escalar para coordenação.
        """.strip()

        return response

    async def handle_escalar(self, args: list[str], context: dict[str, Any]) -> str:
        """
        Handler para comando /escalar {alert_id}.

        Args:
            args: [alert_id]
            context: Contexto da mensagem

        Returns:
            Texto de resposta
        """
        logger.info("Comando /escalar executado por %s", context["user_name"])

        # Validar argumentos
        if not args:
            return "❌ **Uso**: `/escalar {alert_id}`\n\nExemplo: `/escalar alert-456`"

        alert_id = args[0]

        # TODO: Integrar com engine de roteamento para escalar alerta

        response = f"""
⬆️ **Alerta Escalado**

**ID**: `{alert_id}`
**Escalado por**: {context["user_name"]}
**Data**: 2026-02-17 10:45

**Ação Tomada**:
✅ Alerta escalado para **Coordenação de Cuidados**
✅ Notificação enviada para coordenador
✅ Prioridade aumentada para **CRÍTICA**

**Próximos Passos**:
• Coordenador será notificado em até 5 minutos
• Caso não haja resposta em 15 min, escalar para gestor
• Acompanhar evolução no canal #alertas-clinicos

---
📞 Em caso de emergência, acionar SAMU: 192
        """.strip()

        return response

    async def handle_teleconsulta(self, args: list[str], context: dict[str, Any]) -> str:
        """
        Handler para comando /teleconsulta {patient_id}.

        Args:
            args: [patient_id]
            context: Contexto da mensagem

        Returns:
            Texto de resposta
        """
        logger.info("Comando /teleconsulta executado por %s", context["user_name"])

        # Validar argumentos
        if not args:
            return "❌ **Uso**: `/teleconsulta {patient_id}`\n\nExemplo: `/teleconsulta patient-123`"

        patient_id = args[0]

        # TODO: Integrar com módulo de teleconsulta para criar sala Jitsi

        # Gerar ID de sala
        room_id = f"tc-{patient_id}-{context['user_name']}"
        jitsi_url = f"https://meet.gsi.srv.br/{room_id}"

        response = f"""
📹 **Sala de Teleconsulta Criada**

**Paciente**: `{patient_id}`
**Criado por**: {context["user_name"]}
**Data**: 2026-02-17 10:50

**Link da Sala**:
🔗 {jitsi_url}

**Instruções**:
1. Clique no link acima para entrar na sala
2. Aguarde o paciente conectar
3. A sala ficará ativa por 2 horas
4. Gravação automática habilitada (LGPD)

**Participantes Convidados**:
• {context["user_name"]} (você)
• Paciente (link enviado via SMS)

---
💡 A sala será arquivada automaticamente após o término.
        """.strip()

        return response
