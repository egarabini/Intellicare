---
tipo: design-system
atualizado: 2026-03-13
---

# Sistema de Design — IntelliCare V3

## Paleta Clínica de Severidade

| Token | Hex | Uso |
|-------|-----|-----|
| `--severity-critical` | `#DC2626` | Alertas críticos, dados faltantes urgentes, exames vencidos |
| `--severity-warning` | `#D97706` | Avisos, prazo vencendo, atenção necessária |
| `--severity-info` | `#2563EB` | Informação neutra, guias, dicas |
| `--severity-success` | `#16A34A` | Confirmações, dados completos, protocolo aplicado |
| `--severity-neutral` | `#6B7280` | Texto secundário, metadados, timestamps |
| `--surface-primary` | `#FFFFFF` | Fundo de painéis e cards |
| `--surface-secondary` | `#F9FAFB` | Fundo de página, zebra em tabelas |
| `--text-primary` | `#111827` | Texto principal |
| `--text-secondary` | `#6B7280` | Labels, hints |

---

## Princípios de Interface

**1. Densidade informacional**
Painéis clínicos mostram mais dados em menos espaço. Tabelas densas são preferíveis
a cards esparsos quando o contexto é profissional.

**2. Contraste alto**
Acessível em monitores ruins, iluminação adversa de postos de saúde.
Mínimo WCAG AA em todos os textos funcionais.

**3. Ação principal sempre visível**
Sem caça a botões. O próximo passo está sempre visível, sem scroll.

**4. Estado do sistema explícito**
Loading, erro, vazio, sucesso: sempre indicado. Nada desaparece silenciosamente.

**5. Formulários lineares**
Evitar wizards complexos. Um formulário = uma ação = um resultado.

---

## Stack por contexto

| Contexto | Stack | Justificativa |
|----------|-------|--------------|
| Admin / Gestor | FastAPI + Jinja2 + HTMX | Sem build step, deploy simples, suficiente para painéis administrativos |
| Clínico (Fase 3) | React 19 + TailwindCSS | SPA necessária para fluidez em consulta com streaming de resposta SLM |
| Tokens de design | CSS custom properties | Sem framework de UI externo — portável entre Jinja2 e React |

---

## Componentes base (Jinja2/HTMX)

```html
<!-- Card de status de tenant -->
<div class="card" data-status="{{ tenant.status }}">
  <span class="badge badge--{{ tenant.status }}">{{ tenant.status }}</span>
  <h3>{{ tenant.name }}</h3>
  <p class="text-secondary">{{ tenant.vertical }} · {{ tenant.plan }}</p>
</div>

<!-- Alerta clínico -->
<div class="alert alert--{{ severity }}" role="alert">
  <strong>{{ title }}</strong>
  <p>{{ message }}</p>
</div>
```

---

## Acessibilidade — checklist mínimo

- [ ] Contraste de texto ≥ 4.5:1 (WCAG AA)
- [ ] Todos os inputs com `<label>` associado
- [ ] Botões com texto descritivo (não apenas ícones)
- [ ] Mensagens de erro vinculadas ao campo com `aria-describedby`
- [ ] Navegação por teclado funcional em todos os fluxos principais
