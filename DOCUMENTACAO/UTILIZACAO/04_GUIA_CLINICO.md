# 4. Guia do Clinico (ClinicoUI)

## Menu principal

- `Início` (Dashboard)
- `Jornadas`
- `Agenda`
- `Pacientes`
- `Grupos`
- `Profissionais`
- `Equipe`
- `Assistente IA`
- `Meu Perfil`

## 4.1 Dashboard clinico (Minha Agenda)

### O que a tela mostra

- Quantidade de consultas do dia
- Quantidade em andamento
- Bloco de equipe (profissionais ativos, grupos)
- Lista de consultas com acao `Atender` ou `Retomar`

### Exemplo de uso

1. Abrir dashboard no inicio do turno.
2. Clicar em `Atender` no primeiro paciente.
3. Se houver encontro aberto, usar `Retomar`.

## 4.1.1 Perfil do paciente: aba padrao "Linha do Tempo" (DEM-071)

Ao abrir um paciente no `ClinicoUI`, a aba padrao passa a ser **Linha do Tempo**.

Essa aba consolida, em ordem cronologica:

- consultas;
- notas clinicas (Florence);
- prescricoes (Oswaldo);
- tarefas de jornada (CarePlanner).

Uso recomendado: revisar os ultimos eventos antes de iniciar o encontro atual.

## 4.2 Fluxo de atendimento (Encounter)

## Passo a passo

1. Acessar paciente e abrir `Encontro Atual`.
2. Se nao houver encontro aberto, clicar em `Abrir Novo Encontro`.
3. Registrar conteudo clinico nas abas:
   - `Notas Florence`
   - `Prescrição` (Oswaldo)
   - `Legado` (nota SOAP + CID + prescricao textual)
4. Finalizar em `Fechar Encontro`.
5. Gerar `PDF Clínico` quando necessario.

## 4.3 Notas Florence (documentacao clinica)

### Modos disponiveis

- `Texto livre (FREE)`
- `SOAP`

### Campos em SOAP

- Motivo da consulta
- `S` Subjetivo
- `O` Objetivo
- `A` Avaliacao
- `P` Plano

### Recurso IA (Sugestão IA)

- O botão "Sugestão IA" está disponível na EncounterView e agiliza o preenchimento.
- A sugestão agora considera o **histórico longitudinal** do paciente (últimos encontros, notas, prescrições) — gerando um resultado mais personalizado.
- Quando MARIE_ENABLED está ativo, a sugestão pode levar 2–5s a mais — comportamento esperado, não é erro.
- Em fallback por regra, a tela sinaliza baixa confianca para revisao manual.

### Exemplo preenchido (SOAP)

- Motivo: `cefaleia persistente ha 3 dias`
- S: `paciente relata dor em pressao frontal, sem vomitos`
- O: `PA 130x80, afebril, sem rigidez de nuca`
- A: `cefaleia tensional, sem sinais de alarme`
- P: `analgesico sintomatico, hidratacao, retorno se piora`

## 4.4 Prescricao Oswaldo

### Funcionalidades

- Sugestao IA de CID-10 e itens de prescricao
- Adicao manual de itens
- Historico de prescricoes do encontro

### Campos de item

- Medicamento
- Posologia
- Duracao (opcional)

### Exemplo preenchido

- CID-10: `R51 - Cefaleia`
- Item 1: `Dipirona 500mg`, `1 comprimido 6/6h`, `3 dias`
- Item 2: `Ibuprofeno 400mg`, `1 comprimido 8/8h`, `2 dias`

### Receituario digital (DEM-072)

No historico da prescricao, o botao **Imprimir Receituário** permite gerar PDF medico para impressao.

Tipos disponiveis:

- `Receita Comum`
- `Receita de Controle Especial` (quando aplicavel)

Fluxo:

1. Abrir historico da prescricao.
2. Clicar em `Imprimir Receituário`.
3. Abrir PDF em nova aba.
4. Imprimir com `Ctrl + P`.

### Alertas de Interação Medicamentosa

- O alerta aparece automaticamente ao prescrever dois ou mais medicamentos com interação conhecida
- Cores: vermelho (GRAVE), amarelo (MODERADO), azul (LEVE)
- Como agir: avaliar clinicamente → clicar "Entendido — manter prescrição" se intencional
- O alerta **não impede** a prescrição — decisão sempre do médico
- Alertas marcados "por IA" devem ser confirmados com fontes clínicas antes de ignorar

## 4.5 Jornadas no contexto clinico

- Tela de jornadas permite filtro `Minhas Jornadas`.
- Clinico acompanha status das jornadas relacionadas a seus pacientes.
- Notificacoes com sino exibem itens nao lidos quando disponiveis.

## 4.6 Notificacoes push (DEM-066)

### Onde ativar

- No sino de notificacoes (`NotificationBell`) no topo da aplicacao.
- Usar o toggle para `Ativar notificações push` ou `Desativar notificações push`.

### Como usar no dia a dia

- Manter push ativo durante o turno para resposta rapida a eventos clinicos.
- Abrir notificacao para marcar como lida e seguir para o fluxo correspondente.

### Checklist rapido

- Permitir push no navegador.
- Validar toggle habilitado.
- Confirmar recebimento em evento de teste.

## 4.7 Recomendacoes de seguranca clinica

- Sempre revisar sugestoes IA antes de salvar.
- Priorizar preenchimento completo do SOAP em casos complexos.
- Fechar encontro apenas apos validar conduta final.
- Usar PDF clinico para referencia e continuidade de cuidado.

## 4.8 Cadastro de Pacientes

**CPF recomendado no cadastro:**
- O campo CPF no cadastro de paciente agora é recomendado (não obrigatório).
- Quando preenchido, o sistema garante que o mesmo paciente não será duplicado entre estabelecimentos IntelliCare.
- O paciente recebe um identificador único que o acompanha em toda a rede.
- Não há mudança visual no formulário — o comportamento é automático e transparente.

## 4.9 Cadastro de Profissionais

**CPF recomendado no cadastro de profissional:**
- Igualmente ao cadastro de pacientes, o CPF de profissionais agora conecta ao sistema de identidade central.
- Quando preenchido, o profissional é reconhecido em todos os estabelecimentos da rede.
- Comportamento transparente — sem mudança visual no formulário.
