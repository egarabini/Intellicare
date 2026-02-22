#!/usr/bin/env python3
"""Create intellicareDB database if not exists."""

import psycopg2
from psycopg2 import sql

try:
    # Connect to server (without specifying database)
    conn = psycopg2.connect(
        host='161.97.141.186',
        port='5432',
        user='admin_intellicare',
        password='Crazy#57LB',
        database='postgres'
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Create database if not exists
    try:
        cursor.execute('CREATE DATABASE "intellicareDB" OWNER admin_intellicare;')
        print('✓ Database intellicareDB criado com sucesso')
    except psycopg2.errors.DuplicateDatabase:
        print('✓ Database intellicareDB já existe')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'✗ Erro: {e}')
