# EXECUÇÃO SEMANA 1: INFRAESTRUTURA

## 📌 ID: DEV1-EXEC-002-S1
## 📅 Período: 20/02/2026 - 26/02/2026
## 👤 Responsável: DEV1
## 🎯 Objetivo: Setup completo da infraestrutura OLTP/OLAP

---

## 🎯 OBJETIVO DA SEMANA 1

Configurar a infraestrutura completa de bancos de dados separados (OLTP e OLAP), migrar dados históricos dos 2 módulos piloto e validar conectividade.

**Esforço**: 16 horas  
**Entregável**: 2 bancos PostgreSQL funcionando com dados migrados

---

## 📋 CHECKLIST GERAL

### Infraestrutura:
- [ ] PostgreSQL OLTP configurado
- [ ] PostgreSQL OLAP configurado
- [ ] Schemas criados para 2 módulos
- [ ] Dados históricos migrados
- [ ] Conexões configuradas nos módulos
- [ ] Conectividade validada

---

## 📅 CRONOGRAMA DETALHADO

### 🗓️ DIA 1 - Quinta, 20/02 (4h)

#### 09:00-10:00 | Setup PostgreSQL OLTP (1h)
**Objetivo**: Configurar banco operacional

**Tarefas**:
```bash
# 1. Conectar ao servidor PostgreSQL
psql -h localhost -U postgres

# 2. Criar database OLTP
CREATE DATABASE intellicare_oltp
    WITH 
    ENCODING = 'UTF8'
    LC_COLLATE = 'pt_BR.UTF-8'
    LC_CTYPE = 'pt_BR.UTF-8'
    TEMPLATE = template0;

# 3. Conectar ao database
\c intellicare_oltp

# 4. Criar schemas para módulos
CREATE SCHEMA donabedian;
CREATE SCHEMA wanda;

# 5. Configurar permissões
CREATE USER intellicare_app WITH PASSWORD 'senha_segura';
GRANT CONNECT ON DATABASE intellicare_oltp TO intellicare_app;
GRANT USAGE ON SCHEMA donabedian, wanda TO intellicare_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA donabedian, wanda TO intellicare_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA donabedian, wanda 
    GRANT ALL ON TABLES TO intellicare_app;
```

**Checklist**:
- [ ] Database `intellicare_oltp` criado
- [ ] Schemas `donabedian` e `wanda` criados
- [ ] Usuário `intellicare_app` criado
- [ ] Permissões configuradas

---

#### 10:00-11:00 | Criar Tabelas OLTP - Donabedian (1h)
**Objetivo**: Criar estrutura de tabelas operacionais

**Tarefas**:
```sql
-- Schema: donabedian (Indicadores de Qualidade)

-- Tabela: indicadores
CREATE TABLE donabedian.indicadores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    descricao TEXT,
    tipo VARCHAR(50) NOT NULL, -- estrutura, processo, resultado
    formula TEXT,
    meta_valor DECIMAL(10,2),
    meta_unidade VARCHAR(20),
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela: medicoes
CREATE TABLE donabedian.medicoes (
    id SERIAL PRIMARY KEY,
    indicador_id INTEGER REFERENCES donabedian.indicadores(id),
    periodo_inicio DATE NOT NULL,
    periodo_fim DATE NOT NULL,
    valor_medido DECIMAL(10,2) NOT NULL,
    valor_meta DECIMAL(10,2),
    atingiu_meta BOOLEAN,
    observacoes TEXT,
    responsavel_id INTEGER, -- FK para usuários
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela: planos_acao
CREATE TABLE donabedian.planos_acao (
    id SERIAL PRIMARY KEY,
    medicao_id INTEGER REFERENCES donabedian.medicoes(id),
    descricao TEXT NOT NULL,
    prazo DATE,
    status VARCHAR(50) DEFAULT 'pendente',
    responsavel_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX idx_medicoes_indicador ON donabedian.medicoes(indicador_id);
CREATE INDEX idx_medicoes_periodo ON donabedian.medicoes(periodo_inicio, periodo_fim);
CREATE INDEX idx_planos_medicao ON donabedian.planos_acao(medicao_id);
```

**Checklist**:
- [ ] Tabela `indicadores` criada
- [ ] Tabela `medicoes` criada
- [ ] Tabela `planos_acao` criada
- [ ] Índices criados

---

