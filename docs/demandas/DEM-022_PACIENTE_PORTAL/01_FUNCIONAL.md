# DEM-022 — Portal do Paciente

## Objetivo

Criar o frontend para o usuário final — o **paciente** — que acessa a plataforma
para ver seus agendamentos, histórico de consultas, programas de saúde e
interagir com a sua clínica.

É a interface mais simples dos 4 módulos, mas a mais visível para o usuário final.
Deve ser acessível, limpa e mobile-first.

## Ator

| Ator | Papel |
|------|-------|
| PACIENTE | Usuário final — acessa dados próprios do seu tenant |

## Diferença dos outros módulos

```
AdminUI    → PLATFORM_ADMIN  → gerencia a plataforma
GestorUI   → TENANT_GESTOR   → gerencia o estabelecimento
ClinicoUI  → CLINICO         → atende pacientes
PacienteUI → PACIENTE        → vê suas próprias informações
```

O paciente **não edita nada** — só visualiza. Exceção: dados cadastrais básicos
e confirmação de agendamento.

## Funcionalidades

### F01 — Tela Inicial (Meu Painel)

Visão resumida:
- Próxima consulta agendada (data, clínico, tipo)
- Avisos da clínica (campo texto livre do gestor — read-only)
- Atalhos: Ver Agenda | Ver Histórico | Meus Programas

### F02 — Minha Agenda

Lista de agendamentos futuros:
- Data, hora, clínico, tipo (consulta/retorno/exame), status
- Botão "Confirmar presença" (muda status de `agendado` → `confirmado`)
- Botão "Cancelar" (com confirmação — muda status para `cancelado`)
- Histórico de consultas passadas (últimas 10)

### F03 — Meu Histórico Clínico

Lista de encontros realizados:
- Data, clínico, tipo, CID-10 (se preenchido), prescrição
- **Não** exibe notas SOAP completas — apenas resumo (privacidade clínica)
- Download do resumo em PDF (botão — gera PDF simples no browser)

### F04 — Meus Programas de Saúde

Programas em que o paciente está inscrito:
- Nome do programa, clínico responsável, data de inscrição
- Status (ativo/concluído)
- Próxima ação prevista (campo texto do programa)

### F05 — Meu Cadastro

Dados cadastrais do paciente:
- Nome, data nascimento, CPF (mascarado: ***.***.***-**), plano de saúde
- E-mail e telefone editáveis (PATCH /cuidado/patients/:id com campos limitados)
- Botão "Salvar alterações"

### F06 — Contato com a Clínica

Informações de contato do tenant:
- Nome da clínica, telefone, endereço, e-mail
- Horário de funcionamento (campo livre do gestor)
- Botão "WhatsApp" (abre wa.me/+55... se telefone tiver WhatsApp configurado)

## Critérios de Aceite

- [ ] Login com role PACIENTE redireciona para o PacienteUI
- [ ] Paciente só vê dados do seu próprio tenant (isolamento)
- [ ] Agenda lista agendamentos corretos com botão confirmar/cancelar
- [ ] Histórico não exibe notas SOAP completas
- [ ] Dados cadastrais podem ser editados (e-mail e telefone)
- [ ] Build sem erros: `npm run build`
- [ ] Serve em `http://127.0.0.1:9000/paciente-ui/`
