# 12. Receituario Digital (DEM-072)

## O que e

O **Receituario Digital** gera um PDF medico padronizado com base CFM/ANVISA, a partir de uma prescricao registrada no Oswaldo.

## Onde acessar

No `ClinicoUI`:

1. abrir paciente;
2. ir para aba `Prescrição` (Oswaldo);
3. no **Historico de Prescricoes**, clicar em **Imprimir Receituário**.

## Tipos de receituario

- **Receita Comum (`simple`)**
  - uso para medicacoes gerais.
- **Receita de Controle Especial (`special_control`)**
  - uso para medicamentos de controle especial (ex.: tarja preta);
  - exige dados adicionais obrigatorios conforme regra legal, como CPF do paciente, validade e numero de notificacao.

## O que aparece no PDF

- cabecalho com identificacao do profissional (incluindo CRM);
- simbolo medico `℞`;
- lista de medicamentos com posologia formatada;
- elementos de autenticidade (ex.: QR code, quando habilitado no ambiente);
- area de assinatura.

## Impressao

- o PDF abre em nova aba;
- para imprimir: `Ctrl + P` ou botao de impressao do navegador.

## Exemplo de uso

1. clinico fecha a prescricao no encontro;
2. abre o historico da prescricao;
3. seleciona tipo de receituario;
4. abre PDF e imprime para entrega/arquivo.

## Captura de tela sugerida

- menu de "Imprimir Receituário" aberto no historico;
- PDF do receituario aberto em nova aba.