#### 11:00-12:00 | Criar Tabelas OLTP - Wanda (1h)
**Objetivo**: Criar estrutura de tabelas operacionais

**Tarefas**:
```sql
-- Schema: wanda (Gestão de Leitos)

-- Tabela: leitos
CREATE TABLE wanda.leitos (
    id SERIAL PRIMARY KEY,
    numero VARCHAR(20) NOT NULL,
    setor VARCHAR(100) NOT NULL,
    tipo VARCHAR(50) NOT NULL, -- UTI, enfermaria, isolamento
    status VARCHAR(50) DEFAULT 'disponivel',
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela: ocupacoes
CREATE TABLE wanda.ocupacoes (
    id SERIAL PRIMARY KEY,
    leito_id INTEGER REFERENCES wanda.leitos(id),
    paciente_id INTEGER NOT NULL, -- FK para pacientes
    data_entrada TIMESTAMP NOT NULL,
    data_saida TIMESTAMP,
    motivo_internacao TEXT,
    status VARCHAR(50) DEFAULT 'ativo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela: transferencias
CREATE TABLE wanda.transferencias (
    id SERIAL PRIMARY KEY,
    ocupacao_id INTEGER REFERENCES wanda.ocupacoes(id),
    leito_origem_id INTEGER REFERENCES wanda.leitos(id),
    leito_destino_id INTEGER REFERENCES wanda.leitos(id),
    data_transferencia TIMESTAMP NOT NULL,
    motivo TEXT,
    responsavel_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX idx_ocupacoes_leito ON wanda.ocupacoes(leito_id);
CREATE INDEX idx_ocupacoes_paciente ON wanda.ocupacoes(paciente_id);
CREATE INDEX idx_ocupacoes_datas ON wanda.ocupacoes(data_entrada, data_saida);
CREATE INDEX idx_transferencias_ocupacao ON wanda.transferencias(ocupacao_id);
```

**Checklist**:
- [ ] Tabela `leitos` criada
- [ ] Tabela `ocupacoes` criada
- [ ] Tabela `transferencias` criada
- [ ] Índices criados

---

#### 14:00-15:00 | Backup e Documentação (1h)
**Objetivo**: Documentar configurações e criar backup

**Tarefas**:
```bash
# 1. Criar backup da estrutura
pg_dump -h localhost -U postgres -s intellicare_oltp > oltp_schema_backup.sql

# 2. Documentar conexões
cat > config_oltp.md << EOF
# Configuração PostgreSQL OLTP

## Conexão
- Host: localhost
- Port: 5432
- Database: intellicare_oltp
- User: intellicare_app
- Password: [vault]

## Schemas
- donabedian: Indicadores de Qualidade
- wanda: Gestão de Leitos

## Tabelas
### donabedian
- indicadores (3 colunas principais)
- medicoes (8 colunas principais)
- planos_acao (6 colunas principais)

### wanda
- leitos (7 colunas principais)
- ocupacoes (8 colunas principais)
- transferencias (7 colunas principais)
EOF
```

**Checklist**:
- [ ] Backup da estrutura criado
- [ ] Documentação de configuração criada
- [ ] Credenciais armazenadas no vault

---

### 🗓️ DIA 2 - Sexta, 21/02 (4h)

#### 09:00-10:00 | Setup PostgreSQL OLAP (1h)
**Objetivo**: Configurar banco analítico

**Tarefas**:
```sql
-- 1. Criar database OLAP
CREATE DATABASE intellicare_olap
    WITH 
    ENCODING = 'UTF8'
    LC_COLLATE = 'pt_BR.UTF-8'
    LC_CTYPE = 'pt_BR.UTF-8'
    TEMPLATE = template0;

\c intellicare_olap

-- 2. Criar schemas analíticos
CREATE SCHEMA analytics_donabedian;
CREATE SCHEMA analytics_wanda;

-- 3. Configurar usuário read-only
CREATE USER intellicare_analytics WITH PASSWORD 'senha_segura_analytics';
GRANT CONNECT ON DATABASE intellicare_olap TO intellicare_analytics;
GRANT USAGE ON SCHEMA analytics_donabedian, analytics_wanda TO intellicare_analytics;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics_donabedian, analytics_wanda TO intellicare_analytics;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics_donabedian, analytics_wanda 
    GRANT SELECT ON TABLES TO intellicare_analytics;
```

**Checklist**:
- [ ] Database `intellicare_olap` criado
- [ ] Schemas analíticos criados
- [ ] Usuário read-only criado

