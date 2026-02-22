"""
Templates WhatsApp (D4).

Define templates pré-aprovados pela Meta para WhatsApp Business API.
"""

from typing import Dict, List, Any


# Templates WhatsApp pré-aprovados
WHATSAPP_TEMPLATES: Dict[str, Dict[str, Any]] = {
    # Template 1: Alerta Clínico
    "alerta_clinico": {
        "meta_template_name": "alerta_clinico_v1",
        "language": "pt_BR",
        "category": "UTILITY",
        "description": "Alerta clínico para profissionais de saúde",
        "params_count": 4,  # profissional, paciente, alerta, severidade
        "components": [
            {
                "type": "HEADER",
                "format": "TEXT",
                "text": "🚨 Alerta IntelliCare",
            },
            {
                "type": "BODY",
                "text": (
                    "Olá {{1}},\n\n"
                    "Alerta para o paciente {{2}}:\n"
                    "⚠️ {{3}}\n"
                    "Severidade: {{4}}\n\n"
                    "Por favor, verifique o caso com urgência."
                ),
                "example": {
                    "body_text": [
                        ["Dr. João", "Maria Santos", "eGFR < 30 ml/min", "CRÍTICA"]
                    ]
                },
            },
            {
                "type": "FOOTER",
                "text": "IntelliCare - Plataforma de Saúde Inteligente",
            },
            {
                "type": "BUTTONS",
                "buttons": [
                    {"type": "URL", "text": "Ver no Portal", "url": "https://portal.gsi.srv.br/alert/{{1}}"},
                    {"type": "QUICK_REPLY", "text": "Confirmar Leitura"},
                ],
            },
        ],
    },
    
    # Template 2: Convite Teleconsulta (para paciente)
    "teleconsulta_convite": {
        "meta_template_name": "teleconsulta_convite_v1",
        "language": "pt_BR",
        "category": "UTILITY",
        "description": "Convite de teleconsulta para paciente",
        "params_count": 4,  # paciente, profissional, data, horário
        "components": [
            {
                "type": "HEADER",
                "format": "TEXT",
                "text": "📹 Teleconsulta Agendada",
            },
            {
                "type": "BODY",
                "text": (
                    "Olá {{1}}!\n\n"
                    "Sua teleconsulta foi agendada:\n"
                    "👨‍⚕️ Profissional: {{2}}\n"
                    "📅 Data: {{3}}\n"
                    "🕐 Horário: {{4}}\n\n"
                    "Clique no botão abaixo para entrar na sala no horário marcado.\n\n"
                    "💡 Dicas:\n"
                    "• Use Wi-Fi ou 4G\n"
                    "• Fique em local silencioso\n"
                    "• Permita câmera e microfone"
                ),
                "example": {
                    "body_text": [
                        ["Maria Santos", "Dr. João Silva", "20/02/2026", "14:00"]
                    ]
                },
            },
            {
                "type": "BUTTONS",
                "buttons": [
                    {"type": "URL", "text": "Entrar na Sala", "url": "https://meet.gsi.srv.br/{{1}}"}
                ],
            },
        ],
    },
    
    # Template 3: Lembrete de Medicação
    "lembrete_medicacao": {
        "meta_template_name": "lembrete_medicacao_v1",
        "language": "pt_BR",
        "category": "UTILITY",
        "description": "Lembrete de medicação para paciente",
        "params_count": 3,  # paciente, medicamento, horário
        "components": [
            {
                "type": "BODY",
                "text": (
                    "Olá {{1}}! 💊\n\n"
                    "Lembrete: está na hora de tomar:\n"
                    "• {{2}}\n\n"
                    "Horário: {{3}}\n\n"
                    "Cuide-se! A regularidade no tratamento faz toda a diferença."
                ),
                "example": {
                    "body_text": [
                        ["Maria Santos", "Losartana 50mg", "08:00"]
                    ]
                },
            },
            {
                "type": "BUTTONS",
                "buttons": [
                    {"type": "QUICK_REPLY", "text": "✅ Tomei"},
                    {"type": "QUICK_REPLY", "text": "⏰ Lembrar depois"},
                ],
            },
        ],
    },
    
    # Template 4: Lembrete de Consulta
    "lembrete_consulta": {
        "meta_template_name": "lembrete_consulta_v1",
        "language": "pt_BR",
        "category": "UTILITY",
        "description": "Lembrete de consulta próxima",
        "params_count": 4,  # paciente, profissional, minutos, horário
        "components": [
            {
                "type": "BODY",
                "text": (
                    "Olá {{1}}!\n\n"
                    "Lembrete: sua teleconsulta com {{2}} "
                    "é em {{3}} minutos ({{4}}).\n\n"
                    "🔗 Acesse pelo link no botão abaixo.\n\n"
                    "Certifique-se de estar em local com boa conexão."
                ),
                "example": {
                    "body_text": [
                        ["Maria Santos", "Dr. João Silva", "15", "14:00"]
                    ]
                },
            },
            {
                "type": "BUTTONS",
                "buttons": [
                    {"type": "URL", "text": "Entrar na Sala", "url": "https://meet.gsi.srv.br/{{1}}"}
                ],
            },
        ],
    },
    
    # Template 5: Resultado de Exame
    "resultado_exame": {
        "meta_template_name": "resultado_exame_v1",
        "language": "pt_BR",
        "category": "UTILITY",
        "description": "Notificação de resultado de exame disponível",
        "params_count": 1,  # paciente
        "components": [
            {
                "type": "BODY",
                "text": (
                    "Olá {{1}}!\n\n"
                    "Seus resultados de exame foram analisados pelo seu médico.\n\n"
                    "Para ver os detalhes, acesse o portal do paciente "
                    "ou entre em contato com sua equipe de saúde.\n\n"
                    "Em caso de urgência, procure a unidade de saúde mais próxima."
                ),
                "example": {
                    "body_text": [
                        ["Maria Santos"]
                    ]
                },
            },
        ],
    },
}


def get_template(template_name: str) -> Dict[str, Any]:
    """
    Obtém template por nome.

    Args:
        template_name: Nome do template.

    Returns:
        Dict: Template.

    Raises:
        KeyError: Se template não existir.
    """
    return WHATSAPP_TEMPLATES[template_name]


def list_templates() -> List[str]:
    """
    Lista nomes de todos os templates.

    Returns:
        List[str]: Nomes dos templates.
    """
    return list(WHATSAPP_TEMPLATES.keys())

