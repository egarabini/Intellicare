"""Templates seed para o sistema de comunicação."""

from __future__ import annotations

from datetime import UTC, datetime

from comunicacao.templates.models import MessageTemplate, TemplateVariant


def get_seed_templates() -> list[MessageTemplate]:
    """Retorna os 4 templates seed obrigatórios.

    Cada template tem 5 variantes de canal:
    - rocketchat
    - email
    - sms
    - whatsapp
    - jitsi
    """
    return [
        _clinical_alert_template(),
        _medication_reminder_template(),
        _teleconsult_invite_template(),
        _escalation_template(),
    ]


def _clinical_alert_template() -> MessageTemplate:
    """Template de alerta clínico."""
    return MessageTemplate(
        id="clinical_alert_generic",
        name="Alerta Clínico Genérico",
        category="clinical_alert",
        description="Usado para alertas clínicos gerais (queda de eGFR, valores críticos, etc)",
        version=1,
        active=True,
        params_schema={
            "type": "object",
            "required": ["patient_name", "alert_type", "message", "severity"],
            "properties": {
                "patient_name": {"type": "string"},
                "alert_type": {"type": "string"},
                "message": {"type": "string"},
                "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                "correlation_id": {"type": "string"},
                "source_module": {"type": "string"},
            },
        },
        sample_params={
            "patient_name": "Maria Silva",
            "alert_type": "Queda de eGFR",
            "message": "eGFR caiu de 45 para 32 ml/min/1.73m² em 90 dias",
            "severity": "high",
            "correlation_id": "CLN-2026-001234",
            "source_module": "intellicare-clinical",
        },
        channel_variants={
            "rocketchat": TemplateVariant(
                format="markdown",
                body=(
                    "🚨 **ALERTA CLÍNICO — {{severity}}**\n\n"
                    "**Paciente**: {{patient_name}}\n"
                    "**Tipo**: {{alert_type}}\n"
                    "**Mensagem**: {{message}}\n"
                    "**Módulo**: {{source_module}}\n"
                    "**Ref**: {{correlation_id}}"
                ),
            ),
            "email": TemplateVariant(
                format="html",
                subject="[IntelliCare] Alerta Clínico — {{patient_name}}",
                body=(
                    "<html><body>"
                    "<h2 style='color: #d32f2f;'>🚨 Alerta Clínico</h2>"
                    "<p><strong>Paciente:</strong> {{patient_name}}</p>"
                    "<p><strong>Tipo:</strong> {{alert_type}}</p>"
                    "<p><strong>Severidade:</strong> {{severity}}</p>"
                    "<p><strong>Mensagem:</strong> {{message}}</p>"
                    "<hr>"
                    "<p><small>Módulo: {{source_module}} | Ref: {{correlation_id}}</small></p>"
                    "</body></html>"
                ),
            ),
            "sms": TemplateVariant(
                format="plain",
                body="ALERTA {{severity}}: {{patient_name}} - {{alert_type}}. {{message}}",
                max_length=160,
            ),
            "whatsapp": TemplateVariant(
                format="whatsapp_template",
                body=(
                    "⚠️ *ALERTA CLÍNICO*\n\n"
                    "Paciente: {{patient_name}}\n"
                    "Tipo: {{alert_type}}\n"
                    "Severidade: {{severity}}\n\n"
                    "{{message}}\n\n"
                    "_Ref: {{correlation_id}}_"
                ),
            ),
            "jitsi": TemplateVariant(
                format="plain",
                title="Alerta Clínico — {{patient_name}}",
                body="{{alert_type}}: {{message}} (Severidade: {{severity}})",
            ),
        },
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _medication_reminder_template() -> MessageTemplate:
    """Template de lembrete de medicação."""
    return MessageTemplate(
        id="medication_reminder",
        name="Lembrete de Medicação",
        category="medication",
        description="Lembrete para paciente tomar medicação",
        version=1,
        active=True,
        params_schema={
            "type": "object",
            "required": ["patient_name", "medication_name", "dosage", "time"],
            "properties": {
                "patient_name": {"type": "string"},
                "medication_name": {"type": "string"},
                "dosage": {"type": "string"},
                "time": {"type": "string"},
                "instructions": {"type": "string"},
            },
        },
        sample_params={
            "patient_name": "João Santos",
            "medication_name": "Losartana",
            "dosage": "50mg",
            "time": "08:00",
            "instructions": "Tomar em jejum com água",
        },
        channel_variants={
            "rocketchat": TemplateVariant(
                format="markdown",
                body=(
                    "💊 **LEMBRETE DE MEDICAÇÃO**\n\n"
                    "**Paciente**: {{patient_name}}\n"
                    "**Medicamento**: {{medication_name}} — {{dosage}}\n"
                    "**Horário**: {{time}}\n"
                    "**Instruções**: {{instructions}}"
                ),
            ),
            "email": TemplateVariant(
                format="html",
                subject="[IntelliCare] Lembrete de Medicação — {{time}}",
                body=(
                    "<html><body>"
                    "<h2 style='color: #1976d2;'>💊 Lembrete de Medicação</h2>"
                    "<p>Olá, {{patient_name}}!</p>"
                    "<p>Está na hora de tomar sua medicação:</p>"
                    "<ul>"
                    "<li><strong>Medicamento:</strong> {{medication_name}}</li>"
                    "<li><strong>Dosagem:</strong> {{dosage}}</li>"
                    "<li><strong>Horário:</strong> {{time}}</li>"
                    "</ul>"
                    "<p><em>{{instructions}}</em></p>"
                    "</body></html>"
                ),
            ),
            "sms": TemplateVariant(
                format="plain",
                body="Lembrete: {{medication_name}} {{dosage}} às {{time}}. {{instructions}}",
                max_length=160,
            ),
            "whatsapp": TemplateVariant(
                format="whatsapp_template",
                body=(
                    "💊 *Lembrete de Medicação*\n\n"
                    "Olá, {{patient_name}}!\n\n"
                    "Está na hora de tomar:\n"
                    "• {{medication_name}} — {{dosage}}\n"
                    "• Horário: {{time}}\n\n"
                    "_{{instructions}}_"
                ),
            ),
            "jitsi": TemplateVariant(
                format="plain",
                title="Lembrete de Medicação — {{time}}",
                body="{{medication_name}} {{dosage}} — {{instructions}}",
            ),
        },
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )



def _teleconsult_invite_template() -> MessageTemplate:
    """Template de convite para teleconsulta."""
    return MessageTemplate(
        id="teleconsult_invite",
        name="Convite para Teleconsulta",
        category="teleconsult",
        description="Convite para paciente participar de teleconsulta via Jitsi",
        version=1,
        active=True,
        params_schema={
            "type": "object",
            "required": ["patient_name", "doctor_name", "date", "time", "room_url"],
            "properties": {
                "patient_name": {"type": "string"},
                "doctor_name": {"type": "string"},
                "specialty": {"type": "string"},
                "date": {"type": "string"},
                "time": {"type": "string"},
                "room_url": {"type": "string"},
                "room_name": {"type": "string"},
                "duration_minutes": {"type": "integer"},
            },
        },
        sample_params={
            "patient_name": "Ana Costa",
            "doctor_name": "Dr. Carlos Mendes",
            "specialty": "Nefrologia",
            "date": "2026-02-20",
            "time": "14:00",
            "room_url": "https://meet.gsi.srv.br/teleconsult-abc123",
            "room_name": "teleconsult-abc123",
            "duration_minutes": 30,
        },
        channel_variants={
            "rocketchat": TemplateVariant(
                format="markdown",
                body=(
                    "📹 **CONVITE PARA TELECONSULTA**\n\n"
                    "**Paciente**: {{patient_name}}\n"
                    "**Médico**: {{doctor_name}} ({{specialty}})\n"
                    "**Data**: {{date}} às {{time}}\n"
                    "**Duração**: {{duration_minutes}} minutos\n\n"
                    "🔗 **Link da sala**: {{room_url}}\n\n"
                    "_Clique no link acima no horário agendado._"
                ),
            ),
            "email": TemplateVariant(
                format="html",
                subject="[IntelliCare] Teleconsulta agendada — {{date}} {{time}}",
                body=(
                    "<html><body>"
                    "<h2 style='color: #388e3c;'>📹 Teleconsulta Agendada</h2>"
                    "<p>Olá, {{patient_name}}!</p>"
                    "<p>Você tem uma teleconsulta agendada:</p>"
                    "<ul>"
                    "<li><strong>Médico:</strong> {{doctor_name}} ({{specialty}})</li>"
                    "<li><strong>Data:</strong> {{date}}</li>"
                    "<li><strong>Horário:</strong> {{time}}</li>"
                    "<li><strong>Duração:</strong> {{duration_minutes}} minutos</li>"
                    "</ul>"
                    "<p><a href='{{room_url}}' style='background-color: #388e3c; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;'>Entrar na Sala</a></p>"
                    "<p><small>Link: {{room_url}}</small></p>"
                    "</body></html>"
                ),
            ),
            "sms": TemplateVariant(
                format="plain",
                body="Teleconsulta com {{doctor_name}} em {{date}} às {{time}}. Link: {{room_url}}",
                max_length=160,
            ),
            "whatsapp": TemplateVariant(
                format="whatsapp_template",
                body=(
                    "📹 *Teleconsulta Agendada*\n\n"
                    "Olá, {{patient_name}}!\n\n"
                    "Você tem uma consulta online:\n"
                    "• Médico: {{doctor_name}} ({{specialty}})\n"
                    "• Data: {{date}} às {{time}}\n"
                    "• Duração: {{duration_minutes}} min\n\n"
                    "🔗 Link da sala:\n{{room_url}}\n\n"
                    "_Clique no link no horário agendado._"
                ),
            ),
            "jitsi": TemplateVariant(
                format="jitsi_invite",
                title="Teleconsulta — {{doctor_name}}",
                body=(
                    "Teleconsulta agendada para {{date}} às {{time}}\n"
                    "Médico: {{doctor_name}} ({{specialty}})\n"
                    "Paciente: {{patient_name}}\n"
                    "Sala: {{room_name}}"
                ),
            ),
        },
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )



def _escalation_template() -> MessageTemplate:
    """Template de escalation para coordenadores."""
    return MessageTemplate(
        id="escalation_notification",
        name="Notificação de Escalation",
        category="escalation",
        description="Notifica coordenador sobre falha de entrega que requer atenção",
        version=1,
        active=True,
        params_schema={
            "type": "object",
            "required": ["original_intent_id", "patient_name", "failed_channels", "reason", "severity"],
            "properties": {
                "original_intent_id": {"type": "string"},
                "patient_name": {"type": "string"},
                "failed_channels": {"type": "array", "items": {"type": "string"}},
                "reason": {"type": "string"},
                "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                "original_message": {"type": "string"},
                "attempts_count": {"type": "integer"},
            },
        },
        sample_params={
            "original_intent_id": "intent-abc123",
            "patient_name": "Pedro Oliveira",
            "failed_channels": ["rocketchat", "email", "sms"],
            "reason": "all_channels_failed",
            "severity": "critical",
            "original_message": "Alerta clínico: eGFR crítico",
            "attempts_count": 9,
        },
        channel_variants={
            "rocketchat": TemplateVariant(
                format="markdown",
                body=(
                    "⚠️ **ESCALATION — ATENÇÃO NECESSÁRIA**\n\n"
                    "**Severidade**: {{severity}}\n"
                    "**Paciente**: {{patient_name}}\n"
                    "**Motivo**: {{reason}}\n"
                    "**Canais que falharam**: {{failed_channels}}\n"
                    "**Tentativas**: {{attempts_count}}\n\n"
                    "**Mensagem original**:\n{{original_message}}\n\n"
                    "**Intent ID**: `{{original_intent_id}}`\n\n"
                    "_Ação manual necessária para garantir entrega._"
                ),
            ),
            "email": TemplateVariant(
                format="html",
                subject="[IntelliCare] ESCALATION — {{severity}} — {{patient_name}}",
                body=(
                    "<html><body>"
                    "<h2 style='color: #ff6f00;'>⚠️ Escalation — Atenção Necessária</h2>"
                    "<p><strong>Severidade:</strong> <span style='color: #d32f2f;'>{{severity}}</span></p>"
                    "<p><strong>Paciente:</strong> {{patient_name}}</p>"
                    "<p><strong>Motivo:</strong> {{reason}}</p>"
                    "<p><strong>Canais que falharam:</strong> {{failed_channels}}</p>"
                    "<p><strong>Tentativas:</strong> {{attempts_count}}</p>"
                    "<hr>"
                    "<h3>Mensagem Original:</h3>"
                    "<p>{{original_message}}</p>"
                    "<hr>"
                    "<p><small>Intent ID: {{original_intent_id}}</small></p>"
                    "<p><em>Ação manual necessária para garantir entrega.</em></p>"
                    "</body></html>"
                ),
            ),
            "sms": TemplateVariant(
                format="plain",
                body="ESCALATION {{severity}}: Falha ao entregar msg para {{patient_name}}. Canais: {{failed_channels}}. Ação necessária.",
                max_length=160,
            ),
            "whatsapp": TemplateVariant(
                format="whatsapp_template",
                body=(
                    "⚠️ *ESCALATION — ATENÇÃO*\n\n"
                    "Severidade: *{{severity}}*\n"
                    "Paciente: {{patient_name}}\n"
                    "Motivo: {{reason}}\n"
                    "Canais falhados: {{failed_channels}}\n"
                    "Tentativas: {{attempts_count}}\n\n"
                    "*Mensagem original:*\n{{original_message}}\n\n"
                    "_Intent: {{original_intent_id}}_\n\n"
                    "Ação manual necessária."
                ),
            ),
            "jitsi": TemplateVariant(
                format="plain",
                title="Escalation — {{severity}} — {{patient_name}}",
                body=(
                    "Falha na entrega após {{attempts_count}} tentativas.\n"
                    "Canais: {{failed_channels}}\n"
                    "Motivo: {{reason}}\n"
                    "Intent: {{original_intent_id}}"
                ),
            ),
        },
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

