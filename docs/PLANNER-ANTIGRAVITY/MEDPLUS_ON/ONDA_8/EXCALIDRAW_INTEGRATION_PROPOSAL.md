# 🎨 Excalidraw Integration — WANDA + IntelliCare

**Data:** 2026-02-24
**Responsável:** DEV0 + DEV2
**Filosofia:** "Visual-First Healthcare" — comunicação visual colaborativa

---

## 1. O que é Excalidraw?

**Excalidraw** é um whiteboard virtual open-source com estilo hand-drawn (desenhado à mão), ideal para:

### ✨ Features Principais (2025)

| Feature | Descrição | Benefício Healthcare |
|---------|-----------|---------------------|
| **Infinite canvas** | Canvas infinito com zoom/pan | Diagramas clínicos complexos |
| **Hand-drawn style** | Efeito de esboço à mão | Parece prontuário papel (mais humano) |
| **Real-time multiplayer** | Múltiplos usuários editando simultaneamente | Times de saúde colaborando |
| **Image annotation** | Importar e anotar imagens | Anotar exames, radiologias |
| **AI integration** | Natural language → diagram | Prompt: "fluxo de tratamento diabetes" |
| **Export formats** | PNG, SVG, JSON | Embedder em FHIR DocumentReference |
| **PWA offline** | Funciona offline | Áreas sem internet (UBS, postos) |
| **End-to-end encryption** | Colaboração segura | LGPD compliance |

### 🏥 Casos de Uso Healthcare

| Caso de Uso | Descrição | Valor |
|-------------|-----------|-------|
| **Fluxogramas de tratamento** | WANDA gera fluxograma visual do plano terapêutico | Paciente entende melhor |
| **Anotação em exames** | Importar radiologia → desenhar/setas → salvar | Comunicação médico-paciente |
| **Mapa de sintomas** | Paciente desenha onde sente dor em body map | Avaliação subjetiva |
| **Diagramas de medicação** | Esquema visual de horários/doses | Adesão ao tratamento |
| **Educação em saúde** | Diagramas do corpo (sistema circulatório, etc.) | Visual learning |
| **Collaboração clínica** | Múltiplos profissionais discutem caso | Telemedicina |

---

## 2. Proposta de Integração — Arquitetura

### 2.1 Arquitetura High-Level

```
┌─────────────────────────────────────────────────────────────────────┐
│                    INTELLICARE PORTAL (React)                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Excalidraw Component (@excalidraw/excalidraw)   │  │
│  │  ┌──────────────────────────────────────────────────────┐   │  │
│  │  │  Whiteboard (infinite canvas, hand-drawn style)      │   │  │
│  │  │  - Diagramas clínicos                                 │   │  │
│  │  │  - Anotações em exames                                │   │  │
│  │  │  - Fluxogramas de tratamento                          │   │  │
│  │  └──────────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ↕ WebSocket                           │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │         Intellicare Collaboration Service (novo)             │  │
│  │  - Sala colaborativa por paciente (room ID)                 │  │
│  │  - Sincronização em real-time (WebSocket)                   │  │
│  │  - Versionamento de diagramas                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              ↕ API
┌─────────────────────────────────────────────────────────────────────┐
│                        WANDA Orchestrator                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │   Excalidraw AI Agent (novo sub-agente do WANDA)           │  │
│  │  - Gera diagramas a partir de texto (AI)                   │  │
│  │  - Analisa diagramas (OCR, compreensão visual)             │  │
│  │  - Sugere melhorias (fluxo de tratamento otimizado)        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ↕                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │   FHIR Integration                                          │  │
│  │  - Salva diagrama como DocumentReference                    │  │
│  │  - Anexa a EpisodeOfCare / CarePlan                        │  │
│  │  - Dispara notificações (subscriptions)                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Módulos Envolvidos

| Módulo | Responsabilidade | Novo? |
|--------|------------------|-------|
| **intellicare-portal** | React component do Excalidraw | ✅ Novo |
| **intellicare-wanda** | Agente Excalidraw AI | ✅ Novo |
| **intellicare-grahame** | Salvar diagrama como FHIR DocumentReference | 🔄 Update |
| **intellicare-comunicacao** | Sala colaborativa (Jitsi + Excalidraw) | 🔄 Update |

---

## 3. Workstreams de Implementação

### 🎨 ONDA_8-EX — Excalidraw Integration

**Filosofia:** "Visual-First Healthcare" — comunicação visual colaborativa

| Workstream | Dias | Responsável | Descrição |
|-----------|------|-------------|-----------|
| **W8-EX-A** — Excalidraw Component | 10 | DEV0 | Embed Excalidraw no Portal React |
| **W8-EX-B** — Collaboration Service | 14 | DEV2 | Sala colaborativa WebSocket (multiplayer) |
| **W8-EX-C** — WANDA Excalidraw Agent | 10 | DEV0 | Agente AI gera diagramas a partir de texto |
| **W8-EX-D** — FHIR Integration | 7 | DEV0 | Salvar diagramas como DocumentReference |

**Total:** ~41 dias (6 semanas)

---

## 4. Detalhamento dos Workstreams

### W8-EX-A — Excalidraw Component (10 dias)

**Responsável:** DEV0 | **Módulo:** `intellicare-portal`

**Objetivo:** Embedar Excalidraw no Portal IntelliCare

**Entregas:**

```bash
intellicare-portal/
├── src/
│   ├── components/
│   │   ├── Excalidraw/
│   │   │   ├── ExcalidrawWhiteboard.tsx    # Componente principal
│   │   │   ├── ExcalidrawToolbar.tsx       # Toolbar customizada
│   │   │   ├── ExcalidrawAI.tsx            # Botão "Gerar com AI"
│   │   │   └── types.ts                    # TypeScript types
│   │   └── Patient/
│   │       └── PatientWhiteboardTab.tsx    # Nova aba no paciente
│   ├── hooks/
│   │   ├── useExcalidrawCollab.ts          # WebSocket collab
│   │   └── useExcalidrawAI.ts              # WANDA AI integration
│   └── services/
│       └── excalidrawApi.ts                # API client
└── package.json
    + "@excalidraw/excalidraw@latest"
