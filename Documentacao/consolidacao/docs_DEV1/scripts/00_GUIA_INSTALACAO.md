# Guia de Instalação - PostgreSQL para Projeto 02

---

## 📋 Pré-requisitos

Para executar os scripts do Projeto 02, você precisa ter o PostgreSQL instalado.

---

## 🔧 Instalação do PostgreSQL no Windows

### Opção 1: Instalador Oficial (Recomendado)

1. **Download**:
   - Acesse: https://www.postgresql.org/download/windows/
   - Baixe o instalador EDB para Windows
   - Versão recomendada: PostgreSQL 15 ou superior

2. **Instalação**:
   ```
   - Execute o instalador
   - Porta padrão: 5432
   - Senha do superuser (postgres): anote esta senha!
   - Locale: Portuguese, Brazil (pt_BR.UTF-8)
   - Componentes: PostgreSQL Server, pgAdmin 4, Command Line Tools
   ```

3. **Adicionar ao PATH**:
   ```powershell
   # Adicionar PostgreSQL ao PATH do sistema
   $env:Path += ";C:\Program Files\PostgreSQL\15\bin"
   
   # Para tornar permanente, adicione nas variáveis de ambiente do sistema
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\PostgreSQL\15\bin", "Machine")
   ```

4. **Verificar instalação**:
   ```powershell
   psql --version
   # Deve retornar: psql (PostgreSQL) 15.x
   ```

---

### Opção 2: Docker (Alternativa)

Se preferir usar Docker:

```powershell
# 1. Instalar Docker Desktop para Windows
# Download: https://www.docker.com/products/docker-desktop

# 2. Executar PostgreSQL em container
docker run --name intellicare-postgres `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=postgres `
  -p 5432:5432 `
  -d postgres:15

# 3. Verificar se está rodando
docker ps

# 4. Conectar ao PostgreSQL
docker exec -it intellicare-postgres psql -U postgres
```

---

## 🚀 Execução dos Scripts

### Passo 1: Verificar Conexão

```powershell
# Testar conexão com PostgreSQL
psql -h localhost -U postgres -c "SELECT version();"
```

### Passo 2: Executar Setup OLTP (Dia 1)

```powershell
# Navegar até o diretório de scripts
cd C:\DOCSHARE\INTELLICARE\Documentacao\consolidacao\docs_DEV1\scripts

# Executar script de setup OLTP
psql -h localhost -U postgres -f 01_setup_oltp.sql

# Validar estrutura criada
psql -h localhost -U postgres -d intellicare_oltp -c "\dt donabedian.*"
psql -h localhost -U postgres -d intellicare_oltp -c "\dt wanda.*"
```

### Passo 3: Executar Setup OLAP (Dia 2)

```powershell
# Executar script de setup OLAP
psql -h localhost -U postgres -f 02_setup_olap.sql

# Testar funções de anonimização
psql -h localhost -U postgres -d intellicare_olap -c "SELECT hash_id(123);"
psql -h localhost -U postgres -d intellicare_olap -c "SELECT categorizar_valor(50, 30, 70);"
```

### Passo 4: Migrar Dados (Dia 3)

```powershell
# Instalar dependências Python
pip install psycopg2-binary

# Executar migração
python 03_migrate_data.py

# Validar dados
python 05_validate_data.py
```

### Passo 5: Testar Conexões (Dia 4)

```powershell
# Executar testes de conexão
python 04_test_connections.py
```

---

## 🔐 Credenciais Padrão

### PostgreSQL Superuser:
- **User**: postgres
- **Password**: (definida durante instalação)
- **Host**: localhost
- **Port**: 5432

### OLTP (Criado pelo script):
- **Database**: intellicare_oltp
- **User**: intellicare_app
- **Password**: IntelliCare@2026!OLTP

### OLAP (Criado pelo script):
- **Database**: intellicare_olap
- **User**: intellicare_analytics
- **Password**: IntelliCare@2026!OLAP

---

## ⚠️ Troubleshooting

### Erro: "psql: command not found"
**Solução**: PostgreSQL não está no PATH
```powershell
# Adicionar ao PATH temporariamente
$env:Path += ";C:\Program Files\PostgreSQL\15\bin"

# Ou reiniciar o terminal após instalação
```

### Erro: "connection refused"
**Solução**: PostgreSQL não está rodando
```powershell
# Verificar serviço
Get-Service -Name "*postgres*"

# Iniciar serviço
Start-Service postgresql-x64-15
```

### Erro: "database already exists"
**Solução**: Remover databases existentes
```powershell
psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS intellicare_oltp;"
psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS intellicare_olap;"
```

### Erro: "locale pt_BR.UTF-8 not found"
**Solução**: Usar locale padrão
```sql
-- Editar scripts SQL e trocar:
LC_COLLATE = 'pt_BR.UTF-8'
-- Por:
LC_COLLATE = 'Portuguese_Brazil.1252'
```

---

## 📊 Validação Pós-Instalação

Após executar todos os scripts, valide:

```powershell
# 1. Listar databases
psql -h localhost -U postgres -c "\l"

# 2. Verificar tabelas OLTP
psql -h localhost -U postgres -d intellicare_oltp -c "\dt donabedian.*"
psql -h localhost -U postgres -d intellicare_oltp -c "\dt wanda.*"

# 3. Verificar tabelas OLAP
psql -h localhost -U postgres -d intellicare_olap -c "\dt analytics_donabedian.*"
psql -h localhost -U postgres -d intellicare_olap -c "\dt analytics_wanda.*"

# 4. Contar registros
psql -h localhost -U intellicare_app -d intellicare_oltp -c "SELECT COUNT(*) FROM donabedian.indicadores;"
psql -h localhost -U intellicare_app -d intellicare_oltp -c "SELECT COUNT(*) FROM wanda.leitos;"
```

---

## 📋 Checklist de Instalação

- [ ] PostgreSQL 15+ instalado
- [ ] Serviço PostgreSQL rodando
- [ ] `psql` disponível no PATH
- [ ] Conexão testada com sucesso
- [ ] Script `01_setup_oltp.sql` executado
- [ ] Script `02_setup_olap.sql` executado
- [ ] Dependências Python instaladas (`psycopg2-binary`)
- [ ] Script `03_migrate_data.py` executado
- [ ] Script `04_test_connections.py` passou
- [ ] Script `05_validate_data.py` passou

---

## 🎯 Próximos Passos

Após instalação e execução bem-sucedida:

1. ✅ Databases OLTP e OLAP criados
2. ✅ Dados históricos migrados
3. ✅ Testes de conexão passando
4. 🚀 Iniciar Semana 2: Pipeline ETL

---

**Data**: 20/02/2026  
**Responsável**: DEV1  
**Projeto**: 02 - Separação Operacional/Analítico

