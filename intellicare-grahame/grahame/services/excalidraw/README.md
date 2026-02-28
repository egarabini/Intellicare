# 🎨 Excalidraw Integration - Guia de Uso

## 📋 Visão Geral

Integração completa do Excalidraw com FHIR para criação e colaboração em diagramas clínicos.

---

## 🚀 Quick Start

### 1. Criar um Diagrama

```python
from grahame.services.excalidraw import ExcalidrawDiagramStorage

storage = ExcalidrawDiagramStorage(db, tenant_id="hospital-1")

diagram_data = {
    "type": "excalidraw",
    "version": 2,
    "elements": [
        {
            "id": "rect1",
            "type": "rectangle",
            "x": 100,
            "y": 100,
            "width": 200,
            "height": 100,
            "strokeColor": "#000000",
            "backgroundColor": "#ffffff",
        }
    ],
    "appState": {
        "viewBackgroundColor": "#ffffff",
    }
}

result = storage.save_diagram(
    diagram_data=diagram_data,
    patient_id="patient-123",
    title="Fluxograma de Tratamento",
    description="Quimioterapia - Ciclo 1",
    category="clinical-diagram",
    author_id="practitioner-456",
)

print(f"Diagrama criado: {result['media_id']}")
```

---

### 2. Recuperar um Diagrama

```python
diagram = storage.get_diagram("media-abc123")

if diagram:
    print(f"Título: {diagram['title']}")
    print(f"Elementos: {len(diagram['data']['elements'])}")
    print(f"Paciente: {diagram['patient_id']}")
```

---

### 3. Listar Diagramas de um Paciente

```python
diagrams = storage.list_patient_diagrams(
    patient_id="patient-123",
    category="clinical-diagram"  # Opcional
)

for diagram in diagrams:
    print(f"{diagram['title']} - {diagram['created']}")
```

---

### 4. Atualizar um Diagrama

```python
# Adicionar novo elemento
diagram_data['elements'].append({
    "id": "text1",
    "type": "text",
    "x": 150,
    "y": 130,
    "text": "Novo texto",
})

storage.update_diagram(
    media_id="media-abc123",
    diagram_data=diagram_data,
    title="Fluxograma Atualizado"
)
```

---

### 5. Colaboração em Tempo Real

```python
from grahame.services.excalidraw import ExcalidrawCollaborationService

collab = ExcalidrawCollaborationService()

# Em um WebSocket handler
await collab.join_room(
    room_id="diagram-abc123",
    websocket=websocket,
    user_id="user-1",
    user_name="Dr. Silva",
    patient_id="patient-123"
)

# Broadcast de atualização
await collab.broadcast_update(
    room_id="diagram-abc123",
    sender_ws=websocket,
    update_data={"elements": [...]}
)

# Broadcast de cursor
await collab.broadcast_cursor(
    room_id="diagram-abc123",
    sender_ws=websocket,
    user_id="user-1",
    cursor_data={"x": 100, "y": 200}
)
```

---

## 🎨 Integração Frontend (React)

### Instalação

```bash
npm install @excalidraw/excalidraw
```

### Componente Básico

```tsx
import { Excalidraw } from "@excalidraw/excalidraw";
import { useState, useEffect } from "react";

function ExcalidrawDiagram({ patientId, diagramId }) {
  const [excalidrawAPI, setExcalidrawAPI] = useState(null);
  const [diagramData, setDiagramData] = useState(null);

  // Carregar diagrama
  useEffect(() => {
    if (diagramId) {
      fetch(`/api/v1/excalidraw/diagrams/${diagramId}`)
        .then(res => res.json())
        .then(data => setDiagramData(data.data));
    }
  }, [diagramId]);

  // Salvar mudanças
  const handleChange = (elements, appState) => {
    const data = {
      type: "excalidraw",
      version: 2,
      elements,
      appState,
    };

    // Debounce save
    clearTimeout(window.saveTimeout);
    window.saveTimeout = setTimeout(() => {
      fetch(`/api/v1/excalidraw/diagrams/${diagramId}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({diagram_data: data})
      });
    }, 1000);
  };

  return (
    <div style={{ height: "600px" }}>
      <Excalidraw
        excalidrawAPI={(api) => setExcalidrawAPI(api)}
        initialData={diagramData}
        onChange={handleChange}
      />
    </div>
  );
}
```

---

### Colaboração em Tempo Real

```tsx
import { Excalidraw } from "@excalidraw/excalidraw";
import { useState, useEffect, useRef } from "react";

