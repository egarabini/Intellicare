# ROTEIRO DE SIMULAÇÃO - VALIDAÇÃO LGPD

## 🎭 Simulação de Reunião de Validação

**Data da Simulação**: 25/02/2026 - 14:00-15:00  
**Data da Validação Real**: 26/02/2026 - 10:00-12:00  
**Responsável**: DEV1  
**Versão**: 1.0

---

## 🎯 OBJETIVO DA SIMULAÇÃO

Praticar a condução da validação LGPD para:
- ✅ Testar o fluxo da reunião
- ✅ Identificar pontos de melhoria
- ✅ Ajustar timing da agenda
- ✅ Verificar materiais e ambiente
- ✅ Ganhar confiança na apresentação

---

## 👥 PARTICIPANTES DA SIMULAÇÃO

### Facilitador (DEV1):
- Conduz a reunião
- Apresenta o conteúdo
- Gerencia o tempo

### Especialista Simulado (DEV2):
- Faz papel da Dra. Maria Santos
- Faz perguntas desafiadoras
- Avalia a apresentação

---

## ⏱️ ROTEIRO CRONOMETRADO

### [00:00 - 00:05] Abertura e Contexto (5 min)

**DEV1 diz**:
> "Bom dia, Dra. Maria! Muito obrigado por participar desta validação. Seu tempo é muito valioso para nós."

> "Hoje vamos validar a conformidade LGPD do nosso processo de anonimização de dados no pipeline ETL do projeto INTELLICARE."

> "A agenda é: 5 min de contexto, 30 min de demonstração, 45 min de testes práticos, 30 min de discussão e 10 min de próximos passos."

> "Vou compartilhar minha tela. [Compartilhar tela com diagrama]"

> "O INTELLICARE é um sistema de gestão de qualidade em saúde. Implementamos separação de dados operacionais e analíticos usando CQRS. Os dados analíticos precisam estar anonimizados para conformidade LGPD."

**DEV2 (como especialista) pergunta**:
> "Qual o volume de dados pessoais que vocês processam?"

**DEV1 responde**:
> "Atualmente processamos dados de [X] pacientes e [Y] leitos. Todos os dados pessoais ficam apenas no banco operacional. O banco analítico recebe apenas dados anonimizados."

**✅ Checkpoint**: Tempo OK? Contexto claro?

---

### [00:05 - 00:35] Demonstração do Sistema (30 min)

#### [00:05 - 00:10] Arquitetura CQRS (5 min)

**DEV1 apresenta**:
> "Vou mostrar nossa arquitetura. [Mostrar diagrama]"

> "Temos dois bancos PostgreSQL separados:"
> - "OLTP (Operacional): Recebe dados em tempo real, com PII"
> - "OLAP (Analítico): Recebe dados anonimizados, sem PII"

> "A separação garante que análises nunca acessam dados pessoais."

**DEV2 pergunta**:
> "Como vocês garantem que não há vazamento de PII entre os bancos?"

**DEV1 responde**:
> "Três camadas de proteção: 1) Anonimização irreversível no ETL, 2) Usuários diferentes com permissões diferentes, 3) Auditoria de todos os acessos."

---

#### [00:10 - 00:20] Pipeline ETL (10 min)

**DEV1 demonstra**:
> "Vou mostrar o código do pipeline ETL. [Abrir script]"

> "O processo tem 3 etapas:"
> 1. "Extração: Lemos dados do OLTP"
> 2. "Transformação: Aplicamos anonimização SHA-256"
> 3. "Carga: Inserimos no OLAP"

> "Veja este exemplo: [Mostrar código de anonimização]"

```python
# Exemplo real do código
leito_id_anonimizado = hashlib.sha256(
    f"{leito_id}{SALT}".encode()
).hexdigest()
```

**DEV2 pergunta**:
> "O salt é único por instalação? Como é gerenciado?"

**DEV1 responde**:
> "Sim, cada instalação tem um salt único gerado na configuração inicial. É armazenado em variável de ambiente, nunca no código."

---

#### [00:20 - 00:35] Processo de Anonimização (15 min)

**DEV1 explica**:
> "Vou mostrar exemplos práticos de anonimização. [Mostrar tabela]"

**Antes (OLTP)**:
```
leito_id: "L-101"
paciente_id: "12345678900"
data_entrada: "2026-02-15 14:30:00"
```

**Depois (OLAP)**:
```
leito_id_hash: "a3f5b8c9d2e1..."
paciente_id_hash: "7e4d3c2b1a0f..."
periodo: "2026-Q1"
categoria_permanencia: "media"
```

**DEV1 destaca**:
> "Note que:"
> - "IDs são hashes irreversíveis"
> - "Data exata vira trimestre"
> - "Tempo de permanência vira categoria"

**DEV2 pergunta**:
> "E se precisarmos correlacionar com dados operacionais?"

**DEV1 responde**:
> "Não é possível e é intencional. O OLAP é para análises agregadas, não para rastreamento individual. Isso garante privacidade."

**✅ Checkpoint**: Demonstração clara? Perguntas respondidas?

---

### [00:35 - 01:20] Testes Práticos (45 min)

**DEV1 introduz**:
> "Agora vamos executar os 5 testes de conformidade LGPD. Preparei um script automatizado."

#### [00:35 - 00:45] Teste 1: Irreversibilidade (10 min)

**DEV1 executa**:
```bash
python 11_validate_lgpd.py --test irreversibilidade
```

**DEV1 explica**:
> "Este teste tenta reverter o hash SHA-256. Veja o resultado: [Mostrar output]"
> "Impossível recuperar o dado original. ✅ PASSOU"

