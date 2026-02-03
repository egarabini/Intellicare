# 📚 Documentação - IntelliCare

Esta pasta contém toda a **documentação técnica e funcional** dos módulos do projeto IntelliCare.

---

## 📋 Propósito

Centralizar todas as especificações, documentos técnicos e funcionais de cada módulo desenvolvido no projeto IntelliCare, seguindo um padrão de versionamento e nomenclatura consistente.

---

## 🗂️ Estrutura de Organização

### Padrão de Nomenclatura

Todos os documentos seguem o padrão:

```
V{versão}-{AAAAMMDDHHNN}-{tipo}-{NomeModulo}.md
```

**Onde:**
- `V{versão}`: Versão do documento (ex: V1.0, V1.1, V1.2)
- `{AAAAMMDDHHNN}`: Data e hora de criação (ex: 202502031800)
- `{tipo}`: Tipo do documento
  - `SDP`: Solicitação de Desenvolvimento de Produto
  - `EF`: Especificação Funcional
  - `ET`: Especificação Técnica
  - `RESUMO`: Resumo Executivo
- `{NomeModulo}`: Nome do módulo (PascalCase)

**Exemplo:**
```
V1.2-202502031800-EF-EmailManagementSystem.md
```

---

## 📑 Tipos de Documentos

### 1. SDP - Solicitação de Desenvolvimento de Produto
**Propósito:** Documento inicial que descreve a necessidade de negócio e requisitos de alto nível.

**Conteúdo:**
- Contexto e justificativa
- Objetivos do produto
- Stakeholders
- Requisitos de alto nível
- Restrições e premissas

---

### 2. EF - Especificação Funcional
**Propósito:** Detalha COMO o sistema deve funcionar do ponto de vista do usuário.

**Conteúdo:**
- Visão geral
- Requisitos funcionais (RF)
- Requisitos não funcionais (RNF)
- Casos de uso
- Regras de negócio
- Fluxos de trabalho
- Arquitetura de alto nível
- Cronograma
- Métricas de sucesso

---

### 3. ET - Especificação Técnica
**Propósito:** Detalha COMO implementar o sistema tecnicamente.

**Conteúdo:**
- Stack tecnológica
- Estrutura de diretórios
- Modelos de dados
- APIs e endpoints
- Configurações
- Código de implementação
- Docker/Deploy
- Testes
- Troubleshooting
- Exemplos de uso

---

### 4. RESUMO - Resumo Executivo
**Propósito:** Visão condensada para apresentação rápida.

**Conteúdo:**
- Visão geral (1 parágrafo)
- Principais recursos
- Stack tecnológica (tabela)
- Quick start
- Exemplo de uso
- Métricas
- Próximos passos

---

## 📂 Organização por Módulo

Cada módulo possui seus próprios documentos versionados:

```
desenvolvimento/docs/
├── README.md (este arquivo)
│
├── PortalIntellicare/
│   ├── V1.0-202502011500-EF-PortalIntellicare.md
│   ├── V1.0-202502011530-ET-PortalIntellicare.md
│   └── V1.1-202502020900-EF-PortalIntellicare.md
│
├── BrazilianHealthDataAgent/
│   ├── V1.0-202502021900-EF-BrazilianHealthDataAgent.md
│   ├── V1.0-202502021900-ET-BrazilianHealthDataAgent.md
│   ├── V1.0-202502021900-RESUMO-BrazilianHealthDataAgent.md
│   ├── V1.1-202502022100-EF-BrazilianHealthDataAgent.md (correções)
│   └── API-VALIDATION-CHECKLIST.md
│
├── EmailManagementSystem/
│   ├── V1.2-202502031800-EF-EmailManagementSystem.md
│   ├── V1.2-202502031800-ET-EmailManagementSystem.md
│   └── V1.2-202502031800-RESUMO-EmailManagementSystem.md
│
└── [NovosModulos]/
    └── ...
```

---

## 🔄 Versionamento

### Quando criar nova versão?

- **Patch (1.0 → 1.1)**: Correções, ajustes menores, clarificações
- **Minor (1.2 → 1.3)**: Novos recursos, melhorias significativas
- **Major (1.x → 2.0)**: Mudanças arquiteturais, breaking changes

### Histórico de Versões

Cada documento deve ter seção de changelog no final:

```markdown
## Changelog

### V1.2 - 2025-02-03 18:00
- Adicionado suporte a SendGrid
- Melhorias na documentação de deployment

### V1.1 - 2025-02-03 15:00
- Correções de nomenclatura (HERMES → WANDA)
- Ajustes de cache TTL

### V1.0 - 2025-02-02 19:00
- Versão inicial
```

---

## 📖 Como Usar Esta Documentação

### Para Desenvolvedores:
1. Leia o **RESUMO** para visão geral
2. Leia a **EF** para entender requisitos
3. Leia a **ET** para implementar
4. Consulte **steps/** para acompanhar progresso

### Para Gestores:
1. Leia o **RESUMO** para decisões rápidas
2. Consulte **EF** para validar requisitos
3. Verifique **steps/** para status do projeto

### Para Novos Membros:
1. Comece pelo **README.md** de cada módulo
2. Leia **RESUMO** de todos os módulos
3. Aprofunde na **EF** e **ET** conforme necessário

---

## ✅ Checklist de Qualidade

Antes de finalizar um documento, verificar:

- [ ] Nome segue padrão de nomenclatura
- [ ] Versão está correta
- [ ] Data/hora de criação está presente
- [ ] Seções obrigatórias estão completas
- [ ] Código (se ET) está testado
- [ ] Exemplos funcionam
- [ ] Changelog atualizado
- [ ] Links internos funcionam
- [ ] Imagens/diagramas estão claros

---

## 🔗 Documentos Relacionados

- **Steps**: `../steps/README.md` - Acompanhamento de desenvolvimento
- **Código**: `../../[modulo]/` - Implementação real
- **Testes**: `../../[modulo]/tests/` - Testes automatizados

---

**Última atualização:** 2025-02-03  
**Responsável:** Equipe IntelliCare

