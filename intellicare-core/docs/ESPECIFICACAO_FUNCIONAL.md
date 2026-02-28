# intellicare-core — Especificacao Funcional

## 1. Proposito

O intellicare-core e a **biblioteca compartilhada** (SDK) que fornece funcionalidades comuns a todos os modulos IntelliCare. Ele NAO e um servico — e um pacote Python que outros modulos importam.

## 2. Funcionalidades

### 2.1 Cliente FHIR R4
- Comunicacao HTTP com servidores FHIR (HAPI FHIR)
- Busca de pacientes por CPF, nome, ID
- Leitura de recursos FHIR (Patient, Observation, Condition, etc.)
- Suporte a International Patient Summary (IPS Brasil)
- Cache de requisicoes para reduzir carga no servidor

### 2.2 Gerenciamento de Configuracao
- Configuracao centralizada via variaveis de ambiente
- Validacao automatica de configuracoes
- Valores padrao sensiveis para desenvolvimento local
- Suporte a arquivos .env

### 2.3 Logging Estruturado
- Formato padrao de logs para todos os modulos
- Niveis configuráveis (DEBUG, INFO, WARNING, ERROR)
- Correlacao de logs entre modulos (trace ID)
- Saida JSON para ambientes de producao

### 2.4 Contratos de Modulo
- Interface padrao que todo modulo deve implementar
- Schema de informacao do modulo (nome, versao, capabilities)
- Schema de health check (status, dependencias)
- Schema base de resposta de analise

### 2.5 Autenticacao (futuro)
- Cliente Keycloak para validacao de tokens
- Decoradores de autorizacao para rotas FastAPI
- Roles padrao do IntelliCare

## 3. Usuarios

O intellicare-core e usado por:
- Desenvolvedores que criam novos modulos IntelliCare
- Todos os modulos existentes (Oswaldo, Florence, etc.)
- O portal (indiretamente, via APIs dos modulos)

## 4. Restricoes

- NAO deve conter logica de negocio de nenhum agente especifico
- NAO deve ter dependencias pesadas (sem torch, sem tensorflow, sem pandas)
- DEVE ser leve e rapido de instalar (< 30 segundos)
- DEVE ser compativel com Python 3.11+
- DEVE ter cobertura de testes >= 90% (por ser fundacao)

## 5. Origem do Codigo

| Funcionalidade | Arquivo no INTELLICAREREPO |
|---------------|---------------------------|
| FHIR Client | `agentes/mcp_servers/fhir_mcp_server.py` (extrair classe client) |
| Config Base | `agentes/mcp_servers/config.py` + `agentes/wanda/config.py` |
| Base Agent | `agentes/wanda/subagents/base.py` |
| Logging | `structlog` patterns de `agentes/mcp_servers/` |
| Modelos FHIR | `agentes/mcp_servers/fhir_mcp_server.py` (PatientSummary, IPS, etc.) |
