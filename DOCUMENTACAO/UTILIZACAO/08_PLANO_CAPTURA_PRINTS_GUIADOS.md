# 8. Plano de Captura de Prints Guiados

Este documento define como produzir imagens de tela para o manual de usuario do IntelliCare com consistencia visual e seguranca de dados.

## 8.1 Objetivo

Padronizar capturas para:

- treinamento de novos usuarios;
- onboarding operacional por perfil;
- material de suporte interno.

## 8.2 Regras gerais de captura

- Capturar em resolucao minima de `1920x1080`.
- Usar navegador com zoom em `100%`.
- Capturar tela cheia da pagina (evitar recortes pequenos).
- Manter o menu lateral visivel quando fizer sentido pedagogico.
- Priorizar estados reais de uso: dados, status e botoes acionaveis.

## 8.3 Convencao de nomes dos arquivos

Padrao:

`<ordem>_<perfil>_<modulo>_<tela>_<acao>.png`

Exemplos:

- `01_admin_dashboard_visao-geral.png`
- `07_gestor_careplanner_nova-jornada_formulario.png`
- `14_clinico_encounter_florence-soap_preenchido.png`
- `22_paciente_jornadas_lista-status.png`

## 8.4 Estrutura recomendada (opcional)

Sugestao de organizacao dentro de `DOCUMENTACAO`:

- `prints/admin/`
- `prints/gestor/`
- `prints/clinico/`
- `prints/paciente/`

## 8.5 Padrrao de destaque visual

Para cada print, aplicar ate 3 marcacoes:

- Retangulo `azul`: area principal de acao.
- Retangulo `verde`: resultado esperado.
- Retangulo `laranja`: alerta/campo obrigatorio.

Evitar excesso de setas e textos na imagem. A explicacao detalhada deve ficar na legenda.

## 8.6 Qualidade minima antes de aprovar print

- Texto legivel sem zoom adicional.
- Data/hora visivel quando relevante ao fluxo.
- Nenhum dado sensivel em claro.
- Elemento citado na legenda realmente aparece na imagem.
- Nome do arquivo segue padrao.

## 8.7 Sequencia de captura recomendada

1. Admin
2. Gestor
3. Clinico
4. Paciente

Essa ordem reduz retrabalho porque o setup de tenant/equipe normalmente comeca no Admin/Gestor.