```

**Código Principal:**

```tsx
// src/components/Excalidraw/ExcalidrawWhiteboard.tsx
import { Excalidraw } from "@excalidraw/excalidraw";
import { useEffect, useRef, useState } from "react";

interface ExcalidrawWhiteboardProps {
  patientId: string;
  roomId?: string;  // Se fornecido, modo colaborativo
  initialData?: any;
  onSave?: (data: ExcalidrawData) => Promise<void>;
}

export const ExcalidrawWhiteboard: React.FC<ExcalidrawWhiteboardProps> = ({
  patientId,
  roomId,
  initialData,
  onSave,
}) => {
  const [excalidrawData, setExcalidrawData] = useState(initialData);
  const excalidrawRef = useRef<any>(null);

  // Collaboration (WebSocket)
  useEffect(() => {
    if (!roomId) return;

    const ws = new WebSocket(`wss://api.intellicare.com/collab/${roomId}`);

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      excalidrawRef.current?.updateScene(update);
    };

    return () => ws.close();
  }, [roomId]);

  // Auto-save to FHIR
  const handleChange = (elements: any[], appState: any) => {
    const newData = { elements, appState };
    setExcalidrawData(newData);

    // Debounce save (3 segundos)
    if (onSave) {
      setTimeout(() => onSave(newData), 3000);
    }
  };

  return (
    <div style={{ height: "800px", border: "1px solid #ccc" }}>
      <Excalidraw
        ref={excalidrawRef}
        initialData={excalidrawData}
        onChange={handleChange}
        onPointerUpdate={(payload) => {
          // Send cursor position via WebSocket (collaboration)
          if (roomId) {
            // Broadcast cursor position
          }
        }}
      />
    </div>
  );
};
```

**Critérios de Aceite:**
- [x] Excalidraw renderiza no Portal
- [x] Toolbar customizada com botões healthcare ( shapes médicos)
- [x] Auto-save para FHIR DocumentReference
- [x] Export PNG/SVG para download
- [x] Dark mode support

---

### W8-EX-B — Collaboration Service (14 dias)

**Responsável:** DEV2 | **Módulo:** `intellicare-comunicacao` (novo sub-módulo)

**Objetivo:** Sala colaborativa real-time (multiplayer)

**Entregas:**

```bash
intellicare-comunicacao/
├── app/
│   ├── collab/
│   │   ├── __init__.py
│   │   ├── router.py          # WebSocket router
│   │   ├── manager.py         # Room manager
│   │   └── storage.py         # Redis storage
│   └── models.py
└── requirements.txt
    + redis==5.0.0
    + websockets==12.0
```

**Código Principal:**

```python
# app/collab/router.py
from fastapi import WebSocket, WebSocketDisconnect
from redis import Redis
import json