---

#### 10:00-12:00 | Criar Tabelas OLAP (2h)
**Objetivo**: Criar estrutura de tabelas analíticas com anonimização

**Tarefas**:
```sql
-- Schema: analytics_donabedian

-- Tabela: fato_medicoes (anonimizada)
CREATE TABLE analytics_donabedian.fato_medicoes (
    id SERIAL PRIMARY KEY,
    indicador_hash VARCHAR(64) NOT NULL, -- SHA-256 do ID original
    indicador_nome VARCHAR(200),
    indicador_tipo VARCHAR(50),
    periodo_ano INTEGER NOT NULL,
    periodo_mes INTEGER NOT NULL,
    periodo_trimestre INTEGER,
    valor_medido DECIMAL(10,2),
    valor_meta DECIMAL(10,2),
    atingiu_meta BOOLEAN,
    faixa_valor VARCHAR(20), -- categorização: baixo, médio, alto
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Particionamento por ano
CREATE TABLE analytics_donabedian.fato_medicoes_2024 
    PARTITION OF analytics_donabedian.fato_medicoes
    FOR VALUES FROM (2024) TO (2025);

CREATE TABLE analytics_donabedian.fato_medicoes_2025 
    PARTITION OF analytics_donabedian.fato_medicoes
    FOR VALUES FROM (2025) TO (2026);

CREATE TABLE analytics_donabedian.fato_medicoes_2026 
    PARTITION OF analytics_donabedian.fato_medicoes
    FOR VALUES FROM (2026) TO (2027);

-- Schema: analytics_wanda

-- Tabela: fato_ocupacoes (anonimizada)
CREATE TABLE analytics_wanda.fato_ocupacoes (
    id SERIAL PRIMARY KEY,
    leito_hash VARCHAR(64) NOT NULL, -- SHA-256 do ID original
    paciente_hash VARCHAR(64) NOT NULL, -- SHA-256 do ID do paciente
    setor VARCHAR(100),
    tipo_leito VARCHAR(50),
    data_entrada_ano INTEGER,
    data_entrada_mes INTEGER,
    data_entrada_dia_semana INTEGER,
    tempo_permanencia_dias INTEGER,
    faixa_permanencia VARCHAR(20), -- curta, média, longa
    status_final VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices analíticos
CREATE INDEX idx_fato_medicoes_periodo ON analytics_donabedian.fato_medicoes(periodo_ano, periodo_mes);
CREATE INDEX idx_fato_medicoes_tipo ON analytics_donabedian.fato_medicoes(indicador_tipo);
CREATE INDEX idx_fato_ocupacoes_periodo ON analytics_wanda.fato_ocupacoes(data_entrada_ano, data_entrada_mes);
CREATE INDEX idx_fato_ocupacoes_setor ON analytics_wanda.fato_ocupacoes(setor);
```

**Checklist**:
- [ ] Tabela `fato_medicoes` criada com particionamento
- [ ] Tabela `fato_ocupacoes` criada
- [ ] Índices analíticos criados
- [ ] Campos anonimizados definidos

---

#### 14:00-15:00 | Configurar Retenção e Políticas (1h)
**Objetivo**: Configurar políticas de retenção de dados

**Tarefas**:
```sql
-- Política de retenção OLAP (manter 5 anos)
CREATE OR REPLACE FUNCTION analytics_donabedian.cleanup_old_data()
RETURNS void AS $$
BEGIN
    DELETE FROM analytics_donabedian.fato_medicoes
    WHERE created_at < CURRENT_DATE - INTERVAL '5 years';
END;
$$ LANGUAGE plpgsql;

-- Agendar limpeza mensal (via cron externo)
-- 0 0 1 * * psql -c "SELECT analytics_donabedian.cleanup_old_data();"

-- Política de backup
-- OLTP: Backup diário completo + WAL contínuo
-- OLAP: Backup semanal completo
```

**Checklist**:
- [ ] Função de limpeza criada
- [ ] Política de retenção documentada
- [ ] Política de backup documentada

---

### 🗓️ DIA 3 - Segunda, 24/02 (4h)

#### 09:00-11:00 | Migração Dados Históricos - Donabedian (2h)
**Objetivo**: Migrar dados históricos do módulo donabedian

