# 🎨 Excalidraw — Especificação de Integração com WANDA

**Feature ID:** EF-W020
**Módulo:** `intellicare-wanda` + `intellicare-pierre` (Tool nova)
**Data:** 2026-02-25
**Status:** PROPOSTA — aguarda aprovação

---

## 1. Visão Geral

Integrar [Excalidraw](https://excalidraw.com) como ferramenta de geração de diagramas visuais na Wanda, exposta como **nova MCP Tool** dentro do `intellicare-pierre` (seguindo o padrão existente). A Wanda poderá invocar essa tool para criar representações visuais clínicas: planos de cuidado, timelines de medicamentos, fluxos de triagem e relatórios de métricas.

### Por que Excalidraw?
- **Open-source** — MIT License, sem custo de licença
- **Saída como JSON** — formato `.excalidraw` (JSON puro) facilmente gerado programaticamente
- **CLI headless** — conversão para PNG/SVG sem browser via `@excalidraw/utils` (Node.js)
- **Estética clínica** — visual hand-drawn humaniza a interface com o paciente
- **Formato embeddável** — arquivos PNG podem ser anexados em mensagens WhatsApp (via WAHA/Meta), e-mail e portal

---

## 2. Arquitetura de Integração

```
WANDA (LLM)
  │
  │ decide gerar diagrama
  ▼
MCP Tool: create_diagram (pierre)
  │
  ├── Monta JSON .excalidraw (Python)
  │     └── Elements: rectangles, arrows, text, groups
  │
  └── Chama ExcalidrawRenderer (Node.js CLI via subprocess)
        └── Gera PNG/SVG

WANDA recebe:
  - diagram_json: str (.excalidraw)
  - image_base64: str (PNG para embed)
  - image_url: str (se storage S3/MinIO disponível)
```

### Componentes

| Componente | Tecnologia | Localização |
|---|---|---|
| `ExcalidrawBuilder` | Python (dataclasses) | `pierre/diagram/builder.py` |
| `ExcalidrawRenderer` | Node.js (subprocess) | `pierre/diagram/renderer.py` |
| MCP Tool `create_diagram` | FastAPI + MCP | `pierre/mcp/tools/create_diagram.py` |
| MCP Tool `render_diagram` | FastAPI + MCP | `pierre/mcp/tools/render_diagram.py` |
| Docker sidecar Node.js | `node:20-slim` | `intellicare-pierre/Dockerfile` |

---

## 3. Funcionalidades

### 3.1 Tool: `create_diagram`

Gera um diagrama Excalidraw a partir de dados estruturados.

**Input:**
```json
{
  "diagram_type": "care_plan | medication_timeline | triage_flow | measure_report | custom",
  "title": "Plano de Cuidado — Jose Silva",
  "data": {
    "nodes": [
      {"id": "n1", "label": "Hipertensão", "type": "condition", "severity": "high"},
      {"id": "n2", "label": "Losartana 50mg", "type": "medication"},
      {"id": "n3", "label": "Consulta Cardiologista", "type": "appointment", "date": "2026-03-10"}
    ],
    "edges": [
      {"from": "n1", "to": "n2", "label": "trata"},
      {"from": "n1", "to": "n3", "label": "encaminha"}
    ]
  },
  "render_to_png": true,
  "theme": "light | dark | clinical"
}
```

**Output:**
```json
{
  "diagram_json": "{\"type\":\"excalidraw\", \"elements\": [...]}",
  "image_base64": "iVBORw0KGgoAAAANS...",
  "image_format": "png",
  "element_count": 7,
  "render_time_ms": 450
}
```

### 3.2 Tool: `render_diagram`

Renderiza um `.excalidraw` JSON existente para PNG (uso quando Wanda recebe diagrama externo).

**Input:**
```json
{
  "diagram_json": "{\"type\":\"excalidraw\", ...}",
  "format": "png | svg",
  "width": 1200,
  "background": "white | transparent"
}
```

### 3.3 Tipos de Diagrama Pré-definidos

| Tipo | Descrição | FHIR Resources usados |
|---|---|---|
| `care_plan` | Condições → Intervenções → Objetivos | Condition, CarePlan, Goal |
| `medication_timeline` | Timeline horizontal de medicamentos | MedicationRequest, MedicationAdministration |
| `triage_flow` | Fluxo de triagem (sintoma → avaliação → ação) | Encounter, Observation, ServiceRequest |
| `measure_report` | Indicadores como gráfico de barras/pizza | MeasureReport |
| `custom` | Livre — dados no formato nodes/edges | Qualquer |

---

## 4. Especificação Técnica

### 4.1 ExcalidrawBuilder (Python)

```python
# pierre/diagram/builder.py

from dataclasses import dataclass, field
from typing import Literal
import uuid
import json

ElementType = Literal["rectangle", "ellipse", "arrow", "text", "diamond"]
Theme = Literal["light", "dark", "clinical"]

@dataclass
class ExcalidrawElement:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: ElementType = "rectangle"
    x: float = 0.0
    y: float = 0.0
    width: float = 160.0
    height: float = 60.0
    label: str = ""
    stroke_color: str = "#1e1e1e"
    background_color: str = "#ffffff"
    roughness: int = 1          # 0=smooth, 1=sketchy (padrão Excalidraw)
    font_size: int = 16
    arrow_from: str | None = None
    arrow_to: str | None = None

    def to_excalidraw(self) -> dict:
        """Serializa para formato Excalidraw JSON."""
        ...


class ExcalidrawBuilder:
    """Builder fluente para diagramas Excalidraw."""

    CLINICAL_PALETTE = {
        "condition": {"stroke": "#c0392b", "bg": "#fadbd8"},   # vermelho suave
        "medication": {"stroke": "#1a5276", "bg": "#d6eaf8"},  # azul suave
        "appointment": {"stroke": "#1e8449", "bg": "#d5f5e3"}, # verde suave
        "goal": {"stroke": "#7d3c98", "bg": "#e8daef"},        # roxo suave
        "default": {"stroke": "#2c3e50", "bg": "#f8f9fa"},
    }

    def care_plan_diagram(self, nodes: list[dict], edges: list[dict], title: str) -> str:
        """Gera diagrama de plano de cuidado."""
        ...

    def medication_timeline(self, medications: list[dict], period_days: int = 30) -> str:
        """Gera timeline horizontal de medicamentos."""
        ...

    def triage_flow(self, steps: list[dict]) -> str:
        """Gera fluxograma de triagem."""
        ...

    def measure_report(self, measures: list[dict]) -> str:
        """Gera gráfico de indicadores (barras horizontais)."""
        ...

    def to_json(self) -> str:
        """Serializa para .excalidraw JSON string."""
        return json.dumps({
            "type": "excalidraw",
            "version": 2,
            "source": "intellicare-pierre",
            "elements": [e.to_excalidraw() for e in self._elements],
            "appState": {"theme": "light", "gridModeEnabled": False},
            "files": {},
        }, ensure_ascii=False)
```

### 4.2 ExcalidrawRenderer (Node.js via subprocess)

```python
# pierre/diagram/renderer.py

import asyncio
import base64
import json
import tempfile
from pathlib import Path

class ExcalidrawRenderer:
    """
    Renderiza .excalidraw JSON para PNG/SVG via Node.js CLI.

    Requer: node >= 20, @excalidraw/utils instalado globalmente no Docker.
    Comando: node /app/excalidraw_render.js <input.excalidraw> <output.png>
    """

    SCRIPT_PATH = "/app/excalidraw_render.js"
    TIMEOUT_SECONDS = 15

    async def render_to_png(
        self,
        diagram_json: str,
        width: int = 1200,
        background: str = "white",
    ) -> bytes:
        """Renderiza diagrama para PNG e retorna bytes."""
        with tempfile.NamedTemporaryFile(suffix=".excalidraw", delete=False) as f:
            f.write(diagram_json.encode())
            input_path = f.name

        output_path = input_path.replace(".excalidraw", ".png")

        try:
            proc = await asyncio.create_subprocess_exec(
                "node", self.SCRIPT_PATH,
                "--input", input_path,
                "--output", output_path,
                "--width", str(width),
                "--background", background,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(proc.communicate(), timeout=self.TIMEOUT_SECONDS)

            if proc.returncode != 0:
                raise RuntimeError(f"Renderer failed: {proc.returncode}")

            return Path(output_path).read_bytes()
        finally:
            Path(input_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)

    async def is_available(self) -> bool:
        """Verifica se Node.js e o script estão disponíveis."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "node", "--version",
                stdout=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(proc.communicate(), timeout=3)
            return proc.returncode == 0
        except Exception:
            return False
```

### 4.3 Script Node.js de Renderização

```javascript
// /app/excalidraw_render.js
// Uso: node excalidraw_render.js --input in.excalidraw --output out.png

const { exportToSvg, exportToBlob } = require("@excalidraw/utils");
const fs = require("fs");
const { createCanvas } = require("canvas");

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, val, i, arr) => {
    if (val.startsWith("--")) acc.push([val.slice(2), arr[i + 1]]);
    return acc;
  }, [])
);

const diagramData = JSON.parse(fs.readFileSync(args.input, "utf8"));

exportToBlob({
  elements: diagramData.elements,
  appState: { ...diagramData.appState, exportWithDarkMode: false },
  files: diagramData.files ?? {},
  mimeType: "image/png",
  quality: 0.95,
}).then((blob) => blob.arrayBuffer()).then((buf) => {
  fs.writeFileSync(args.output, Buffer.from(buf));
  process.exit(0);
}).catch((err) => {
  console.error(err.message);
  process.exit(1);
});
```

### 4.4 Integração com MCPClientConfig (Wanda)

Nenhuma mudança necessária no `MCPClientConfig` — as tools `create_diagram` e `render_diagram` são adicionadas ao PIERRE e a Wanda as descobre automaticamente via `list_tools()` no startup.

A Wanda precisará de uma atualização no `MCP_TOOL_DESCRIPTIONS` em `tool_registry.py`:

```python
# Adicionar ao dict existente:
"create_diagram": (
    "Cria diagrama visual clínico (plano de cuidado, timeline de medicamentos, "
    "fluxo de triagem, indicadores). Retorna imagem PNG em base64 e JSON Excalidraw. "
    "Use quando o usuário pede visualização, gráfico ou mapa de condições clínicas."
),
"render_diagram": (
    "Renderiza um diagrama Excalidraw JSON existente para PNG/SVG. "
    "Use quando você já tem o JSON e precisa gerar a imagem."
),
```

### 4.5 Dockerfile atualizado (pierre)

```dockerfile
# Multi-stage: instalar dependências Node.js no build
FROM node:20-slim AS node-deps
WORKDIR /app
RUN npm install -g @excalidraw/utils canvas
COPY excalidraw_render.js /app/excalidraw_render.js

FROM python:3.11-slim
# Copiar node + script do stage anterior
COPY --from=node-deps /usr/local/bin/node /usr/local/bin/node
COPY --from=node-deps /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=node-deps /app/excalidraw_render.js /app/excalidraw_render.js

# ... resto do Dockerfile existente ...
```

---

## 5. Casos de Uso — Wanda em Ação

### UC1: Médico pede resumo visual do plano de cuidado

```
Usuário: "Wanda, me mostra o plano de cuidado do paciente José Silva"

Wanda:
1. Busca Patient/$everything (FHIR) → obtem Conditions, CarePlan, Goals
2. Chama create_diagram(type="care_plan", data={nodes, edges})
3. Recebe PNG base64
4. Responde com texto + envia imagem via WhatsApp (WAHA/Meta)
```

### UC2: Enfermeira verifica timeline de medicamentos

```
Usuário: "Quais medicamentos o paciente está tomando este mês?"

Wanda:
1. Busca MedicationRequest/$patient (FHIR)
2. Chama create_diagram(type="medication_timeline", period_days=30)
3. Envia timeline visual com datas de início/fim de cada medicamento
```

### UC3: Gestor solicita indicadores de qualidade

```
Usuário: "Como estão os indicadores do mês?"

Wanda:
1. Chama Measure/$evaluate-measure (FHIR, Grahame)
2. Chama create_diagram(type="measure_report", data=measure_reports)
3. Retorna gráfico de barras com % de metas atingidas
```

---

## 6. Impacto nos Módulos Existentes

| Módulo | Mudança | Esforço |
|---|---|---|
| `intellicare-pierre` | +2 MCP tools, +2 arquivos Python, +1 JS, Dockerfile multi-stage | 3-4 dias |
| `intellicare-wanda` | +2 entradas em `MCP_TOOL_DESCRIPTIONS`, zero mudança de roteamento | 30 min |
| `intellicare-grahame` | Nenhuma — usa API FHIR existente | Zero |
| `intellicare-comunicacao` | Nenhuma — PNG é serializado como base64 e enviado pelo canal existente | Zero |
| `docker-compose.yml` do stack | Nenhuma — Pierre já está no stack | Zero |

**Impacto TOTAL no MEDPLUS_ON roadmap: zero** — Excalidraw é uma feature ortogonal que adiciona capacidade de output visual sem interferir nas Ondas 1-4.

---

## 7. Plano de Implementação — 4 dias (DEV PIERRE)

| Dia | Tarefa | Entregável |
|---|---|---|
| **Dia 1** | `ExcalidrawBuilder` Python para `care_plan` + `medication_timeline` | 2 tipos de diagrama funcionando como JSON |
| **Dia 2** | Script Node.js `excalidraw_render.js` + `ExcalidrawRenderer` + Dockerfile multi-stage | Renderização PNG funcional |
| **Dia 3** | MCP Tools `create_diagram` + `render_diagram` + testes (10 cenários) | Tools registradas no PIERRE |
| **Dia 4** | Tipos `triage_flow` + `measure_report` + integração E2E Wanda→PIERRE→PNG | Feature completa |

### Dependências

| Dependência | Como instalar | Custo |
|---|---|---|
| `@excalidraw/utils` | `npm install` no Docker | Gratuito |
| `canvas` (node-canvas) | `npm install canvas` | Gratuito |
| Node.js 20 | Base image `node:20-slim` | Gratuito |

### Riscos

| Risco | Mitigação |
|---|---|
| `@excalidraw/utils` sem suporte headless | Fallback: gerar SVG via template Python (sem Node) |
| Imagem Docker grande (+200MB Node) | Multi-stage Docker minimiza camadas |
| Wanda não sabe quando usar diagrama | System prompt update com exemplos de quando invocar |

---

## 8. Critérios de Aceite

1. ✅ `create_diagram(type="care_plan")` retorna PNG válido em < 2s
2. ✅ PNG recebido enviável via `intellicare-comunicacao` (base64 → arquivo binário)
3. ✅ `create_diagram(type="medication_timeline")` funciona com 1 a 20 medicamentos
4. ✅ Wanda invoca a tool corretamente quando usuário pede "diagrama", "mapa", "visualização"
5. ✅ Graceful degradation: se Node.js indisponível, retorna apenas JSON sem PNG
6. ✅ Testes: 10 cenários cobrindo cada tipo de diagrama + casos de erro

---

## 9. Referências

- [Excalidraw GitHub](https://github.com/excalidraw/excalidraw)
- [@excalidraw/utils](https://www.npmjs.com/package/@excalidraw/utils) — pacote headless
- [Excalidraw JSON Schema](https://github.com/excalidraw/excalidraw/blob/master/packages/excalidraw/types.ts)
- Padrão existente: `intellicare-wanda/wanda/mcp/config.py` — MCPClientConfig
- Padrão existente: `intellicare-pierre/pierre/mcp/server.py` — MCP tool registration