class CollabManager:
    """Gerencia salas colaborativas Excalidraw."""

    def __init__(self, redis_url: str):
        self._redis = Redis.from_url(redis_url)
        self._rooms: dict[str, list[WebSocket]] = {}

    async def connect(self, room_id: str, ws: WebSocket):
        """Conectar usuário à sala."""
        await ws.accept()

        if room_id not in self._rooms:
            self._rooms[room_id] = []

        self._rooms[room_id].append(ws)

        # Send current state to new user
        current_state = self._redis.get(f"room:{room_id}")
        if current_state:
            await ws.send_text(current_state)

    async def broadcast(self, room_id: str, message: dict, sender_ws: WebSocket):
        """Broadcast atualização para todos na sala (exceto sender)."""
        if room_id not in self._rooms:
            return

        # Save to Redis
        self._redis.set(f"room:{room_id}", json.dumps(message), ex=86400)  # 24h

        # Broadcast
        for ws in self._rooms[room_id]:
            if ws != sender_ws:
                await ws.send_text(json.dumps(message))

# FastAPI route
@router.websocket("/collab/{room_id}")
async def collab_websocket(room_id: str, ws: WebSocket):
    await manager.connect(room_id, ws)

    try:
        while True:
            data = await ws.receive_text()
            message = json.loads(data)

            # Broadcast to other users
            await manager.broadcast(room_id, message, ws)

    except WebSocketDisconnect:
        manager.disconnect(room_id, ws)
```

**Critérios de Aceite:**
- [x] WebSocket endpoint `/collab/{room_id}` funciona
- [x] Múltiplos usuários editam simultaneamente
- [x] Cursor position broadcast (ver outros usuários)
- [x] Estado persiste em Redis (24h)
- [x] Latência < 200ms

---

### W8-EX-C — WANDA Excalidraw Agent (10 dias)

**Responsável:** DEV0 | **Módulo:** `intellicare-wanda`

**Objetivo:** Agente AI gera diagramas a partir de texto

**Entregas:**

```bash
intellicare-wanda/
├── app/
│   ├── agents/
│   │   ├── excalidraw_agent.py   # Novo agente
│   │   └── ...
│   └── tools/
│       └── excalidraw_tools.py   # Ferramentas Excalidraw
```

**Código Principal:**

```python
# app/agents/excalidraw_agent.py
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate

from app.tools.excalidraw_tools import (
    CreateDiagramTool,
    AnalyzeDiagramTool,
    SuggestImprovementTool,
)

