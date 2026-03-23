---
tipo: especificacao-funcional
demanda: DEM-080
titulo: Assinatura Digital Receituário
sprint: 2026-05-09
status: em-execucao
dev: DEV-1
criado: 2026-03-22
depende_de: [DEM-072]
tags: [receituario, assinatura-digital, icp-brasil, a1, pkcs12]
---

# DEM-080 — Assinatura Digital Receituário

## Objetivo

Habilitar a assinatura digital do receituário PDF com certificado ICP-Brasil tipo A1 (software — arquivo `.pfx`). O médico faz upload do seu certificado A1 uma única vez; a partir daí, todo receituário gerado é assinado digitalmente, tornando o documento juridicamente válido conforme Resolução CFM 2.299/2021.

---

## Personas

**Clínico:** faz upload do seu certificado `.pfx` (A1) e senha em "Meu Perfil" no ClinicoUI. A partir daí, ao gerar um receituário, o PDF é automaticamente assinado. O clínico vê uma indicação visual "✓ Assinado digitalmente" no PDF.

**Paciente:** ao abrir o receituário no portal, o PDF já contém a assinatura digital visível e verificável por qualquer leitor de PDF (Adobe, navegador).

**Gestor de Plataforma:** sem ação necessária — a infraestrutura de assinatura é por profissional, não por plataforma.

---

## Fluxo

```
1. Clínico → ClinicoUI → "Meu Perfil" → upload .pfx + senha
2. API → criptografa senha com chave do servidor → armazena metadados em professional_certificates
3. Clínico → gera receituário (fluxo existente DEM-072)
4. API → generate_receituario() → sign_pdf() se certificado disponível → PDF assinado
5. PDF retornado com assinatura digital embutida
```

---

## Critérios de aceite

1. Upload de `.pfx` funciona — certificado armazenado com senha criptografada
2. Receituário gerado por médico com certificado cadastrado tem assinatura digital válida
3. Receituário gerado por médico sem certificado funciona normalmente (sem assinatura, sem erro)
4. PDF assinado abre sem erros de validação no Adobe Reader e Chrome PDF viewer
5. `DELETE /professionals/me/certificate` remove o certificado e retorna ao fluxo sem assinatura
6. 4+ testes automatizados cobrindo: upload, geração com assinatura, geração sem certificado, remoção

---

## Fora de escopo

- Certificado A3 (hardware — token USB) — requer integração com drivers do SO, fora de escopo
- Certificado de plataforma compartilhado — cada médico assina com o próprio certificado
- Validação online OCSP/CRL em tempo real — verificação offline suficiente para v1
- Timestamp authority (carimbo do tempo) — pode ser adicionado em sprint futuro
