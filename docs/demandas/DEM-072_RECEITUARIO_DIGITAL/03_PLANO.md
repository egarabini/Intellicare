---
tipo: plano-execucao
demanda: DEM-072
titulo: Receituário Digital
status: em-execucao
dev: DEV-1
criado: 2026-03-21
---

# DEM-072 — Plano de Execução

## Estimativa

Tempo estimado: ~4h | Complexidade: média-alta

O núcleo crítico é o template Jinja2 com layout CFM/ANVISA e a função de formatação de posologia. WeasyPrint já está no projeto — o padrão é conhecido de DEM-027 e DEM-062.

---

## Ordem de execução

### Bloco 1 — Schemas e dados (45min)
1. Criar `ReceituarioData`, `MedicationItem` e `PrescriptionType` em `schemas.py`
2. Implementar `format_posologia()` — números por extenso, frequência padronizada, rota automática por forma farmacêutica

### Bloco 2 — Template HTML (1.5h)
3. Criar `receituario.html` seguindo o layout CFM/ANVISA (ver `01_FUNCIONAL.md`)
4. Testar renderização WeasyPrint localmente com dados mock
5. Validar visualmente: cabeçalho, ℞, lista de medicamentos, rodapé, assinatura
6. Criar variante `special_control` (CPF paciente, validade, número de notificação)

### Bloco 3 — Backend (1h)
7. Implementar `generate_receituario()` em `services.py`
   - Buscar dados do profissional via `ctx.user_id`
   - Buscar dados da prescrição via `prescription_id`
   - Montar `ReceituarioData` e renderizar template
8. Adicionar endpoint em `routes.py`

### Bloco 4 — Testes e Frontend (45min)
9. Criar `tests/test_receituario.py`:
   - `test_receituario_simple_returns_pdf()`
   - `test_receituario_special_control_includes_cpf()`
   - `test_posologia_formatting()`
10. Adicionar botão "Imprimir Receituário" no `OswaldoPrescriptionEditor.tsx`
    - `IconPrinter` Mantine, chama `GET /oswaldo/prescriptions/{id}/receituario.pdf`
    - Abre PDF em nova aba (não forçar download)

---

## Regras de negócio obrigatórias (CFM/ANVISA)

| Regra | Implementação |
|-------|--------------|
| Nome genérico (DCB) obrigatório | Validar que `drug_name` não é marca comercial (warning se contiver ® ou nomes conhecidos) |
| Posologia clara e sem abreviações | `format_posologia()` expande todas as abreviações ("8/8h" → "a cada 8 horas") |
| Receita de controle especial exige CPF | Validar `patient_cpf not None` se `type=special_control` |
| Data por extenso no rodapé | Filtro Jinja2 `format_date_br_extenso` |

---

## Gotcha — WeasyPrint e fontes

WeasyPrint em Docker usa fontes do sistema. O símbolo `℞` pode não renderizar se a fonte não tiver o glyph. Usar fallback:
```css
.rx-symbol { font-family: "DejaVu Serif", "Times New Roman", serif; }
```
Testar o PDF gerado no container antes de assumir que renderizou corretamente.

---

## Entrega

```
feat(oswaldo): receituário digital CFM/ANVISA — template Jinja2, posologia formal, simple/special_control
```
Hash → enviar para o ARQUITETO fechar DEM-072.
