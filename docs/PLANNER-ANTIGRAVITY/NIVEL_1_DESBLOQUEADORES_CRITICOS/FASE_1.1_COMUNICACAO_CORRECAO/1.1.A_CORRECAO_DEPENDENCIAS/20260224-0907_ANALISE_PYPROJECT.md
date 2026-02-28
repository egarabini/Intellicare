# Análise do pyproject.toml - 2026-02-24 09:07

## Descoberta

O `email-validator = "^2.0.0"` **JÁ ESTÁ PRESENTE** no `pyproject.toml` (linha 27).

## Possíveis Causas do Erro

1. O venv não foi atualizado após a adição da dependência
2. O pacote não foi instalado corretamente
3. Versão incorreta do Poetry ou pip

## Próximos Passos

1. Verificar se o pacote está instalado no venv
2. Se não estiver, reinstalar as dependências
3. Executar `pytest --co -q` para ver os erros atuais
