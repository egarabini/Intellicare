# Scripts de Implementação - Projeto 02

Scripts para setup e migração da infraestrutura OLTP/OLAP.

---

## 🚀 Execução Rápida

### Opção 1: Script Automatizado (Recomendado)

```powershell
# Executar setup completo automatizado
cd C:\DOCSHARE\INTELLICARE\Documentacao\consolidacao\docs_DEV1\scripts
.\00_executar_setup.ps1
```

### Opção 2: Execução Manual

Consulte as seções abaixo para execução passo a passo.

---

## 📋 Índice de Scripts

### 0. Utilitários

#### `00_GUIA_INSTALACAO.md`
**Objetivo**: Guia completo de instalação do PostgreSQL

**Conteúdo**:
- Instalação PostgreSQL no Windows
- Configuração de PATH
- Alternativa com Docker
- Troubleshooting

#### `00_executar_setup.ps1`
**Objetivo**: Script PowerShell para execução automatizada

**Execução**:
```powershell
.\00_executar_setup.ps1
```

**Opções**:
1. Setup completo (OLTP + OLAP + Migração)
2. Apenas OLTP (Dia 1)
3. Apenas OLAP (Dia 2)
4. Apenas Migração (Dia 3)
5. Apenas Testes
6. Limpar tudo (DROP databases)

---

### 1. Setup de Bancos de Dados

#### `01_setup_oltp.sql`
**Objetivo**: Criar database PostgreSQL OLTP (Operacional)

**Execução**:
```bash
psql -h localhost -U postgres -f 01_setup_oltp.sql
```

**O que faz**:
- Cria database `intellicare_oltp`
- Cria schemas `donabedian` e `wanda`
- Cria usuário `intellicare_app` (read/write)
- Cria 6 tabelas operacionais
- Cria 13 índices de performance
- Configura triggers de auditoria

**Tempo estimado**: 5 minutos

---

#### `02_setup_olap.sql`
**Objetivo**: Criar database PostgreSQL OLAP (Analítico)

**Execução**:
```bash
psql -h localhost -U postgres -f 02_setup_olap.sql
```

**O que faz**:
- Cria database `intellicare_olap`
- Cria schemas `analytics_donabedian` e `analytics_wanda`
- Cria usuário `intellicare_analytics` (read-only)
- Cria 2 tabelas fato (particionadas)
- Cria 9 índices analíticos
- Cria 3 funções de anonimização (SHA-256)
- Configura política de retenção (5 anos)

**Tempo estimado**: 5 minutos

---

### 2. Migração de Dados

#### `03_migrate_data.py`
**Objetivo**: Migrar dados históricos para OLTP

**Pré-requisitos**:
```bash
pip install psycopg2-binary
```

**Execução**:
```bash
python 03_migrate_data.py
```

**O que faz**:
- Conecta ao OLTP
- Insere 3 indicadores de exemplo
- Insere 36 medições (12 meses)
- Insere 50 leitos
- Insere 200 ocupações (6 meses)
- Valida contagem de registros

**Tempo estimado**: 2 minutos

---

### 3. Testes e Validação

#### `04_test_connections.py`
**Objetivo**: Testar conectividade e permissões

**Execução**:
```bash
python 04_test_connections.py
```

**O que testa**:
- ✅ Conexão OLTP
- ✅ Conexão OLAP
- ✅ Permissões OLTP (read/write)
- ✅ Permissões OLAP (read-only)
- ✅ Schemas e tabelas
- ✅ Funções de anonimização

**Tempo estimado**: 1 minuto

---

#### `05_validate_data.py`
**Objetivo**: Validar integridade dos dados migrados

**Execução**:
```bash
python 05_validate_data.py
```

**O que valida**:
- ✅ Contagem de registros
- ✅ Integridade referencial
- ✅ Qualidade dos dados
- ✅ Existência de índices
- 📊 Gera estatísticas

**Tempo estimado**: 1 minuto

---

## 🚀 Guia de Execução Completo

### Dia 1 (20/02) - Setup OLTP

