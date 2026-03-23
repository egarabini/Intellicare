---
tipo: especificacao-funcional
demanda: DEM-072
titulo: Receituário Digital
sprint: 2026-04-25
status: em-execucao
dev: DEV-1
criado: 2026-03-21
depende_de: [DEM-058, DEM-061]
habilita: [DEM-074]
tags: [oswaldo, receituario, pdf, cfm, anvisa, prescricao, weasyprint]
---

# DEM-072 — Receituário Digital

## Objetivo

Hoje o Oswaldo gera prescrições como lista de itens dentro do PDF clínico do encontro. Isso **não é um receituário médico** — não tem CRM do profissional em destaque, não tem símbolo ℞, não tem formato legal CFM/ANVISA. Um receituário digital independente é um documento autônomo que o médico pode imprimir, assinar e entregar ao paciente, ou enviar eletronicamente. Esta DEM implementa o receituário seguindo o padrão brasileiro obrigatório.

---

## Padrão CFM/ANVISA — layout obrigatório

### Cabeçalho — Identificação do Profissional
- Nome do profissional (ex: `Dr. João Silva`)
- CRM + UF (ex: `CRM 12345/SP`)
- Especialidade
- Endereço e telefone do consultório/clínica

### Corpo — Identificação do Paciente
- Nome completo
- Idade
- Data de emissão

### Símbolo de Receita
- ℞ (ou "R" estilizado) — abre a seção de medicamentos

### Lista de Medicamentos
Para cada item:
1. Nome genérico (DCB — Denominação Comum Brasileira, obrigatório por lei)
2. Concentração
3. Forma farmacêutica (comprimido, cápsula, solução oral, creme...)
4. Quantidade total
5. Posologia no formato formal: `"Tomar 1 (um) comprimido via oral a cada 8 horas por 5 (cinco) dias"`

### Rodapé
- Local e data por extenso (ex: `São Paulo, 21 de março de 2026`)
- Campo de assinatura
- Campo de carimbo (nome + CRM)

### Tipos de receituário
- `simple` — receita comum (tarja vermelha/sem tarja)
- `special_control` — receita de controle especial (tarja preta, exige campos adicionais: CPF do paciente, validade da receita)

---

## Estado Atual vs. Estado Desejado

| Aspecto | Hoje | Após DEM-072 |
|---------|------|--------------|
| Prescrição | Lista de itens dentro do PDF do encontro | Receituário autônomo no formato CFM/ANVISA |
| CRM do médico | Não aparece no documento | Destaque no cabeçalho |
| Símbolo ℞ | Ausente | Presente conforme norma |
| Posologia | Texto livre | Formato formal validado |
| Tipo de receita | Único | `simple` ou `special_control` |
| Botão de acesso | Nenhum dedicado | "Imprimir Receituário" no Oswaldo |
| Arquivo gerado | Embutido no PDF do encontro | PDF autônomo por prescrição |

---

## Critérios de aceite

1. `GET /oswaldo/prescriptions/{id}/receituario.pdf` retorna PDF com layout CFM/ANVISA completo
2. Cabeçalho exibe nome do profissional, CRM/UF, especialidade e contato
3. Cada medicamento usa nome genérico (DCB) com posologia no formato formal
4. Receituário tipo `special_control` exibe CPF do paciente e campo de validade
5. Botão "Imprimir Receituário" no `OswaldoPrescriptionEditor` funciona
6. Mínimo 3 testes automatizados passando

---

## Fora de escopo

- Assinatura digital ICP-Brasil (exige certificado A3 — fase futura)
- Envio direto ao paciente por WhatsApp/e-mail (integrar com CarePlanner em sprint futura)
- QR Code de autenticidade (fase futura, após infraestrutura de validação)