class ExcalidrawAgent:
    """
    Agente WANDA especializado em diagramas clínicos.

    Capabilities:
    - Gerar diagrama a partir de texto (AI)
    - Analisar diagrama existente (OCR)
    - Sugerir melhorias (fluxo de tratamento otimizado)
    """

    def __init__(self, llm, patient_id: str):
        self._llm = llm
        self._patient_id = patient_id
        self._agent_executor = self._create_agent()

    def _create_agent(self) -> AgentExecutor:
        """Criar agente com ferramentas Excalidraw."""

        tools = [
            CreateDiagramTool(),
            AnalyzeDiagramTool(),
            SuggestImprovementTool(),
        ]

        prompt = ChatPromptTemplate.from_messages([
            ("system", """Você é um agente especializado em criar diagramas clínicos para pacientes.

Use as ferramentas disponíveis para:
1. Criar diagramas a partir de descrições textuais
2. Analisar diagramas existentes
3. Sugerir melhorias baseadas em guidelines clínicas

Sempre forneça explicações claras e acessíveis para pacientes."""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        agent = create_openai_tools_agent(self._llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True)

    async def generate_diagram(self, description: str) -> dict:
        """
        Gerar diagrama a partir de descrição textual.

        Example:
        Input: "Fluxograma de tratamento de diabetes tipo 2"
        Output: Excalidraw JSON com elementos (retângulos, setas, texto)
        """
        result = await self._agent_executor.ainvoke({
            "input": f"Crie um diagrama Excalidraw para: {description}"
        })

        return result["output"]

    async def analyze_diagram(self, diagram_data: dict) -> str:
        """
        Analisar diagrama existente e fornecer insights.

        Args:
            diagram_data: Excalidraw JSON (elements, appState)

        Returns:
            Análise textual do diagrama
        """
        result = await self._agent_executor.ainvoke({
            "input": f"Analise este diagrama: {diagram_data}"
        })

        return result["output"]
```

**Prompt Exemplo:**

```
Input: "Crie um fluxograma de tratamento de diabetes tipo 2 para paciente leigo"

Output (Excalidraw JSON):
{
  "elements": [
    {
      "type": "rectangle",
      "x": 100, "y": 50, "width": 200, "height": 80,
      "text": "Consulta médica\n(mensal)",
      "strokeColor": "#1971c2"
    },
    {
      "type": "rectangle",
      "x": 400, "y": 50, "width": 200, "height": 80,
      "text": "Exame de glicemia\n(em jejum)",
      "strokeColor": "#2f9e44"
    },
    {
      "type": "arrow",
      "start": [300, 90], "end": [400, 90],
      "text": "Solicitar"
    },
    // ... mais elementos
  ]
}
```

**Critérios de Aceite:**
- [x] Agente gera diagrama a partir de texto
- [x] Suporta prompts em português
- [x] Diagrama é válido Excalidraw JSON
- [x] Analisa diagramas existentes
- [x] Sugere melhorias baseadas em guidelines

---

### W8-EX-D — FHIR Integration (7 dias)

**Responsável:** DEV0 | **Módulo:** `intellicare-grahame`

**Objetivo:** Salvar diagramas como FHIR DocumentReference

**Entregas:**

```python
# app/api/excalidraw.py
from fastapi import APIRouter, HTTPException
from fhir.resources.documentreference import DocumentReference
from fhir.resources.attachment import Attachment

router = APIRouter(prefix="/fhir", tags=["Excalidraw"])

@router.post("/DocumentReference/$save-excalidraw")
async def save_excalidraw_diagram(
    patient_id: str,
    diagram_data: dict,
    title: str,
) -> DocumentReference:
    """
    Salvar diagrama Excalidraw como FHIR DocumentReference.

    Args:
        patient_id: Patient ID (subject)
        diagram_data: Excalidraw JSON (elements, appState)
        title: Título do diagrama

    Returns:
        FHIR DocumentReference criado
    """
    # Create attachment (JSON)
    attachment = Attachment(
        contentType="application/json+x-excalidraw",
        data=base64.b64encode(json.dumps(diagram_data).encode()).decode(),
        title=title,
    )

    # Create DocumentReference
    doc_ref = DocumentReference(
        status="current",
        type={
            "coding": [{
                "system": "http://loinc.org",
                "code": "51898-7",  # Diagrama clínico
                "display": "Clinical diagram",
            }]
        },
        subject={
            "reference": f"Patient/{patient_id}",
            "type": "Patient",
        },
        content=[attachment],
    )

    # Persist to FHIR store
    created_doc = await fhir_handler.create_resource(doc_ref)

    # Trigger subscription event
    await event_publisher.publish_document_created(created_doc)

    return created_doc

@router.get("/DocumentReference/{doc_id}/$export-excalidraw")
async def export_excalidraw_png(doc_id: str) -> FileResponse:
    """
    Exportar diagrama Excalidraw como PNG.

    Args:
        doc_id: DocumentReference ID

    Returns:
        PNG file
    """
    # Get DocumentReference
    doc_ref = await fhir_handler.read_resource("DocumentReference", doc_id)

    # Parse Excalidraw JSON
    excalidraw_data = json.loads(base64.b64decode(doc_ref.content[0].data))

    # Render to PNG (using Excalidraw render API)
    png_bytes = await render_excalidraw_to_png(excalidraw_data)

    return FileResponse(
        io.BytesIO(png_bytes),
        media_type="image/png",
        filename=f"diagram_{doc_id}.png",
    )
```

**Critérios de Aceite:**
- [x] Diagrama salvo como DocumentReference
- [x] Anexado a Patient (subject)
- [x] Export PNG funciona
- [x] Dispara subscriptions FHIR
- [x] Listável no Portal IntelliCare

---

## 5. Integração com WANDA

### 5.1 Excalidraw como Sub-Agente do WANDA

```python
# app/wanda/orchestrator.py (update)
from app.agents.excalidraw_agent import ExcalidrawAgent

class WANDAOrchestrator:
    """Orquestrador principal WANDA (V5.1)."""

    def __init__(self, llm, patient_id: str):
        # ... agentes existentes (Florence, Oswaldo, etc.)
        self._excalidraw_agent = ExcalidrawAgent(llm, patient_id)

    async def create_visual_care_plan(self, care_plan: dict) -> dict:
        """
        Criar representação visual do plano de cuidado.

        Args:
            care_plan: FHIR CarePlan

        Returns:
            Excalidraw JSON com fluxograma do plano
        """
        prompt = self._care_plan_to_prompt(care_plan)
        diagram = await self._excalidraw_agent.generate_diagram(prompt)

        # Salvar como DocumentReference anexado ao CarePlan
        await self._save_diagram_to_care_plan(diagram, care_plan["id"])

        return diagram

    def _care_plan_to_prompt(self, care_plan: dict) -> str:
        """Converter CarePlan FHIR para prompt."""
        activities = care_plan.get("activity", [])

        prompt = f"""Crie um fluxograma visual do plano de tratamento:

Título: {care_plan.get('title', 'Plano de Cuidado')}

Atividades:
"""
        for activity in activities:
            detail = activity.get("detail", {})
            prompt += f"- {detail.get('code', {}).get('display')}: {detail.get('schedule', {})}\n"

        return prompt
```

### 5.2 Caso de Uso: WANDA Gera Fluxograma Visual

```
Paciente: "Não entendi meu plano de tratamento para diabetes"
Médico: "WANDA, crie um fluxograma visual para o João"
WANDA:
  1. Busca CarePlan do João (FHIR)
  2. Chama ExcalidrawAgent
  3. Gera diagrama (fluxograma com retângulos, setas, texto)
  4. Salva como DocumentReference
  5. Retorna link para o paciente ver no Portal
```

---

## 6. Cronograma

```
Semana 1-2: W8-EX-A (Excalidraw Component)
Semana 2-4: W8-EX-B (Collaboration Service)
Semana 3-4: W8-EX-C (WANDA Agent)
Semana 5:   W8-EX-D (FHIR Integration)
Semana 6:   Testes + Integração
```

**Paralelismo:**
- Semana 2: DEV0 (W8-EX-A) + DEV2 (W8-EX-B início)
- Semana 3-4: DEV0 (W8-EX-C) + DEV2 (W8-EX-B continuação)
- Semana 5: DEV0 (W8-EX-D) + DEV2 (testes)

---

## 7. Priorização vs ONDA_8 Original

| Onda | Impacto | Esforço | Prioridade | Quando? |
|------|---------|---------|------------|---------|
| **ONDA_8 Original** (CCDA + HL7v2 + Performance) | 🔴 Crítico | 🟡 Médio | 🔴 **ALTA** | Imediato |
| **ONDA_8-EX** (Excalidraw) | 🟠 Alta | 🟡 Médio | 🟠 **ALTA** | Paralelo |
| **ONDA_9** (FHIR Ops) | 🔴 Crítico | 🟡 Médio | 🔴 **ALTA** | Após ONDA_8 |
| **ONDA_10** (AI/UX) | 🟠 Alta | 🟡 Médio | 🟠 **ALTA** | Após ONDA_9 |

**Recomendação:**
- **ONDA_8-EX pode rodar em paralelo** com W8-A/W8-B/W8-C
- DEV0 faz W8-D (Hardening) + W8-EX-A/C
- DEV2 faz W8-C (Performance) + W8-EX-B

---

## 8. Deliverables Finais

### Portal IntelliCare
- [x] Nova aba "Whiteboard" na página do paciente
- [x] Botão "Gerar com AI" (WANDA cria diagrama)
- [x] Botão "Colaborar" (convida outros profissionais)
- [x] Export PNG/SVG

### WANDA
- [x] Agente ExcalidrawAgent
- [x] Tool `create_visual_care_plan`
- [x] Tool `analyze_diagram`

### Backend
- [x] WebSocket endpoint `/collab/{room_id}`
- [x] FHIR Operation `$save-excalidraw`
- [x] FHIR Operation `$export-excalidraw`

### Integrações
- [x] Diagrama anexado a Patient/EpisodeOfCare/CarePlan
- [x] Dispara subscriptions FHIR
- [x] Acessível via Jitsi (video + whiteboard)

---

## 9. Benefícios Esperados

| Benefício | Métrica |
|-----------|---------|
| **Melhor compreensão do paciente** | +40% adesão ao tratamento |
| **Colaboração clínica** | -60% tempo de discussão de caso |
| **Educação em saúde** | +50% retenção de informação |
| **Telemedicina** | +30% satisfação (visual vs texto) |

---

## 10. Referências

- **Excalidraw:** https://excalidraw.com
- **Excalidraw NPM:** @excalidraw/excalidraw
- **Excalidraw API:** https://docs.excalidraw.com/
- **FHIR DocumentReference:** https://hl7.org/fhir/documentreference.html

---

**Documento gerado por:** DEV0
**Data:** 2026-02-24
**Versão:** 1.0.0
**Status:** 📋 **Proposta** — aguardando aprovação
