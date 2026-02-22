# 🤖 SCRIPTS DE AUTOMAÇÃO DE COMUNICAÇÃO

## 📌 Visão Geral

Scripts Python para automatizar processos de comunicação e gestão de stakeholders do projeto INTELLICARE.

**Responsável**: DEV1  
**Data de criação**: 21/02/2026  
**Versão**: 1.0

---

## 📁 Scripts Disponíveis

### 1. `gerar_ata.py` - Gerador de Ata de Reunião

**Descrição**: Gera atas de reunião padronizadas a partir de dados estruturados.

**Uso**:
```python
from gerar_ata import GeradorAta

gerador = GeradorAta()

ata = gerador.gerar_ata(
    data="26/02/2026",
    horario_inicio="10:00",
    horario_fim="12:00",
    facilitador="DEV1",
    participantes_presentes=[
        {"nome": "Dra. Maria Santos", "cargo": "Especialista LGPD"}
    ],
    participantes_ausentes=[],
    resumo_executivo="Validação LGPD concluída com sucesso",
    objetivos=[
        {"descricao": "Validar anonimização", "alcancado": True}
    ],
    topicos=[...],
    action_items=[...],
    proximos_passos=[...]
)

# Salvar ata
file_path = gerador.salvar_ata(ata, "26/02/2026", "validacao_lgpd")
```

**Saída**: Arquivo Markdown com ata formatada

---

### 2. `enviar_convites.py` - Enviador de Convites

**Descrição**: Envia convites de reunião por email com agenda anexada.

**Uso**:
```python
from enviar_convites import EnviadorConvites

enviador = EnviadorConvites()

convite = enviador.criar_convite(
    titulo="Validação LGPD",
    data="26/02/2026",
    horario_inicio="10:00",
    duracao_minutos=120,
    participantes_ids=["STK-002"],
    objetivo="Validar anonimização LGPD",
    pauta=[...],
    materiais_previos=[...],
    link_reuniao="https://meet.google.com/..."
)

# Enviar convite (simulação)
resultado = enviador.enviar_convite(convite, simular=True)
```

**Saída**: Email formatado com convite e agenda

---

### 3. `coletar_feedback.py` - Coletor de Feedback

**Descrição**: Coleta e consolida feedback de reuniões e validações.

**Uso**:
```python
from coletar_feedback import ColetorFeedback

coletor = ColetorFeedback()

# Criar formulário
formulario = coletor.criar_formulario_feedback(
    tipo_atividade="Validação",
    titulo="Validação LGPD",
    data="26/02/2026"
)

# Adicionar resposta
formulario = coletor.adicionar_resposta(
    formulario=formulario,
    respondente="Dra. Maria Santos",
    cargo="Especialista LGPD",
    avaliacao_geral=5,
    organizacao="Sim, muito bem organizada",
    pontos_fortes=[...],
    pontos_melhoria=[...],
    sugestoes="..."
)

# Consolidar feedback
consolidado = coletor.consolidar_feedback(formulario)

# Gerar relatório
relatorio = coletor.gerar_relatorio_feedback(consolidado)
```

**Saída**: Relatório consolidado de feedback

---

### 4. `gerar_relatorio.py` - Gerador de Relatórios

**Descrição**: Gera relatórios mensais de métricas de comunicação.

**Uso**:
```python
from gerar_relatorio import GeradorRelatorio

gerador = GeradorRelatorio()

# Gerar dashboard
dashboard = gerador.gerar_dashboard("2026-02")

# Gerar relatório mensal
relatorio = gerador.gerar_relatorio_mensal("2026-02")

# Salvar arquivos
dashboard_path = gerador.salvar_dashboard(dashboard, "2026-02")
relatorio_path = gerador.salvar_relatorio(relatorio, "2026-02")
```

**Saída**: Dashboard JSON + Relatório Markdown

---

## 🔧 Instalação e Configuração

### Requisitos:
- Python 3.11+
- Nenhuma dependência externa (usa apenas biblioteca padrão)

