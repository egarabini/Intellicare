# 13. Gestao de Prompts IA (DEM-073)

## O que sao prompts IA

Prompts IA sao instrucoes-base usadas pelos modulos clinicos para gerar sugestoes de texto (Florence e Oswaldo).  
Com versionamento, ajustes de comportamento nao exigem novo deploy.

## Quem pode acessar

Apenas perfil **Administrador da Plataforma** no `AdminUI`.

## Como acessar

No `AdminUI`:

1. menu lateral `Prompts IA`;
2. rota `/admin/prompts`.

## O que a tela mostra

- slug/nome do prompt;
- versao ativa;
- data da ultima alteracao;
- historico de versoes.

## Como editar um prompt

1. clicar no prompt desejado;
2. editar o texto no editor;
3. preencher **Descricao da alteracao** (obrigatorio);
4. clicar em **Salvar nova versão**;
5. no historico, clicar em **Ativar** na versao que deve entrar em uso.

## Como fazer rollback

No historico, selecionar versao anterior e clicar em **Ativar**.

## Prompts disponiveis e finalidade

| Prompt | Modulo | O que controla |
|--------|--------|---------------|
| `florence_soap` | Florence | Geracao de nota SOAP clinica |
| `florence_free_text` | Florence | Nota em texto livre |
| `oswaldo_prescription` | Oswaldo | Sugestao de prescricao |
| `oswaldo_cid10` | Oswaldo | Sugestao de CID-10 por sintomas |

## Aviso importante

Mudancas em prompts afetam as sugestoes de IA apos ativacao da versao.  
Boas praticas:

- testar em homologacao antes de ativar em producao;
- registrar descricao de alteracao clara (motivo clinico/operacional);
- usar rollback rapido se houver regressao de qualidade.

## Captura de tela sugerida

- listagem de prompts com versao ativa;
- editor aberto com historico e acao de ativacao.