```bash
# 1. Executar setup OLTP
psql -h localhost -U postgres -f 01_setup_oltp.sql

# 2. Validar estrutura
psql -h localhost -U postgres -d intellicare_oltp -c "\dt donabedian.*"
psql -h localhost -U postgres -d intellicare_oltp -c "\dt wanda.*"
```

---

### Dia 2 (21/02) - Setup OLAP

```bash
# 1. Executar setup OLAP
psql -h localhost -U postgres -f 02_setup_olap.sql

# 2. Testar funções de anonimização
psql -h localhost -U postgres -d intellicare_olap -c "SELECT hash_id(123);"
psql -h localhost -U postgres -d intellicare_olap -c "SELECT categorizar_valor(50, 30, 70);"
```

---

### Dia 3 (24/02) - Migração de Dados

```bash
# 1. Instalar dependências
pip install psycopg2-binary

# 2. Executar migração
python 03_migrate_data.py

# 3. Validar dados
python 05_validate_data.py
```

---

### Dia 4 (25/02) - Testes de Conexão

```bash
# 1. Testar conexões e permissões
python 04_test_connections.py

# 2. Validar contagens
psql -h localhost -U intellicare_app -d intellicare_oltp -c "SELECT COUNT(*) FROM donabedian.indicadores;"
psql -h localhost -U intellicare_analytics -d intellicare_olap -c "SELECT COUNT(*) FROM analytics_donabedian.fato_medicoes;"
```

---

## 📊 Estrutura de Dados

### OLTP (Operacional)

```
intellicare_oltp/
├── donabedian/
│   ├── indicadores (3 registros)
│   ├── medicoes (36 registros)
│   └── planos_acao (0 registros)
│
└── wanda/
    ├── leitos (50 registros)
    ├── ocupacoes (200 registros)
    └── transferencias (0 registros)
```

### OLAP (Analítico)

```
intellicare_olap/
├── analytics_donabedian/
│   └── fato_medicoes (particionado por ano)
│       ├── fato_medicoes_2024
│       ├── fato_medicoes_2025
│       └── fato_medicoes_2026
│
└── analytics_wanda/
    └── fato_ocupacoes (anonimizado)
```

---

## 🔐 Credenciais

### OLTP (Read/Write)
- **Host**: localhost
- **Database**: intellicare_oltp
- **User**: intellicare_app
- **Password**: IntelliCare@2026!OLTP

### OLAP (Read-Only)
- **Host**: localhost
- **Database**: intellicare_olap
- **User**: intellicare_analytics
- **Password**: IntelliCare@2026!OLAP

---

## ⚠️ Troubleshooting

### Erro: "database already exists"
```bash
# Remover database existente
psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS intellicare_oltp;"
psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS intellicare_olap;"
```

### Erro: "role already exists"
```bash
# Remover usuários existentes
psql -h localhost -U postgres -c "DROP USER IF EXISTS intellicare_app;"
psql -h localhost -U postgres -c "DROP USER IF EXISTS intellicare_analytics;"
```

### Erro: "permission denied"
```bash
# Verificar permissões
psql -h localhost -U postgres -d intellicare_oltp -c "\du"
```

---

## 📝 Logs

Todos os scripts Python geram logs detalhados:
- ✅ Sucesso
- ❌ Erro
- 📊 Estatísticas
- 🔍 Detalhes

---

## 🎯 Checklist de Validação

- [ ] Database OLTP criado
- [ ] Database OLAP criado
- [ ] 6 tabelas OLTP criadas
- [ ] 2 tabelas OLAP criadas
- [ ] Usuários criados e permissões configuradas
- [ ] Dados migrados (3 indicadores, 36 medições, 50 leitos, 200 ocupações)
- [ ] Testes de conexão passando
- [ ] Validações de integridade passando
- [ ] Funções de anonimização funcionando

---

**Última atualização**: 20/02/2026  
**Responsável**: DEV1  
**Projeto**: 02 - Separação Operacional/Analítico