**DEV2 testa**:
> "Posso tentar eu mesma? [Executar comando]"

**DEV1 apoia**:
> "Claro! Aqui está o terminal. [Compartilhar controle]"

---

#### [00:45 - 00:55] Teste 2: Ausência de PII (10 min)

**DEV1 executa**:
```bash
python 11_validate_lgpd.py --test pii
```

**DEV1 mostra**:
> "O script inspeciona todas as colunas do OLAP procurando por PII."
> "Resultado: Nenhum PII encontrado. ✅ PASSOU"

**DEV2 verifica**:
> "Posso ver a estrutura das tabelas?"

**DEV1 mostra**:
```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'ocupacoes_leitos_anonimizado';
```

---

#### [00:55 - 01:05] Teste 3: Generalização Temporal (10 min)

**DEV1 executa**:
```bash
python 11_validate_lgpd.py --test generalizacao
```

**DEV1 explica**:
> "Verificamos que todas as datas estão generalizadas."
> "Formato aceito: YYYY, YYYY-MM, YYYY-QN"
> "Resultado: 100% generalizado. ✅ PASSOU"

---

#### [01:05 - 01:10] Teste 4: Categorização (5 min)

**DEV1 executa**:
```bash
python 11_validate_lgpd.py --test categorizacao
```

**DEV1 mostra**:
> "Dados numéricos sensíveis são categorizados."
> "Ex: Tempo de permanência → curta/média/longa"
> "Resultado: Categorização adequada. ✅ PASSOU"

---

#### [01:10 - 01:20] Teste 5: Controle de Acesso (10 min)

**DEV1 executa**:
```bash
python 11_validate_lgpd.py --test acesso
```

**DEV1 demonstra**:
> "Tentando inserir dados no OLAP... [Executar INSERT]"
> "Erro: Permissão negada. ✅ PASSOU"

> "Usuários analíticos têm apenas SELECT."

**✅ Checkpoint**: Todos os testes executados? Resultados claros?

---

### [01:20 - 01:50] Discussão e Feedback (30 min)

**DEV1 pergunta**:
> "Dra. Maria, qual sua avaliação geral da conformidade LGPD?"

**DEV2 (como especialista) responde**:
> "Impressionante! Todos os testes passaram. Tenho algumas perguntas..."

**Perguntas possíveis**:
1. "Como vocês auditam acessos ao OLAP?"
2. "Qual o processo de resposta a incidentes?"
3. "Como garantem que novos campos não terão PII?"
4. "A documentação está completa para auditoria externa?"

**DEV1 responde cada uma**:
1. "Logs de auditoria no PostgreSQL + monitoramento"
2. "Temos um plano de resposta a incidentes documentado"
3. "Code review obrigatório + validação LGPD automatizada"
4. "Sim, toda documentação está em `/docs_DEV1/`"

**DEV1 pede feedback**:
> "Há algo que devemos melhorar ou documentar melhor?"

**DEV2 sugere**:
> "Recomendo adicionar um dashboard de conformidade em tempo real."

**DEV1 anota**:
> "Excelente sugestão! Vou criar um action item."

**✅ Checkpoint**: Feedback coletado? Action items anotados?

---

### [01:50 - 02:00] Próximos Passos (10 min)

**DEV1 resume**:
> "Resumindo nossa validação:"
> - "5/5 testes passaram ✅"
> - "Nenhuma não conformidade crítica"
> - "1 sugestão de melhoria (dashboard)"

**DEV1 pergunta**:
> "Qual sua decisão: Aprovado, Aprovado com ressalvas, ou Reprovado?"

**DEV2 decide**:
> "Aprovado com ressalva: implementar dashboard de conformidade em 2 semanas."

**DEV1 confirma**:
> "Perfeito! Vou:"
> 1. "Gerar a ata hoje mesmo"
> 2. "Criar action item para o dashboard"
> 3. "Enviar para sua aprovação em 24h"

**DEV1 agradece**:
> "Muito obrigado pelo seu tempo e expertise, Dra. Maria! Foi muito valioso."

**✅ Checkpoint**: Próximos passos claros? Encerramento profissional?

---

## 📝 CHECKLIST PÓS-SIMULAÇÃO

### Avaliação:
- [ ] Timing adequado? (ajustar se necessário)
- [ ] Transições suaves entre tópicos?
- [ ] Respostas às perguntas convincentes?
- [ ] Materiais funcionando corretamente?
- [ ] Ambiente técnico OK?

### Ajustes Necessários:
- [ ] Revisar slides (se houver)
- [ ] Testar scripts novamente
- [ ] Preparar respostas para perguntas difíceis
- [ ] Ajustar agenda (se necessário)
- [ ] Preparar materiais adicionais

### Confiança:
- [ ] Me sinto preparado para a validação real?
- [ ] Conheço bem o conteúdo?
- [ ] Sei responder perguntas técnicas?
- [ ] Estou confortável com o timing?

---

## 🎯 PONTOS DE ATENÇÃO

### Durante a Simulação:
- ⏱️ **Cronometrar cada seção**
- 📝 **Anotar dificuldades**
- 🤔 **Identificar perguntas difíceis**
- 🔧 **Testar todos os scripts**

### Feedback do DEV2:
- "O que funcionou bem?"
- "O que precisa melhorar?"
- "Perguntas que não soube responder?"
- "Sugestões de ajuste?"

---

**Criado por**: DEV1  
**Data**: 25/02/2026  
**Status**: ✅ Pronto para simulação  
**Próxima ação**: Executar simulação às 14:00

