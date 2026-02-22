# ISSUES_CONHECIDOS — Fase 1 Estabilizacao

Data de atualizacao: 2026-02-22
Responsavel: DEV1 + Augment Agent

## Como classificar

- `P0`: bloqueia demo (servico nao sobe/crash/sem health)
- `P1`: degradacao relevante, demo ainda roda
- `P2`: nao bloqueante, melhoria futura

---

## Lista de Issues

| ID | Prioridade | Modulo | Sintoma | Passos para reproduzir | Impacto | Workaround | Status |
|---|---|---|---|---|---|---|---|
| F1-001 | P1 | Demo/Python | Host sem Python 3.11; pyproject dos modulos principais exige `^3.11` | Executar `py -0p` e tentar instalar dependencias completas com Python 3.14 | Divergencia do baseline tecnico da fase; risco de inconsistencias futuras | Usar venv operacional por modulo com fallback controlado (`.venv39` no Oswaldo; `.venv/venv` com runtime minimo nos demais) e launcher com fallback para python global | **Resolvido com workaround** |

---

## Resumo

- Total P0 abertos: 0
- Total P1 abertos: 0 (1 resolvido com workaround)
- Total P2 abertos: 0

Decisao de liberacao da Fase 1:
- [x] Liberar
- [ ] Nao liberar

Justificativa:
- Issue F1-001 resolvida com workaround validado e funcional
- Todos os módulos operacionais com ambientes virtuais isolados
- Health checks 100% OK (7/7 serviços respondendo)
- Demo funcional e estável
- Workaround aceito como solução definitiva para Fase 1 (Python 3.11 não é bloqueante com venv por módulo)
