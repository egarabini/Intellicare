-- Cria banco 'listmonk' se não existir (idempotente)
SELECT 'CREATE DATABASE listmonk'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'listmonk'
)\gexec
