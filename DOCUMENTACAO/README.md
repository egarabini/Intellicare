# IntelliCare - Documentacao de Usuario

Este pacote foi criado para uso operacional dos perfis do IntelliCare e cobre o sistema ate o que ja foi desenvolvido e validado em codigo.

## Escopo desta versao

- Cobertura funcional: entregas concluidas ate `DEM-063`.
- Item ainda em andamento: `DEM-064` (validacao em staging).
- Modulos considerados: `admin`, `gestor`, `cuidado` (ClinicoUI + PacienteUI), `florence`, `oswaldo`, `careplanner`.

## Arquivos deste pacote

- `01_VISAO_GERAL_INTELLICARE.md` - arquitetura funcional, perfis e mapa de navegacao.
- `02_GUIA_ADMINISTRADOR_PLATAFORMA.md` - operacao do AdminUI.
- `03_GUIA_GESTOR_TENANT.md` - operacao do GestorUI.
- `04_GUIA_CLINICO.md` - operacao do ClinicoUI (encontro, Florence, Oswaldo, jornadas).
- `05_GUIA_PACIENTE.md` - operacao do PacienteUI.
- `06_DASHBOARDS_E_RELATORIOS.md` - leitura de indicadores, alertas e PDFs.
- `07_CHECKLIST_IMPLANTACAO_E_TREINAMENTO.md` - onboarding e runbook de adocao.
- `08_PLANO_CAPTURA_PRINTS_GUIADOS.md` - padrao operacional de captura de telas.
- `09_STORYBOARD_PRINTS_POR_PERFIL.md` - lista de prints obrigatorios por perfil.
- `10_MODELO_LEGENDAS_E_ANONIMIZACAO.md` - template de legenda e checklist LGPD.
- `MANUAL_USUARIO_INTELLICARE_COMPLETO.md` - manual unico consolidado para PDF.
- `MANUAL_USUARIO_INTELLICARE_PRONTO_PARA_IMPRESSAO.md` - versao editorial com capa, sumario e quebras de pagina.
- `MANUAL_USUARIO_INTELLICARE_PRONTO_PARA_IMPRESSAO.html` - versao HTML estilizada para impressao/PDF.

## URLs base (ambiente local)

- AdminUI: `http://127.0.0.1:9000/admin-ui/`
- GestorUI: `http://127.0.0.1:9000/gestor-ui/`
- ClinicoUI: `http://127.0.0.1:9000/clinico-ui/`
- PacienteUI: `http://127.0.0.1:9000/paciente-ui/`

## Observacao importante

As telas podem evoluir em layout, mas os fluxos e capacidades abaixo foram escritos a partir da implementacao atual e das demandas concluidas. Onde existir variacao entre ambiente local/staging/producao, considerar a regra operacional do seu ambiente.
