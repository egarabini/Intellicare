---
tipo: product-sense
atualizado: 2026-03-13
---

# Para quem construímos

## O usuário primário: o profissional de saúde

Tempo médio de consulta: 12-15 minutos.
Janela de atenção para o sistema: **menos de 30 segundos**.

O sistema deve ser **invisível quando funciona**.
O sistema deve ser **imediato quando consultado**.
O sistema deve ser **preciso quando responde**.

---

## Personas

**Médico de família (UBS)**
Alta demanda, poucos recursos, contexto de atenção primária.
Precisa de protocolos rápidos e referências confiáveis do Ministério da Saúde.
Não tem tempo para navegar em 5 telas para encontrar uma informação.

**Enfermeiro da UBS**
Executa protocolos, registra dados, faz triagem.
Usa o sistema com frequência e ritmo acelerado.
Interface deve ser previsível e de baixo atrito.

**Gestor da UBS**
Precisa de números, não de narrativas.
Dashboard limpo, alertas claros, exportações sem complicação.
Não é técnico — não deve precisar ser.

**Administrador da plataforma (IntelliCare)**
Técnico, confia em logs e métricas.
Não precisa de interface bonita — precisa de interface eficaz.
Provisiona tenants, monitora billing, acompanha uso.

---

## Proposta de valor

> "A informação clínica certa, na hora certa, sem sair do fluxo de trabalho."

Para o profissional: menos tempo buscando protocolo, mais tempo com o paciente.
Para o gestor: visão clara da equipe e da unidade, sem planilhas manuais.
Para a secretaria: indicadores de saúde populacionais sem esforço de coleta.

---

## O que nunca fazemos

- Não adicionamos funcionalidade sem usuário e caso de uso confirmados
- Não priorizamos estética sobre velocidade em contexto clínico
- Não exigimos treinamento para tarefas básicas
- Não criamos fluxos com mais de 3 cliques para ações frequentes
- Não ignoramos acessibilidade (profissionais de saúde usam monitores variados, iluminação adversa)

---

## Métricas de produto que importam

| Métrica | Alvo |
|---------|------|
| Tempo de resposta clínica (RAG) | < 300ms |
| Tempo de consulta de protocolo (UX) | < 30s do início ao fim |
| Taxa de adoção por profissional | > 80% de sessões com consulta ao sistema |
| NPS de profissionais de saúde | > 40 |
| Tempo de provisionamento de tenant | < 5 minutos |
