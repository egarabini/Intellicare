# Inicialização do Servidor

Configuração inicial do servidor de homologação, executada uma única vez.

---

## Fases

| Fase | Pasta | Descrição |
|------|-------|-----------|
| 1 | `Fase1_Preparacao_Sistema/` | Atualização do SO, Docker, Docker Compose, ferramentas |
| 2 | `Fase2_Clone_Configuracao/` | Clone do repositório, `.env`, estrutura de diretórios |
| 3 | `Fase3_Infraestrutura/` | Postgres, Redis, schemas, firewall |
| 4 | `Fase4_Seguranca/` | SSH com chave, Fail2Ban, senhas, hardening |

---

## Ordem de execução

```
Fase1 → Fase2 → Fase3 → Fase4
```

---

## Plano de Implementação (DEV)

O plano está na pasta **Fase1_Preparacao_Sistema** (implantação do servidor):

- [Fase1_Preparacao_Sistema/20260221-1000_PLANO_IMPLEMENTACAO_CONFIGURACAO_SERVIDOR.md](Fase1_Preparacao_Sistema/20260221-1000_PLANO_IMPLEMENTACAO_CONFIGURACAO_SERVIDOR.md)

---

## Documentação por fase

Cada pasta de fase deve conter:
- `README.md` — descrição e checklist
- `YYYYMMDD-HHMM_*.md` — relatórios de execução (seguindo NORMAS_E_PADROES)
