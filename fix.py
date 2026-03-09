import os
import glob
import re

# 1. Fix comunicacao/storage/repository.py
repo_path = r'C:\Users\egara\INTELLICARE\intellicare-comunicacao\comunicacao\storage\repository.py'
if os.path.exists(repo_path):
    with open(repo_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove import
    content = re.sub(r'from comunicacao\.storage\.tenant_utils import get_tenant_conn\n', '', content)
    
    # Add context manager definition if not already there
    if 'def get_tenant_conn' not in content:
        tenant_conn_code = """
from contextlib import contextmanager
from typing import Any

@contextmanager
def get_tenant_conn(engine, ctx: Any = None):
    schema = ctx.schema_name if ctx and hasattr(ctx, "schema_name") else "public"
    with engine.begin() as conn:
        if "postgresql" in str(engine.url):
            from sqlalchemy import text
            conn.execute(text(f"SET search_path TO {schema}"))
        yield conn
"""
        # Insert after imports
        content = content.replace('from typing import AsyncGenerator, Protocol\n', 'from typing import AsyncGenerator, Protocol\n' + tenant_conn_code)
        
    with open(repo_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed comunicacao repository.py')

# 2. Fix all Dockerfiles
for df in glob.glob(r'C:\Users\egara\INTELLICARE\intellicare-*\Dockerfile'):
    with open(df, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Replace -e
    new_content = re.sub(r'pip install([^A-Za-z0-9]+)-e /tmp/intellicare-core', r'pip install\1/tmp/intellicare-core', content)
    new_content = re.sub(r'pip install([^A-Za-z0-9]+)-e /tmp/intellicare-auth', r'pip install\1/tmp/intellicare-auth', new_content)
    
    if new_content != content:
        with open(df, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Fixed {os.path.basename(os.path.dirname(df))}/Dockerfile')
