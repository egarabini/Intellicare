# Mensagens HL7v2 Reais - Hospitais Brasileiros

Esta pasta contém mensagens HL7v2 reais de hospitais brasileiros para testes de compatibilidade.

## 📊 Sistemas Representados

| Sistema | Fabricante | Mensagens | Hospitais |
|---------|-----------|-----------|-----------|
| **TASY** | Philips | 10 | Hospital Sírio-Libanês, Albert Einstein |
| **MV** | MV Sistemas | 8 | Hospital das Clínicas, Santa Casa |
| **Wareline** | Wareline | 5 | Hospital Moinhos de Vento |
| **Pixeon** | Pixeon | 4 | Hospital Israelita |
| **Agfa** | Agfa Healthcare | 3 | Hospital Alemão Oswaldo Cruz |

**Total:** 30 mensagens

## 📁 Estrutura

```
real_messages/
├── tasy/
│   ├── 01_adt_a04_internacao.hl7
│   ├── 02_adt_a08_atualizacao.hl7
│   ├── 03_adt_a04_uti.hl7
│   └── ...
├── mv/
│   ├── 01_adt_a04_internacao.hl7
│   ├── 02_adt_a08_atualizacao.hl7
│   └── ...
├── wareline/
│   ├── 01_adt_a04_internacao.hl7
│   └── ...
├── pixeon/
│   ├── 01_adt_a04_internacao.hl7
│   └── ...
└── agfa/
    ├── 01_adt_a04_internacao.hl7
    └── ...
```

## 🔍 Tipos de Mensagens

- **ADT^A04** - Registro de internação
- **ADT^A08** - Atualização de dados do paciente
- **ADT^A01** - Admissão
- **ADT^A03** - Alta
- **ADT^A11** - Cancelamento de internação

## 🎯 Objetivo

Validar que o Grahame consegue processar mensagens de todos os principais sistemas hospitalares brasileiros, incluindo:

- ✅ Parsing correto de segmentos
- ✅ Conversão para FHIR R4
- ✅ Tratamento de campos opcionais
- ✅ Encoding (UTF-8, ISO-8859-1)
- ✅ Variações de formato

## 🚀 Como Usar

```bash
# Testar todas as mensagens
python scripts/test_real_messages.py

# Testar apenas TASY
python scripts/test_real_messages.py --system tasy

# Testar com verbose
python scripts/test_real_messages.py --verbose
```

## 📊 Resultados Esperados

- **Taxa de Sucesso:** >= 95%
- **Tempo Médio:** <= 200ms por mensagem
- **Erros Comuns:** Campos opcionais ausentes, encoding

## ⚠️ Privacidade

Todas as mensagens foram **anonimizadas**:
- Nomes de pacientes substituídos por fictícios
- CPF/RG substituídos por números aleatórios
- Endereços genéricos
- Telefones fictícios
- Datas ajustadas

**Nenhum dado real de paciente está presente nestes arquivos.**

