# IntelliCare V3 — Fluxos Clínicos

> Última atualização: 2026-03-21 | Sprint 2026-04-18

---

## Fluxo completo de atendimento clínico

```mermaid
sequenceDiagram
    actor C as Clínico
    participant UI as ClinicoUI
    participant API as intellicare-service
    participant DB as PostgreSQL
    participant LLM as shared/llm.py
    participant PDF as WeasyPrint

    C->>UI: Abre agenda do dia
    UI->>API: GET /gestor/agenda?date=today
    API->>DB: SELECT encontros WHERE clinico_id=...
    DB-->>API: lista de consultas
    API-->>UI: consultas do dia

    C->>UI: Clica "Atender" no paciente
    UI->>API: POST /cuidado/encounters {patient_id}
    API->>DB: INSERT encounter (schema tenant)
    DB-->>API: encounter_id
    API-->>UI: encounter aberto

    C->>UI: Abre aba "Notas Florence"
    C->>UI: Preenche motivo + clica "Sugerir SOAP com IA"
    UI->>API: POST /florence/notes/suggest {encounter_id, chief_complaint}
    API->>LLM: _call_llm(prompt SOAP + contexto)
    alt LLM disponível
        LLM-->>API: sugestão SOAP estruturada
    else fallback rule-based
        LLM-->>API: template rule-based (baixa confiança)
    end
    API-->>UI: {subjective, objective, assessment, plan, model}
    C->>UI: Revisa e salva nota

    C->>UI: Abre aba "Prescrição Oswaldo"
    C->>UI: Clica "Sugerir com IA"
    UI->>API: POST /oswaldo/suggest {encounter_id, chief_complaint}
    API->>LLM: _call_llm(prompt prescrição + CID-10)
    LLM-->>API: {cid10_code, prescriptions[]}
    API-->>UI: sugestão de prescrição
    C->>UI: Confirma e salva prescrição

    C->>UI: Clica "Gerar PDF Clínico"
    UI->>API: GET /encontros/{id}/report.pdf
    API->>DB: get_encounter_full() — notas + prescrições
    DB-->>API: dados completos
    API->>PDF: render clinical_report.html (Jinja2)
    PDF-->>API: bytes PDF
    API-->>UI: PDF (Content-Type: application/pdf)
    C->>UI: Fecha encontro

    UI->>API: POST /cuidado/encounters/{id}/close
    API->>DB: UPDATE encounter status=closed
```

---

## Fluxo CarePlanner — jornada com fallback de canal

```mermaid
sequenceDiagram
    actor G as Gestor
    participant UI as GestorUI
    participant API as intellicare-service
    participant KESTRA as Kestra 0.20
    participant WA as Evolution API
    participant EMAIL as Listmonk
    participant PAC as Paciente

    G->>UI: Seleciona paciente + template "Confirmação Consulta"
    G->>UI: Escolhe flow "Jornada com Fallback" e dispara
    UI->>API: POST /journeys/trigger {flow_id: careplanner_jornada_com_fallback}
    API->>KESTRA: POST /executions {flow: jornada_com_fallback, inputs}
    KESTRA-->>API: execution_id
    API->>API: INSERT journey status=DISPATCHED

    KESTRA->>API: POST /careplanner/dispatch {channel: whatsapp}
    API->>WA: POST /message/sendText
    alt WhatsApp OK
        WA-->>API: message_id
        API->>KESTRA: resume (status: SENT)
        WA-->>PAC: mensagem WhatsApp
        PAC->>WA: responde "Sim"
        WA->>API: POST /webhook/whatsapp (inbound)
        API->>API: normalize_confirmation("Sim") → "SIM"
        API->>KESTRA: resume (normalized_response: SIM)
        KESTRA->>API: POST /appointments/{id}/confirm
        API-->>G: notificação "Consulta confirmada"
    else WhatsApp FAILED
        WA-->>API: FAILED
        API->>KESTRA: resume (status: FAILED)
        KESTRA->>API: POST /careplanner/dispatch {channel: email}
        API->>EMAIL: POST /api/subscribers + campaign
        EMAIL-->>PAC: e-mail de confirmação
    end
```

---

## Fluxo de notificações — SSE + Push PWA

```mermaid
flowchart TD
    subgraph EVENTO ["Evento no sistema"]
        E1[Mensagem CarePlanner recebida]
        E2[Jornada expirada]
        E3[Nota Florence criada]
    end

    subgraph NOTIF_SVC ["NotificationService"]
        PERSIST[Persiste no banco\nnotifications]
        PUBSUB[Publica no Redis\nPub/Sub channel: tenant_slug]
        PUSH[push_sender.py\nenvia via pywebpush]
    end

    subgraph ENTREGA ["Entrega ao usuário"]
        SSE[SSE Stream\n/notifications/stream\napp aberto]
        PWA[Push Nativo\nservice worker\napp fechado]
        BELL[NotificationBell\nbadge unread]
    end

    E1 & E2 & E3 --> PERSIST
    PERSIST --> PUBSUB
    PERSIST --> PUSH

    PUBSUB -->|Redis message| SSE
    SSE --> BELL

    PUSH -->|VAPID signed| PWA
    PWA -->|clique| BELL

    PUSH -->|410 GONE| REMOVE[Remove subscription\ndo banco automaticamente]

    style REMOVE fill:#fce8e6,stroke:#ea4335
    style PWA fill:#e8f4fd,stroke:#1a73e8
```

---

## Estados de jornada CarePlanner

```mermaid
stateDiagram-v2
    [*] --> CREATED: POST /journeys/trigger
    CREATED --> DISPATCHED: dispatcher processa
    DISPATCHED --> SENT: canal confirma entrega
    DISPATCHED --> FAILED: canal recusa / timeout
    SENT --> REPLIED: paciente responde
    SENT --> EXPIRED: sem resposta após 24h (retry backoff esgotado)
    REPLIED --> CLOSED: clínico ou sistema fecha
    FAILED --> DISPATCHED: fallback canal automático\n(jornada_com_fallback)
    CLOSED --> [*]
    EXPIRED --> [*]

    note right of FAILED
        Se flow = jornada_com_fallback:
        WA FAILED → tenta Email
        Email FAILED → EXPIRED
    end note

    note right of SENT
        Se flow = retry_com_backoff:
        sem resposta em 2h → reenvia
        sem resposta em 6h → reenvia
        sem resposta em 24h → EXPIRED
    end note
```
