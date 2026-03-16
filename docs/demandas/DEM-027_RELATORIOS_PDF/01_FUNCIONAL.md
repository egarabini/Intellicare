# DEM-027 — Relatórios PDF Exportáveis

## Objetivo

Permitir que usuários dos módulos Admin, Gestor e Clínico exportem relatórios em PDF diretamente da interface, sem dependência de ferramentas externas.

---

## Relatórios por módulo

### AdminUI (PLATFORM_ADMIN)

| ID | Relatório | Gatilho |
|----|-----------|---------|
| RPT-A01 | Receita mensal da plataforma | FinanceiroPage → botão "Exportar PDF" |
| RPT-A02 | Lista de tenants ativos | Dashboard → botão "Exportar" |

**RPT-A01 — Receita Mensal:**
- Período selecionado (mês/ano)
- Tabela de invoices pagas: tenant, valor (R$), data pagamento
- Totais por tenant e total geral
- Gráfico de barras simples (receita por mês, últimos 6 meses)

**RPT-A02 — Tenants Ativos:**
- Data de geração
- Tabela: nome do tenant, slug, plano, módulos habilitados, data criação

---

### GestorUI (TENANT_GESTOR)

| ID | Relatório | Gatilho |
|----|-----------|---------|
| RPT-G01 | Consultas por período | nova página Relatórios → formulário de filtros |
| RPT-G02 | Profissionais da unidade | UnitsPage → botão "Exportar" em cada unidade |

**RPT-G01 — Consultas por Período:**
- Filtros: data início, data fim, unidade (opcional), profissional (opcional)
- Tabela: data, paciente, profissional, unidade, tipo de consulta, status
- Totais: total de consultas, por profissional, por unidade

**RPT-G02 — Profissionais da Unidade:**
- Nome da unidade, endereço, data de geração
- Tabela: nome do profissional, especialidade, CRM/registro, status

---

### ClinicoUI (CLINICO)

| ID | Relatório | Gatilho |
|----|-----------|---------|
| RPT-C01 | Resumo clínico do paciente | PatientProfile → botão "Exportar Prontuário" |
| RPT-C02 | Agenda do profissional | AgendaPage → botão "Exportar Agenda" |

**RPT-C01 — Resumo Clínico do Paciente:**
- Cabeçalho: nome, data de nascimento, CPF mascarado, data de geração
- Histórico de consultas: data, profissional, diagnóstico (CID-10), observações
- Assinatura digital (nome do profissional logado + CRM)

**RPT-C02 — Agenda do Profissional:**
- Período: data selecionada (dia ou semana)
- Tabela: horário, paciente, tipo de consulta, status
- Cabeçalho com nome e especialidade do profissional

---

## Layout padrão dos PDFs

Todos os relatórios seguem o mesmo template base:

```
┌─────────────────────────────────────────────────────────┐
│  [Logo IntelliCare]   TÍTULO DO RELATÓRIO           │
│  intellicare.ia.br    Gerado em: DD/MM/AAAA HH:MM   │
├─────────────────────────────────────────────────────────┤
│  [Dados do tenant / contexto]                       │
├─────────────────────────────────────────────────────────┤
│                                                     │
│  [Conteúdo do relatório — tabelas / gráficos]       │
│                                                     │
├─────────────────────────────────────────────────────────┤
│  Página X de Y           [rodapé com contexto]      │
└─────────────────────────────────────────────────────────┘
```

- Papel A4, orientação retrato
- Cores: cabeçalho teal (#0f766e), texto preto, linhas cinza claro
- Fonte: sans-serif (Helvetica)

---

## Critérios de aceitação

1. Botão "Exportar PDF" visível nas páginas indicadas
2. Click dispara chamada ao backend que retorna `application/pdf`
3. Browser inicia download automático com nome descritivo (ex: `receita-2026-03.pdf`)
4. PDF abre sem erros no Acrobat, Chrome e mobile
5. Dados do PDF são idênticos ao que aparece na tela no momento da exportação
6. Relatório com 0 registros exibe mensagem "Nenhum registro encontrado" em vez de tabela vazia
7. Cabeçalho e rodapé repetidos em todas as páginas quando o conteúdo pagina
