#!/bin/bash
# Script para criar schemas no PostgreSQL

echo "Criando schemas no PostgreSQL..."

docker exec -i intellicare-postgres psql -U intellicare_admin -d intellicare_db <<EOF
CREATE SCHEMA IF NOT EXISTS intellicare_florence;
CREATE SCHEMA IF NOT EXISTS intellicare_oswaldo;
CREATE SCHEMA IF NOT EXISTS intellicare_donabedian;
CREATE SCHEMA IF NOT EXISTS intellicare_wanda;
CREATE SCHEMA IF NOT EXISTS intellicare_comunicacao;
CREATE SCHEMA IF NOT EXISTS intellicare_geralda;
\dn
EOF

echo "✅ Schemas criados com sucesso!"

