# CONFIGURAÇÃO DO GOOGLE CALENDAR

## 📅 Calendário: INTELLICARE - Reuniões

**Responsável**: DEV1  
**Data de configuração**: 24/02/2026  
**Versão**: 1.0

---

## 1. CRIAÇÃO DO CALENDÁRIO

### Passos:
1. Acessar Google Calendar (https://calendar.google.com)
2. Clicar em "+" ao lado de "Outros calendários"
3. Selecionar "Criar novo calendário"
4. Preencher informações:
   - **Nome**: INTELLICARE - Reuniões
   - **Descrição**: Calendário de reuniões e validações do projeto INTELLICARE
   - **Fuso horário**: (UTC-03:00) Brasília

---

## 2. CONFIGURAÇÕES DO CALENDÁRIO

### Permissões de Compartilhamento:
- **DEV1**: Fazer alterações e gerenciar compartilhamento
- **DEV2**: Ver todos os detalhes do evento
- **Stakeholders**: Ver apenas livre/ocupado (privacidade)

### Notificações Padrão:
- **Email**: 1 dia antes (09:00)
- **Email**: 2 horas antes
- **Notificação**: 15 minutos antes

### Cores por Tipo de Evento:
- **Validações**: 🔴 Vermelho
- **Alinhamentos**: 🔵 Azul
- **Apresentações**: 🟢 Verde
- **Planejamento**: 🟡 Amarelo

---

## 3. TEMPLATES DE EVENTOS

### Template: Validação

```
Título: Validação [MÓDULO] - [FUNCIONALIDADE]
Data: [DD/MM/YYYY]
Horário: [HH:MM] - [HH:MM]
Local: Google Meet (link automático)

Descrição:
🎯 OBJETIVO
Validar [funcionalidade] do módulo [módulo] com especialista.

👥 PARTICIPANTES
- DEV1 (Facilitador)
- [Nome do Especialista] - [Área]

📋 AGENDA
10:00 - Abertura e contexto (5 min)
10:05 - Demonstração (30 min)
10:35 - Testes práticos (45 min)
11:20 - Discussão e feedback (30 min)
11:50 - Próximos passos (10 min)

📎 MATERIAIS
[Links para documentação]

✅ PREPARAÇÃO
- Ler documentação prévia
- Preparar perguntas

Convidados:
- [email do especialista]
- dev2@intellicare.com
```

### Template: Alinhamento

```
Título: Alinhamento DEV1 ↔ DEV2
Data: [DD/MM/YYYY]
Horário: [HH:MM] - [HH:MM] (15 min)
Local: Google Meet

Descrição:
📊 ALINHAMENTO DIÁRIO

Tópicos:
- Progresso técnico do dia
- Bloqueadores identificados
- Próximas prioridades
- Preparação para validações

Convidados:
- dev2@intellicare.com
```

### Template: Apresentação

```
Título: Apresentação [TEMA] - [PÚBLICO]
Data: [DD/MM/YYYY]
Horário: [HH:MM] - [HH:MM]
Local: Google Meet / Sala de Reuniões

Descrição:
🎤 APRESENTAÇÃO

Público-alvo: [Gestores/Técnicos/Especialistas]

Agenda:
- Introdução (5 min)
- Apresentação principal (30 min)
- Demo (15 min)
- Q&A (10 min)

Materiais:
- Slides: [link]
- Demo: [link]

Convidados:
[Lista de emails]
```

---

## 4. INTEGRAÇÃO COM SCRIPTS

### Script de Criação de Evento:

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def criar_evento_validacao(
    titulo: str,
    data: str,
    horario_inicio: str,
    duracao_minutos: int,
    participantes: list
):
    """
    Cria evento de validação no Google Calendar
    
    Nota: Requer autenticação OAuth2
    """
    # Configuração da API
    creds = Credentials.from_authorized_user_file('token.json')
    service = build('calendar', 'v3', credentials=creds)
    
    # Criar evento
    event = {
        'summary': titulo,
        'description': '...',
        'start': {
            'dateTime': f'{data}T{horario_inicio}:00',
            'timeZone': 'America/Sao_Paulo',
        },
        'end': {
            'dateTime': '...',
            'timeZone': 'America/Sao_Paulo',
        },
        'attendees': [{'email': email} for email in participantes],
        'conferenceData': {
            'createRequest': {'requestId': 'random-string'}
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'email', 'minutes': 120},
                {'method': 'popup', 'minutes': 15},
            ],
        },
    }
    
    event = service.events().insert(
        calendarId='primary',
        body=event,
        conferenceDataVersion=1
    ).execute()
    
    return event.get('htmlLink')
```

---

## 5. EVENTOS RECORRENTES

### Alinhamento Diário DEV1 ↔ DEV2:
- **Frequência**: Segunda a Sexta
- **Horário**: 17:00 - 17:15
- **Duração**: 15 minutos
- **Tipo**: Alinhamento

### Retrospectiva Semanal:
- **Frequência**: Sexta-feira
- **Horário**: 16:00 - 17:00
- **Duração**: 60 minutos
- **Tipo**: Planejamento

---

## 6. PRÓXIMOS EVENTOS AGENDADOS

### Semana 24-28/02/2026:

| Data | Horário | Evento | Participantes |
|------|---------|--------|---------------|
| 26/02 | 10:00-12:00 | Validação LGPD | DEV1, Dra. Maria Santos |
| 26/02 | 15:00-16:00 | Retrospectiva Semanal | DEV1, DEV2 |

---

## 7. BOAS PRÁTICAS

### Ao Criar Evento:
- ✅ Incluir objetivo claro na descrição
- ✅ Adicionar agenda com timebox
- ✅ Anexar materiais prévios
- ✅ Enviar com 48h de antecedência
- ✅ Incluir link do Google Meet
- ✅ Configurar lembretes adequados

### Ao Cancelar Evento:
- ✅ Notificar participantes com antecedência
- ✅ Explicar motivo do cancelamento
- ✅ Propor nova data se aplicável
- ✅ Atualizar documentação

### Ao Modificar Evento:
- ✅ Notificar todos os participantes
- ✅ Explicar mudanças realizadas
- ✅ Confirmar disponibilidade
- ✅ Atualizar materiais se necessário

---

**Configurado por**: DEV1  
**Data**: 24/02/2026  
**Status**: ✅ Configuração completa

