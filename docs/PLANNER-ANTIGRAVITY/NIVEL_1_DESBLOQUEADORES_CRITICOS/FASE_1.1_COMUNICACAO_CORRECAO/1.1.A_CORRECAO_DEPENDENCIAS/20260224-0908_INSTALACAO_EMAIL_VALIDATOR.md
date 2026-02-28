# Instalação do email-validator - 2026-02-24 09:08

## Problema Identificado

O `email-validator` está no `pyproject.toml` mas **NÃO está instalado** no venv.

## Ação Executada

```bash
cd intellicare-comunicacao
.venv/Scripts/pip install email-validator>=2.1.0
```

## Resultado

✅ **SUCESSO!**

```
Collecting email-validator>=2.1.0
  Using cached email_validator-2.3.0-py3-none-any.whl.metadata (26 kB)
Collecting dnspython>=2.0.0 (from email-validator>=2.1.0)
  Using cached dnspython-2.8.0-py3-none.any.wh.metadata (5.7 kB)
...
Installing collected packages: dnspython, email-validator

Successfully installed dnspython-2.8.0 email-validator-2.3.0
```

**Versão instalada:** email-validator 2.3.0

## Próximo Passo

Executar `pytest --co -q` para verificar se os erros de coleta foram resolvidos.
