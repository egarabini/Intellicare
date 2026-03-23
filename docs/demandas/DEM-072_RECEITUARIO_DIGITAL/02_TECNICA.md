---
tipo: especificacao-tecnica
demanda: DEM-072
titulo: Receituário Digital
---

# DEM-072 — Especificação Técnica

## Mapa de mudanças

| Arquivo | Tipo | O que muda |
|---------|------|-----------|
| `modules/oswaldo/routes.py` | Modificar | Endpoint `GET /oswaldo/prescriptions/{id}/receituario.pdf` |
| `modules/oswaldo/services.py` | Modificar | `generate_receituario()` — monta dados + chama renderer |
| `modules/oswaldo/schemas.py` | Modificar | `ReceituarioData`, `MedicationItem`, `PrescriptionType` |
| `packages/intellicare-core/intellicare_core/templates/receituario.html` | **Novo** | Template Jinja2 CFM/ANVISA |
| `frontend/ClinicoUI/src/components/OswaldoPrescriptionEditor.tsx` | Modificar | Botão "Imprimir Receituário" |
| `tests/test_receituario.py` | **Novo** | 3+ testes |

---

## Modelo de dados — `ReceituarioData`

```python
@dataclass
class MedicationItem:
    order: int
    drug_name: str              # Nome genérico (DCB)
    concentration: str          # "500mg"
    pharmaceutical_form: str    # "Comprimido"
    quantity: int               # 20
    quantity_unit: str          # "unidades" / "caixas"
    dosage_instructions: str    # Posologia formal completa
    route: str                  # "Via oral" / "Uso tópico"

@dataclass
class ReceituarioData:
    prescription_id: str
    issued_at: datetime
    prescription_type: Literal["simple", "special_control"]  # simple = comum, special_control = tarja preta

    # Profissional
    professional_name: str      # "Dr. João Silva"
    crm: str                    # "12345"
    crm_state: str              # "SP"
    specialty: str              # "Clínico Geral"
    clinic_address: str
    clinic_phone: str

    # Paciente
    patient_name: str
    patient_age: int
    patient_cpf: str | None     # Obrigatório apenas em special_control

    # Prescrição
    cid10_code: str             # "R51"
    cid10_description: str      # "Cefaleia"
    medications: list[MedicationItem]

    # Controle especial (apenas se special_control)
    prescription_validity_days: int | None = None  # Validade em dias
    prescription_number: str | None = None         # Nº da notificação
```

---

## Template Jinja2 — `receituario.html`

Estrutura HTML seguindo o layout CFM/ANVISA:

```html
<!-- CABEÇALHO -->
<div class="header">
  <h2>{{ data.professional_name }}</h2>
  <p>CRM {{ data.crm }}/{{ data.crm_state }} — {{ data.specialty }}</p>
  <p>{{ data.clinic_address }} | Tel: {{ data.clinic_phone }}</p>
</div>

<hr>

<!-- IDENTIFICAÇÃO DO PACIENTE -->
<div class="patient">
  <p><strong>Paciente:</strong> {{ data.patient_name }}</p>
  <p><strong>Idade:</strong> {{ data.patient_age }} anos</p>
  {% if data.prescription_type == 'special_control' %}
  <p><strong>CPF:</strong> {{ data.patient_cpf }}</p>
  {% endif %}
  <p><strong>Data:</strong> {{ data.issued_at | format_date_br }}</p>
</div>

<!-- SÍMBOLO DE RECEITA -->
<div class="rx-symbol">℞</div>

<!-- MEDICAMENTOS -->
{% for med in data.medications %}
<div class="medication">
  <p><strong>{{ loop.index }}. {{ med.drug_name }} {{ med.concentration }}</strong></p>
  <p>{{ med.pharmaceutical_form }} — {{ med.quantity }} {{ med.quantity_unit }}</p>
  <p><em>{{ med.dosage_instructions }}</em></p>
</div>
{% endfor %}

<!-- RODAPÉ -->
<div class="footer">
  <p>{{ data.clinic_address | city_only }}, {{ data.issued_at | format_date_br_extenso }}</p>
  {% if data.prescription_type == 'special_control' %}
  <p>Validade: {{ data.prescription_validity_days }} dias | Nº {{ data.prescription_number }}</p>
  {% endif %}
  <div class="signature-block">
    <div class="signature-line">_________________________</div>
    <p>{{ data.professional_name }}</p>
    <p>CRM {{ data.crm }}/{{ data.crm_state }}</p>
  </div>
</div>
```

---

## Posologia formal — formatação automática

O `generate_receituario()` formata a posologia automaticamente antes de passar ao template:

```python
def format_posologia(item: dict) -> str:
    """
    Entrada (do Oswaldo): {"dose": "1", "unit": "comprimido", "frequency": "8/8h", "duration": "3 dias"}
    Saída (CFM): "Tomar 1 (um) comprimido via oral a cada 8 horas por 3 (três) dias."
    """
    # Números por extenso para clareza (evitar "1" → "um")
    # Frequência padronizada: "8/8h" → "a cada 8 horas"
    # Rota incluída: "Via oral" se comprimido/cápsula, "Uso tópico" se creme/pomada
```

---

## Endpoint

```
GET /oswaldo/prescriptions/{prescription_id}/receituario.pdf
    ?type=simple|special_control  (default: simple)

Response:
  Content-Type: application/pdf
  Content-Disposition: attachment; filename="receituario_{prescription_id}.pdf"
  Body: bytes PDF
```

---

## Integração com profissional do tenant

O CRM e dados do médico vêm de `professionals` (schema do tenant) via `tenant_session(ctx)` — não hardcodado. O `ctx.user_id` identifica o profissional logado.

---

## Dependências

- `WeasyPrint` + `Jinja2` — já presentes no projeto (usados em DEM-027 e DEM-062)
- Sem migration nova — usa tabela `prescriptions` (migration 014)