### Configuração:
1. Certifique-se de que a estrutura de diretórios `/comunicacao/` existe
2. Verifique que o arquivo `cadastro_stakeholders.json` está atualizado
3. Execute os scripts a partir do diretório raiz do projeto

---

## 📊 Fluxo de Trabalho Recomendado

### Antes da Reunião:
1. **Criar convite** com `enviar_convites.py`
2. **Enviar convite** 48h antes da reunião

### Durante a Reunião:
1. **Tomar notas** dos tópicos discutidos
2. **Registrar action items** e decisões

### Após a Reunião:
1. **Gerar ata** com `gerar_ata.py`
2. **Distribuir ata** em até 24h
3. **Coletar feedback** com `coletar_feedback.py`
4. **Consolidar feedback** e gerar relatório

### Mensalmente:
1. **Gerar dashboard** com `gerar_relatorio.py`
2. **Gerar relatório mensal** com métricas
3. **Analisar tendências** e identificar melhorias

---

## 📝 Exemplos de Uso

### Exemplo Completo - Validação LGPD:

```python
# 1. Enviar convite
from enviar_convites import EnviadorConvites

enviador = EnviadorConvites()
convite = enviador.criar_convite(
    titulo="Validação LGPD",
    data="26/02/2026",
    horario_inicio="10:00",
    duracao_minutos=120,
    participantes_ids=["STK-002"],
    objetivo="Validar anonimização LGPD",
    pauta=[...],
    link_reuniao="https://meet.google.com/..."
)
enviador.enviar_convite(convite, simular=True)

# 2. Após reunião - Gerar ata
from gerar_ata import GeradorAta

gerador_ata = GeradorAta()
ata = gerador_ata.gerar_ata(
    data="26/02/2026",
    horario_inicio="10:00",
    horario_fim="12:00",
    facilitador="DEV1",
    participantes_presentes=[...],
    resumo_executivo="...",
    objetivos=[...],
    topicos=[...],
    action_items=[...],
    proximos_passos=[...]
)
gerador_ata.salvar_ata(ata, "26/02/2026", "validacao_lgpd")

# 3. Coletar feedback
from coletar_feedback import ColetorFeedback

coletor = ColetorFeedback()
formulario = coletor.criar_formulario_feedback(
    tipo_atividade="Validação",
    titulo="Validação LGPD",
    data="26/02/2026"
)
formulario = coletor.adicionar_resposta(
    formulario=formulario,
    respondente="Dra. Maria Santos",
    cargo="Especialista LGPD",
    avaliacao_geral=5,
    organizacao="Sim, muito bem organizada",
    pontos_fortes=[...],
    pontos_melhoria=[...],
    sugestoes="..."
)
consolidado = coletor.consolidar_feedback(formulario)
relatorio_feedback = coletor.gerar_relatorio_feedback(consolidado)

# 4. Fim do mês - Gerar relatório mensal
from gerar_relatorio import GeradorRelatorio

gerador_rel = GeradorRelatorio()
dashboard = gerador_rel.gerar_dashboard("2026-02")
relatorio_mensal = gerador_rel.gerar_relatorio_mensal("2026-02")
gerador_rel.salvar_dashboard(dashboard, "2026-02")
gerador_rel.salvar_relatorio(relatorio_mensal, "2026-02")
```

---

## 🎯 Próximas Melhorias

- [ ] Integração real com Gmail API para envio de emails
- [ ] Integração com Google Calendar para agendamento automático
- [ ] Geração automática de apresentações (PowerPoint/Google Slides)
- [ ] Dashboard web interativo com visualizações
- [ ] Notificações automáticas de action items pendentes
- [ ] Análise de sentimento em feedbacks
- [ ] Exportação de relatórios em PDF

---

**Criado por**: DEV1  
**Data**: 21/02/2026  
**Versão**: 1.0  
**Status**: ✅ Scripts básicos implementados