function CollaborativeExcalidraw({ roomId, userId, userName }) {
  const [excalidrawAPI, setExcalidrawAPI] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    // Conectar WebSocket
    const ws = new WebSocket(
      `ws://localhost:8012/api/v1/excalidraw/collaborate/${roomId}?user_id=${userId}&user_name=${userName}`
    );

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === 'diagram-update' && excalidrawAPI) {
        // Atualizar diagrama
        excalidrawAPI.updateScene({
          elements: message.data.elements,
          appState: message.data.appState,
        });
      }

      if (message.type === 'cursor-update') {
        // Atualizar cursor de outro usuário
        // TODO: Implementar visualização de cursores
      }

      if (message.type === 'user-joined') {
        console.log(`${message.user_name} entrou na sala`);
      }
    };

    wsRef.current = ws;

    return () => ws.close();
  }, [roomId, userId, userName, excalidrawAPI]);

  const handleChange = (elements, appState) => {
    // Enviar atualização via WebSocket
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'diagram-update',
        data: { elements, appState }
      }));
    }
  };

  return (
    <Excalidraw
      excalidrawAPI={setExcalidrawAPI}
      onChange={handleChange}
    />
  );
}
```

---

## 📊 Casos de Uso Clínicos

### 1. Fluxograma de Tratamento (Oncologia)

```python
# Criar fluxograma de quimioterapia
diagram_data = {
    "elements": [
        {"type": "rectangle", "text": "Avaliação Inicial"},
        {"type": "arrow"},
        {"type": "rectangle", "text": "Ciclo 1 - Cisplatina"},
        {"type": "arrow"},
        {"type": "rectangle", "text": "Reavaliação"},
    ]
}

storage.save_diagram(
    diagram_data=diagram_data,
    patient_id="patient-123",
    title="Protocolo Quimioterapia",
    category="treatment-plan"
)
```

### 2. Anotações em Imagens (Radiologia)

```python
# Marcar achados em RX
diagram_data = {
    "elements": [
        {"type": "image", "fileId": "rx-torax.jpg"},
        {"type": "arrow", "text": "Nódulo 2cm"},
        {"type": "ellipse", "strokeColor": "red"},
    ]
}

storage.save_diagram(
    diagram_data=diagram_data,
    patient_id="patient-123",
    title="RX Tórax - Achados",
    category="radiology-annotation"
)
```

### 3. Educação do Paciente

```python
# Explicar procedimento cirúrgico
diagram_data = {
    "elements": [
        {"type": "rectangle", "text": "1. Anestesia"},
        {"type": "rectangle", "text": "2. Incisão"},
        {"type": "rectangle", "text": "3. Procedimento"},
        {"type": "rectangle", "text": "4. Sutura"},
    ]
}

storage.save_diagram(
    diagram_data=diagram_data,
    patient_id="patient-123",
    title="Explicação Cirurgia",
    category="patient-education"
)
```

---

## 🔒 Segurança e Compliance

### LGPD

- ✅ Dados armazenados em FHIR (auditável)
- ✅ Soft-delete (histórico preservado)
- ✅ Versionamento completo
- ✅ Rastreabilidade (autor, data)

### HIPAA

- ✅ Encryption at rest (PostgreSQL)
- ✅ Encryption in transit (HTTPS/WSS)
- ✅ Audit trail (FHIR AuditEvent)
- ✅ Access control (FHIR Access Policies)

---

## 📚 Referências

- [Excalidraw Docs](https://docs.excalidraw.com/)
- [FHIR Media](https://www.hl7.org/fhir/media.html)
- [FHIR DocumentReference](https://www.hl7.org/fhir/documentreference.html)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