**Tarefas**:
```python
# Script: migrate_donabedian.py
import psycopg2
from datetime import datetime
import hashlib

# Conexões
conn_source = psycopg2.connect("dbname=intellicare_old user=postgres")
conn_oltp = psycopg2.connect("dbname=intellicare_oltp user=intellicare_app")

cur_source = conn_source.cursor()
cur_oltp = conn_oltp.cursor()

# 1. Migrar indicadores
cur_source.execute("SELECT * FROM indicadores WHERE ativo = true")
indicadores = cur_source.fetchall()

for ind in indicadores:
    cur_oltp.execute("""
        INSERT INTO donabedian.indicadores 
        (nome, descricao, tipo, formula, meta_valor, meta_unidade, ativo)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (ind[1], ind[2], ind[3], ind[4], ind[5], ind[6], ind[7]))

# 2. Migrar medições (últimos 12 meses)
cur_source.execute("""
    SELECT * FROM medicoes 
    WHERE periodo_inicio >= CURRENT_DATE - INTERVAL '12 months'
""")
medicoes = cur_source.fetchall()

for med in medicoes:
    cur_oltp.execute("""
        INSERT INTO donabedian.medicoes 
        (indicador_id, periodo_inicio, periodo_fim, valor_medido, 
         valor_meta, atingiu_meta, observacoes, responsavel_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (med[1], med[2], med[3], med[4], med[5], med[6], med[7], med[8]))

conn_oltp.commit()
print(f"Migrados {len(indicadores)} indicadores e {len(medicoes)} medições")
```

**Checklist**:
- [ ] Script de migração criado
- [ ] Dados de indicadores migrados
- [ ] Dados de medições migrados (12 meses)
- [ ] Validação de contagem realizada

---

#### 11:00-13:00 | Migração Dados Históricos - Wanda (2h)
**Objetivo**: Migrar dados históricos do módulo wanda

**Tarefas**:
```python
# Script: migrate_wanda.py
import psycopg2

conn_source = psycopg2.connect("dbname=intellicare_old user=postgres")
conn_oltp = psycopg2.connect("dbname=intellicare_oltp user=intellicare_app")

cur_source = conn_source.cursor()
cur_oltp = conn_oltp.cursor()

# 1. Migrar leitos
cur_source.execute("SELECT * FROM leitos WHERE ativo = true")
leitos = cur_source.fetchall()

for leito in leitos:
    cur_oltp.execute("""
        INSERT INTO wanda.leitos 
        (numero, setor, tipo, status, ativo)
        VALUES (%s, %s, %s, %s, %s)
    """, (leito[1], leito[2], leito[3], leito[4], leito[5]))

# 2. Migrar ocupações (últimos 6 meses)
cur_source.execute("""
    SELECT * FROM ocupacoes 
    WHERE data_entrada >= CURRENT_DATE - INTERVAL '6 months'
""")
ocupacoes = cur_source.fetchall()

for ocup in ocupacoes:
    cur_oltp.execute("""
        INSERT INTO wanda.ocupacoes 
        (leito_id, paciente_id, data_entrada, data_saida, 
         motivo_internacao, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (ocup[1], ocup[2], ocup[3], ocup[4], ocup[5], ocup[6]))

conn_oltp.commit()
print(f"Migrados {len(leitos)} leitos e {len(ocupacoes)} ocupações")
```

**Checklist**:
- [ ] Script de migração criado
- [ ] Dados de leitos migrados
- [ ] Dados de ocupações migrados (6 meses)
- [ ] Validação de contagem realizada

---

### 🗓️ DIA 4 - Terça, 25/02 (2h)

#### 09:00-10:00 | Configurar Conexões nos Módulos (1h)
**Objetivo**: Atualizar módulos para usar OLTP

**Tarefas**:
```python
# intellicare-donabedian/config/database.py
from pydantic_settings import BaseSettings

class DatabaseSettings(BaseSettings):
    # OLTP (operacional) - READ/WRITE
    OLTP_HOST: str = "localhost"
    OLTP_PORT: int = 5432
    OLTP_DATABASE: str = "intellicare_oltp"
    OLTP_USER: str = "intellicare_app"
    OLTP_PASSWORD: str  # from vault
    
    # OLAP (analítico) - READ ONLY
    OLAP_HOST: str = "localhost"
    OLAP_PORT: int = 5432
    OLAP_DATABASE: str = "intellicare_olap"
    OLAP_USER: str = "intellicare_analytics"
    OLAP_PASSWORD: str  # from vault
    
    @property
    def oltp_url(self) -> str:
        return f"postgresql://{self.OLTP_USER}:{self.OLTP_PASSWORD}@{self.OLTP_HOST}:{self.OLTP_PORT}/{self.OLTP_DATABASE}"
    
    @property
    def olap_url(self) -> str:
        return f"postgresql://{self.OLAP_USER}:{self.OLAP_PASSWORD}@{self.OLAP_HOST}:{self.OLAP_PORT}/{self.OLAP_DATABASE}"
```

