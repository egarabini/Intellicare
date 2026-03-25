# 5. Guia do Paciente (PacienteUI)

## Menu principal do paciente

- `Painel`
- `Agenda`
- `Minhas Jornadas`
- `Histórico Clínico`
- `Programas`
- `Meus Dados`
- `Contato`

## 5.1 Painel inicial

### O que o paciente visualiza

- Nome de exibicao
- Proxima consulta (data, horario, tipo, profissional)
- Total de agendamentos futuros
- Total de consultas realizadas
- Aviso da clinica (quando houver)

### Exemplo de leitura

- Proxima consulta: `24/03/2026 14:30 - Retorno`
- Agendamentos futuros: `2`
- Historico: `7`

## 5.2 Minhas Jornadas

### O que aparece na tabela

- Canal (`WHATSAPP`, `EMAIL`, `SMS`, `ROCKETCHAT`)
- Status da jornada
- Template/mensagem base
- Data de abertura
- Data de fechamento

### Como interpretar status

- `DISPATCHED`/`SENT`: mensagem enviada.
- `REPLIED`: paciente respondeu.
- `CLOSED`: jornada concluida.
- `FAILED`: falha de envio.
- `EXPIRED`: expirou sem resposta.

## 5.3 Historico Clinico (Meu Histórico)

- **Como acessar**: Portal do Paciente → "Meu Histórico"
- **O que aparece**: consultas, notas Florence (sem partes internas), prescrições, jornadas de acompanhamento
- **Como baixar receituário**: clicar em "Baixar Receituário" na prescrição → PDF em nova aba
- **Privacidade**: o paciente vê o que foi compartilhado pelo médico, não as anotações internas SOAP-A

## 5.4 Agenda, dados e contato

- Paciente consulta agenda e proximos compromissos.
- Paciente atualiza dados cadastrais (quando habilitado no fluxo do tenant).
- Paciente acessa canal de contato da unidade.

## 5.5 Orientacao para equipe de atendimento

Quando o paciente relatar "nao recebi mensagem":

1. Confirmar numero no formato internacional (E.164) ou e-mail.
2. Verificar status da jornada no GestorUI.
3. Se `FAILED`, reenviar por canal alternativo.
