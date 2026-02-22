# ============================================================================
# Script de Execução Automatizada - Projeto 02
# Executa setup completo de OLTP e OLAP
# ============================================================================

param(
    [string]$PostgresPassword = "postgres",
    [string]$PostgresHost = "localhost",
    [int]$PostgresPort = 5432
)

# Cores para output
function Write-Success { Write-Host "✅ $args" -ForegroundColor Green }
function Write-Error-Custom { Write-Host "❌ $args" -ForegroundColor Red }
function Write-Info { Write-Host "ℹ️  $args" -ForegroundColor Cyan }
function Write-Warning-Custom { Write-Host "⚠️  $args" -ForegroundColor Yellow }

# Banner
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  PROJETO 02 - SETUP OLTP/OLAP" -ForegroundColor Cyan
Write-Host "  Separação Operacional/Analítico" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se psql está disponível
Write-Info "Verificando PostgreSQL..."
try {
    $version = psql --version
    Write-Success "PostgreSQL encontrado: $version"
} catch {
    Write-Error-Custom "PostgreSQL não encontrado no PATH!"
    Write-Warning-Custom "Por favor, instale o PostgreSQL ou adicione ao PATH"
    Write-Info "Consulte: 00_GUIA_INSTALACAO.md"
    exit 1
}

# Testar conexão
Write-Info "Testando conexão com PostgreSQL..."
$env:PGPASSWORD = $PostgresPassword
try {
    $result = psql -h $PostgresHost -p $PostgresPort -U postgres -c "SELECT version();" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Conexão estabelecida com sucesso"
    } else {
        throw "Falha na conexão"
    }
} catch {
    Write-Error-Custom "Não foi possível conectar ao PostgreSQL"
    Write-Warning-Custom "Verifique se o serviço está rodando"
    exit 1
}

# Menu de opções
Write-Host ""
Write-Host "Escolha uma opção:" -ForegroundColor Yellow
Write-Host "1. Setup completo (OLTP + OLAP + Migração)"
Write-Host "2. Apenas OLTP (Dia 1)"
Write-Host "3. Apenas OLAP (Dia 2)"
Write-Host "4. Apenas Migração (Dia 3)"
Write-Host "5. Apenas Testes"
Write-Host "6. Limpar tudo (DROP databases)"
Write-Host ""
$opcao = Read-Host "Digite a opção (1-6)"

switch ($opcao) {
    "1" {
        Write-Info "Executando setup completo..."
        
        # OLTP
        Write-Host ""
        Write-Host "=" * 60 -ForegroundColor Cyan
        Write-Host "PASSO 1: Setup OLTP" -ForegroundColor Cyan
        Write-Host "=" * 60 -ForegroundColor Cyan
        psql -h $PostgresHost -p $PostgresPort -U postgres -f "01_setup_oltp.sql"
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Setup OLTP concluído"
        } else {
            Write-Error-Custom "Erro no setup OLTP"
            exit 1
        }
        
        # OLAP
        Write-Host ""
        Write-Host "=" * 60 -ForegroundColor Cyan
        Write-Host "PASSO 2: Setup OLAP" -ForegroundColor Cyan
        Write-Host "=" * 60 -ForegroundColor Cyan
        psql -h $PostgresHost -p $PostgresPort -U postgres -f "02_setup_olap.sql"
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Setup OLAP concluído"
        } else {
            Write-Error-Custom "Erro no setup OLAP"
            exit 1
        }
        
        # Migração
        Write-Host ""
        Write-Host "=" * 60 -ForegroundColor Cyan
        Write-Host "PASSO 3: Migração de Dados" -ForegroundColor Cyan
        Write-Host "=" * 60 -ForegroundColor Cyan
        python 03_migrate_data.py
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Migração concluída"
        } else {
            Write-Error-Custom "Erro na migração"
            exit 1
        }
        
        # Testes
        Write-Host ""
        Write-Host "=" * 60 -ForegroundColor Cyan
        Write-Host "PASSO 4: Testes de Conexão" -ForegroundColor Cyan
        Write-Host "=" * 60 -ForegroundColor Cyan
        python 04_test_connections.py
        
        Write-Host ""
        Write-Host "=" * 60 -ForegroundColor Cyan
        Write-Host "PASSO 5: Validação de Dados" -ForegroundColor Cyan
        Write-Host "=" * 60 -ForegroundColor Cyan
        python 05_validate_data.py
        
        Write-Host ""
        Write-Success "Setup completo finalizado!"
    }
    
    "2" {
        Write-Info "Executando setup OLTP..."
        psql -h $PostgresHost -p $PostgresPort -U postgres -f "01_setup_oltp.sql"
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Setup OLTP concluído"
        }
    }
    
    "3" {
        Write-Info "Executando setup OLAP..."
        psql -h $PostgresHost -p $PostgresPort -U postgres -f "02_setup_olap.sql"
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Setup OLAP concluído"
        }
    }
    
    "4" {
        Write-Info "Executando migração..."
        python 03_migrate_data.py
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Migração concluída"
        }
    }
    
    "5" {
        Write-Info "Executando testes..."
        python 04_test_connections.py
        python 05_validate_data.py
    }
    
    "6" {
        Write-Warning-Custom "ATENÇÃO: Isso irá remover TODOS os dados!"
        $confirm = Read-Host "Digite 'SIM' para confirmar"
        if ($confirm -eq "SIM") {
            Write-Info "Removendo databases..."
            psql -h $PostgresHost -p $PostgresPort -U postgres -c "DROP DATABASE IF EXISTS intellicare_oltp;"
            psql -h $PostgresHost -p $PostgresPort -U postgres -c "DROP DATABASE IF EXISTS intellicare_olap;"
            psql -h $PostgresHost -p $PostgresPort -U postgres -c "DROP USER IF EXISTS intellicare_app;"
            psql -h $PostgresHost -p $PostgresPort -U postgres -c "DROP USER IF EXISTS intellicare_analytics;"
            Write-Success "Limpeza concluída"
        } else {
            Write-Info "Operação cancelada"
        }
    }
    
    default {
        Write-Error-Custom "Opção inválida"
        exit 1
    }
}

# Resumo final
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "RESUMO" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

# Listar databases
Write-Info "Databases criados:"
psql -h $PostgresHost -p $PostgresPort -U postgres -c "\l" | Select-String "intellicare"

Write-Host ""
Write-Success "Execução finalizada!"
Write-Host ""