**Checklist**:
- [ ] Configuração OLTP adicionada
- [ ] Configuração OLAP adicionada
- [ ] Credenciais no vault configuradas
- [ ] Variáveis de ambiente documentadas

---

#### 10:00-11:00 | Testar Conectividade (1h)
**Objetivo**: Validar todas as conexões

**Tarefas**:
```python
# Script: test_connectivity.py
import psycopg2
from config.database import DatabaseSettings

settings = DatabaseSettings()

# Teste 1: Conexão OLTP (read/write)
try:
    conn_oltp = psycopg2.connect(settings.oltp_url)
    cur = conn_oltp.cursor()
    cur.execute("SELECT COUNT(*) FROM donabedian.indicadores")
    count = cur.fetchone()[0]
    print(f"✅ OLTP conectado: {count} indicadores")
    conn_oltp.close()
except Exception as e:
    print(f"❌ OLTP falhou: {e}")

# Teste 2: Conexão OLAP (read-only)
try:
    conn_olap = psycopg2.connect(settings.olap_url)
    cur = conn_olap.cursor()
    cur.execute("SELECT COUNT(*) FROM analytics_donabedian.fato_medicoes")
    count = cur.fetchone()[0]
    print(f"✅ OLAP conectado: {count} medições")
    conn_olap.close()
except Exception as e:
    print(f"❌ OLAP falhou: {e}")

# Teste 3: Validar read-only OLAP
try:
    conn_olap = psycopg2.connect(settings.olap_url)
    cur = conn_olap.cursor()
    cur.execute("INSERT INTO analytics_donabedian.fato_medicoes (indicador_hash) VALUES ('test')")
    print("❌ OLAP permite escrita (ERRO!)")
except Exception as e:
    print(f"✅ OLAP bloqueou escrita: {e}")
```

**Checklist**:
- [ ] Conexão OLTP validada (read/write)
- [ ] Conexão OLAP validada (read-only)
- [ ] Bloqueio de escrita OLAP validado
- [ ] Contagem de registros conferida

---

### 🗓️ DIA 5 - Quarta, 26/02 (2h)

#### 09:00-10:00 | Documentação Final (1h)
**Objetivo**: Documentar toda a infraestrutura

**Tarefas**:
- Criar diagrama de arquitetura
- Documentar schemas e tabelas
- Documentar processo de migração
- Criar guia de troubleshooting

**Checklist**:
- [ ] Diagrama de arquitetura criado
- [ ] Documentação de schemas completa
- [ ] Processo de migração documentado
- [ ] Guia de troubleshooting criado

---

#### 10:00-11:00 | Validação Final e Entrega (1h)
**Objetivo**: Validar entregáveis da semana

**Checklist Final**:
- [ ] PostgreSQL OLTP funcionando
- [ ] PostgreSQL OLAP funcionando
- [ ] 2 schemas OLTP criados (donabedian, wanda)
- [ ] 2 schemas OLAP criados (analytics_*)
- [ ] Dados históricos migrados
- [ ] Conexões configuradas nos módulos
- [ ] Conectividade validada
- [ ] Documentação completa

---

## 📊 ENTREGÁVEIS DA SEMANA 1

1. ✅ Database `intellicare_oltp` configurado
2. ✅ Database `intellicare_olap` configurado
3. ✅ 6 tabelas OLTP criadas (3 donabedian + 3 wanda)
4. ✅ 2 tabelas OLAP criadas (fato_medicoes + fato_ocupacoes)
5. ✅ Dados históricos migrados (12 meses donabedian + 6 meses wanda)
6. ✅ Conexões configuradas nos 2 módulos
7. ✅ Testes de conectividade passando
8. ✅ Documentação completa

---

**Período**: 20-26/02/2026  
**Esforço**: 16 horas  
**Status**: 🚀 **EM EXECUÇÃO**

---

🚀 **SEMANA 1 INICIADA - VAMOS CONSTRUIR A INFRAESTRUTURA!**

