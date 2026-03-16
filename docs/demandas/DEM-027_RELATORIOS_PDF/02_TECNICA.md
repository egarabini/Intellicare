# DEM-027 — Relatórios PDF — Especificação Técnica

## 1. Biblioteca: WeasyPrint

**Escolha:** `weasyprint` — renderiza HTML+CSS para PDF via Python.

**Motivo:**
- Integra com Jinja2 (templates HTML já usados no projeto)
- Suporte a CSS paginado (`@page`, `page-break-*`)
- Leve — sem Chromium, sem processos externos
- Saída de alta qualidade para tabelas e texto

**Instalação:**
```bash
# No deploy/Dockerfile (stage Python), adicionar ao apt-get:
apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libfontconfig1

# No pyproject.toml de intellicare-core:
weasyprint = ">=62.0"
jinja2 = ">=3.1"      # já deve estar instalado
```

---

## 2. Estrutura de arquivos

```
packages/intellicare-core/intellicare_core/
├── pdf/
│   ├── __init__.py
│   ├── renderer.py          # função render_pdf(template, context) → bytes
│   └── templates/
│       ├── base.html        # layout base (cabeçalho, rodapé, estilos)
│       ├── admin_receita.html
│       ├── admin_tenants.html
│       ├── gestor_consultas.html
│       ├── gestor_profissionais.html
│       ├── clinico_prontuario.html
│       └── clinico_agenda.html

modules/admin/router.py      # novos endpoints /admin/relatorios/*
modules/gestor/router.py     # novos endpoints /gestor/relatorios/*
modules/cuidado/router.py    # novos endpoints /cuidado/relatorios/*
```

---

## 3. renderer.py

```python
from weasyprint import HTML
from jinja2 import Environment, PackageLoader
from datetime import datetime

jinja_env = Environment(
    loader=PackageLoader("intellicare_core", "pdf/templates")
)

def render_pdf(template_name: str, context: dict) -> bytes:
    context.setdefault("generated_at", datetime.now().strftime("%d/%m/%Y %H:%M"))
    template = jinja_env.get_template(template_name)
    html_str = template.render(**context)
    return HTML(string=html_str).write_pdf()
```

---

## 4. Novos endpoints

Todos retornam `Response(content=pdf_bytes, media_type="application/pdf")` com header:
```
Content-Disposition: attachment; filename="<nome>.pdf"
```

### módulo admin (`/admin/relatorios/`)

```
GET /admin/relatorios/receita?mes=2026-03
    → RPT-A01 — Receita mensal
    → query: invoices pagas no mês, agrupadas por tenant
    → roles: PLATFORM_ADMIN

GET /admin/relatorios/tenants
    → RPT-A02 — Lista de tenants ativos
    → roles: PLATFORM_ADMIN
```

### módulo gestor (`/gestor/relatorios/`)

```
GET /gestor/relatorios/consultas?inicio=2026-03-01&fim=2026-03-31&unidade_id=&profissional_id=
    → RPT-G01 — Consultas por período
    → scoped por tenant do gestor logado
    → roles: TENANT_GESTOR

GET /gestor/relatorios/profissionais/{unit_id}
    → RPT-G02 — Profissionais da unidade
    → roles: TENANT_GESTOR
```

### módulo cuidado (`/cuidado/relatorios/`)

```
GET /cuidado/relatorios/prontuario/{patient_id}
    → RPT-C01 — Resumo clínico do paciente
    → roles: CLINICO

GET /cuidado/relatorios/agenda?data=2026-03-16
    → RPT-C02 — Agenda do profissional logado no dia/semana
    → roles: CLINICO
```

**Total: 6 novos endpoints**

---

## 5. Template base (base.html)

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
  @page {
    size: A4;
    margin: 2cm 1.5cm;
    @top-left   { content: "IntelliCare v3"; font-size: 9px; color: #666; }
    @top-right  { content: "{{ generated_at }}"; font-size: 9px; color: #666; }
    @bottom-right { content: "Página " counter(page) " de " counter(pages);
                    font-size: 9px; color: #666; }
  }
  body { font-family: Helvetica, Arial, sans-serif; font-size: 11px; color: #1a1a1a; }
  h1   { color: #0f766e; font-size: 18px; margin-bottom: 4px; }
  h2   { color: #0f766e; font-size: 13px; margin-top: 16px; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; }
  th    { background: #0f766e; color: white; padding: 6px 8px; text-align: left; }
  td    { padding: 5px 8px; border-bottom: 1px solid #e5e7eb; }
  tr:nth-child(even) td { background: #f9fafb; }
  .empty { text-align: center; color: #6b7280; padding: 24px; font-style: italic; }
  .total { font-weight: bold; background: #f0fdf4 !important; }
</style>
</head>
<body>
  <h1>{% block titulo %}{% endblock %}</h1>
  <p style="color:#6b7280; font-size:10px; margin-top:0">
    {% block subtitulo %}{% endblock %}
  </p>
  <hr style="border:none; border-top:2px solid #0f766e; margin:12px 0">
  {% block conteudo %}{% endblock %}
</body>
</html>
```

---

## 6. Frontend — botões de exportação

Padrão para todos os botões de exportação:

```tsx
// Hook genérico reutilizável
async function downloadPdf(url: string, filename: string) {
  const token = tokenRef.current;
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Erro ao gerar PDF");
  const blob = await res.blob();
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

// Uso em componente
<Button
  leftSection={<IconFileTypePdf size={16} />}
  variant="light"
  color="red"
  onClick={() => downloadPdf("/admin/relatorios/receita?mes=2026-03", "receita-2026-03.pdf")}
>
  Exportar PDF
</Button>
```

---

## 7. Dependências no Dockerfile

Adicionar ao estágio Python do `deploy/Dockerfile`:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*
```

---

## 8. Checklist de entrega

- [ ] `weasyprint` adicionado ao `pyproject.toml` de `intellicare-core`
- [ ] `libpango*` / `libharfbuzz` / `libfontconfig` adicionados ao `Dockerfile`
- [ ] `packages/intellicare-core/intellicare_core/pdf/renderer.py` criado
- [ ] `base.html` + 6 templates HTML criados
- [ ] 6 endpoints implementados (2 admin, 2 gestor, 2 cuidado)
- [ ] Botões de exportação adicionados nas páginas indicadas
- [ ] Download automático funciona no browser
- [ ] PDF com 0 registros exibe mensagem vazia
- [ ] Cabeçalho/rodapé paginados aparecem em páginas múltiplas
- [ ] Testes: `pytest tests/admin/test_relatorios.py` e equivalentes
