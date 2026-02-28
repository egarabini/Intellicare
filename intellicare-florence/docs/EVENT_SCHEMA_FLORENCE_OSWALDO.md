# EVENT SCHEMAS - INTEGRAÇÃO FLORENCE-OSWALDO
## Contrato de Eventos para RabbitMQ/Message Bus
### Data: 12 de Fevereiro de 2026

---

## 🎯 OBJETIVO

Definir o **contrato de mensagens** entre Florence e Oswaldo via RabbitMQ.

Quando Oswaldo está implementado, ele apenas "plugou" nestes eventos já definidos.
Nenhuma mudança nos schemas de eventos.

---

## 📋 EVENTOS GLOBAIS (3 tipos)

```
┌─────────────────────────────────────────────────────────────┐
│                      EVENT BUS (RabbitMQ)                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Publisher: Florence               Consumer: Oswaldo        │
│  ├─ exame_critico                  └─ processar            │
│  ├─ exame_created                                            │
│  └─ alerta_novo                                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Queues RabbitMQ Necessárias
```
florence.exame.critico       → Exames com resultado crítico
florence.exame.created       → Novo exame criado
florence.alerta.novo         → Novo alerta gerado
```

---

## 1️⃣ EVENTO: ExameCritico

**Quando é publicado**:
- ✅ Exame finalizado E validação detecta incoerência clínica
- ✅ Resultado crítico (ex: glicemia 350, hemoglobina <7)
- ✅ Necessário revisão médica urgente

**Queue**: `florence.exame.critico`

**Schema JSON**:
```json
{
  "version": "1.0",
  "event_type": "exame_critico",
  "timestamp": "2026-02-12T14:30:00Z",
  "event_id": "evt_7f8e9d0c1b2a3f4e",
  
  "paciente": {
    "id_hash": "a1b2c3d4e5f6... (SHA256 - sem CPF)",
    "age_anos": 45,
    "sexo": "M",
    "condicoes": ["diabético", "hipertensão"]
  },
  
  "exame": {
    "id": "exm_12345678",
    "tipo": "hemograma",  // hemograma | lipidograma | hepatograma | funcao_renal | glicemia
    "data_coleta": "2026-02-12T10:00:00Z",
    "data_resultado": "2026-02-12T14:30:00Z",
    
    "resultado": {
      // Os parâmetros específicos do exame
      "hemoglobina": 6.5,
      "hematocrito": 20,
      "leucocitos": 3.2,
      // ... outros parâmetros
    }
  },
  
  "validacao": {
    "validador": "ClinicaAlgorithmValidator",
    "valido": false,
    "tipo_problema": "incoerencia_absoluta",  // incoerencia_absoluta | resultado_critico | ambos
    
    "problemas": [
      {
        "parametro": "hemoglobina",
        "valor_reportado": 6.5,
        "valor_esperado_min": 13.5,
        "valor_esperado_max": 17.5,
        "severidade": "critica",  // info | aviso | critica
        "mensagem": "Hemoglobina crítica (<7 g/dL) - risco de sintomate"
      }
    ]
  },
  
  "recomendacao": {
    "acao": "revisar_imediatamente",  // revisar_imediatamente | revisar_hoje | examinar_amostra
    "especialista_recomendado": "hematologia",  // hematologia | cardiologia | nefrologia | etc
    "encaminhar_emergencia": true,
    "justificativa": "Anemia grave detectada"
  },
  
  "origem": {
    "sistema": "florence",
    "versao_api": "v1",
    "usuario_criacao": "tecnico_lab_001"
  }
}
```

**Campos Obrigatórios**: 
- event_id, timestamp, paciente.id_hash, exame.id, exame.tipo
- validacao.valido, validacao.problemas

**Campos Opcionais**:
- recomendacao.especialista_recomendado (null se não houver indicação)

**Exemplo Real**:
```json
{
  "event_id": "evt_abc123",
  "timestamp": "2026-02-12T14:30:00Z",
  "event_type": "exame_critico",
  "paciente": {
    "id_hash": "d4ffa1a7c6e2...",
    "age_anos": 67,
    "sexo": "F"
  },
  "exame": {
    "id": "exm_999",
    "tipo": "glicemia",
    "data_coleta": "2026-02-12T08:00:00Z",
    "resultado": {
      "glicemia": 350,
      "tipo_amostra": "aleatoria",
      "paciente_diabetico": true
    }
  },
  "validacao": {
    "valido": false,
    "problemas": [{
      "parametro": "glicemia",
      "valor_reportado": 350,
      "severidade": "critica",
      "mensagem": "Hiperglicemia crítica (>300) - encaminhar emergência"
    }]
  },
  "recomendacao": {
    "acao": "revisar_imediatamente",
    "encaminhar_emergencia": true,
    "justificativa": "Hiperglicemia crítica-risco de coma diabético"
  }
}
```

---

## 2️⃣ EVENTO: ExameCreated

**Quando é publicado**:
- ✅ Novo exame foi criado no Florence
- ✅ Validação passou (sem problemas críticos)
- ✅ Oswaldo pode processar dados para análise metabolismo

**Queue**: `florence.exame.created`

**Schema JSON**:
```json
{
  "version": "1.0",
  "event_type": "exame_created",
  "timestamp": "2026-02-12T14:30:00Z",
  "event_id": "evt_7f8e9d0c1b2a3f4e",
  
  "paciente": {
    "id_hash": "a1b2c3d4e5f6...",
    "age_anos": 45,
    "sexo": "M",
    "altura_cm": 175,
    "peso_kg": 85,
    "imc": 27.8,
    "condicoes": ["diabético"]
  },
  
  "exame": {
    "id": "exm_12345678",
    "tipo": "hemograma",
    "data_coleta": "2026-02-12T08:00:00Z",
    "data_resultado": "2026-02-12T14:30:00Z",
    
    "resultado": {
      // Todos os parâmetros do tipo de exame
      "hemoglobina": 14.5,
      "hematocrito": 42.5,
      "leucocitos": 7.2,
      "plaquetas": 250,
      "linfocitos_perc": 30,
      "neutrofilos_perc": 60,
      "monocitos_perc": 8,
      "eosinofilos_perc": 2
    }
  },
  
  "validacao": {
    "validador": "ClinicaAlgorithmValidator",
    "valido": true,
    "problemas": [],
    "avisos": []
  },
  
  "contexto_padrao": {
    // Informações para Oswaldo processar
    "tipo_coleta": "eletiva",  // eletiva | emergencia | rotina_internacao
    "medicamentos_conhecidos": [
      {"nome": "metformina", "dose": "500mg", "frequencia": "2x/dia"}
    ],
    "historico_metabolico": {
      "tem_diabetes": true,
      "controle_glicemia": "regular",
      "ultima_glicemia_dias_atras": 3
    }
  },
  
  "origem": {
    "sistema": "florence",
    "versao_api": "v1",
    "usuario_criacao": "tecnico_lab_001"
  }
}
```

**Campos Obrigatórios**:
- event_id, timestamp, paciente.id_hash, exame.id, exame.tipo, exame.resultado
- validacao.valido

**Campos Opcionais**:
- contexto_padrao (null se não houver)
- medicamentos_conhecidos (array vazia se não houver)

**Exemplo Real**:
```json
{
  "event_id": "evt_def456",
  "timestamp": "2026-02-12T14:30:00Z",
  "event_type": "exame_created",
  "paciente": {
    "id_hash": "a1b2c3...",
    "age_anos": 52,
    "sexo": "M",
    "condicoes": ["hipertensão", "dislipidemia"]
  },
  "exame": {
    "id": "exm_1001",
    "tipo": "lipidograma",
    "resultado": {
      "colesterol_total": 280,
      "hdl": 35,
      "ldl": 200,
      "triglicerida": 150
    }
  },
  "validacao": {
    "valido": true,
    "problemas": []
  }
}
```

---

## 3️⃣ EVENTO: AlertaNovo

**Quando é publicado**:
- ✅ Florence gerou alerta baseado em validação de série de exames
- ✅ Padrão detectado (ex: glicemia aumentando há 3 exames)
- ✅ Oswaldo deve processar para gerar recomendação metabolismo

**Queue**: `florence.alerta.novo`

**Schema JSON**:
```json
{
  "version": "1.0",
  "event_type": "alerta_novo",
  "timestamp": "2026-02-12T14:30:00Z",
  "event_id": "evt_7f8e9d0c1b2a3f4e",
  
  "paciente": {
    "id_hash": "a1b2c3d4e5f6...",
    "age_anos": 45,
    "sexo": "M"
  },
  
  "alerta": {
    "id": "alt_888",
    "tipo": "tendencia_glicemia_elevada",  // tendencia_* | padrão_* | anomalia_*
    "data_alerta": "2026-02-12T14:30:00Z",
    "severidade": "media",  // baixa | media | alta | critica
    
    "serie_exames": [
      {
        "exame_id": "exm_995",
        "data": "2026-02-09",
        "valor_glicemia": 160
      },
      {
        "exame_id": "exm_996",
        "data": "2026-02-10",
        "valor_glicemia": 180
      },
      {
        "exame_id": "exm_997",
        "data": "2026-02-12",
        "valor_glicemia": 210
      }
    ],
    
    "analise": {
      "tendencia": "crescente",
      "dias_analise": 3,
      "media_valores": 183.3,
      "taxa_crescimento": "+25 mg/dL em 3 dias"
    },
    
    "contexto": {
      "paciente_diabetico": true,
      "medicacoes_antidiabete": ["metformina 500mg"],
      "evento_precipitante": null  // ex: infeccao_detectada, modificacao_dieta
    }
  },
  
  "recomendacao": {
    "acao": "investigar_descontrole",
    "especialista_recomendado": "endocrinologia",
    "justificativa": "Glicemia ascendente em diabético. Possível desajuste medicamentoso ou evento precipitante."
  },
  
  "origem": {
    "sistema": "florence",
    "versao_api": "v1",
    "usuario_criacao": "sistema_automatico"
  }
}
```

**Campos Obrigatórios**:
- event_id, timestamp, paciente.id_hash, alerta.id, alerta.tipo, alerta.serie_exames
- analise.tendencia

**Campos Opcionais**:
- contexto.evento_precipitante (null se não houver)
- recomendacao (null se não houver)

**Exemplo Real**:
```json
{
  "event_id": "evt_ghi789",
  "timestamp": "2026-02-12T14:30:00Z",
  "event_type": "alerta_novo",
  "paciente": {
    "id_hash": "xyz789...",
    "age_anos": 68
  },
  "alerta": {
    "id": "alt_999",
    "tipo": "tendencia_ureia_elevada",
    "severidade": "alta",
    "serie_exames": [
      {"exame_id": "exm_50", "data": "2026-02-08", "valor_ureia": 45},
      {"exame_id": "exm_51", "data": "2026-02-10", "valor_ureia": 62},
      {"exame_id": "exm_52", "data": "2026-02-12", "valor_ureia": 85}
    ],
    "analise": {
      "tendencia": "crescente",
      "dias_analise": 4,
      "taxa_crescimento": "+40 mg/dL em 4 dias"
    }
  },
  "recomendacao": {
    "acao": "investigar_funcao_renal",
    "especialista_recomendado": "nefrologia",
    "justificativa": "Ureia em ascensão. Possível insuficiência renal aguda."
  }
}
```

---

## 🔄 FLUXO DE INTEGRAÇÃO

```
┌──────────────────┐
│   Florence       │
│                  │
│ 1. Cria Exame    │
│    (input)       │
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│  Validação       │
│  Clínica         │
│  (6 algoritmos)  │
└────────┬─────────┘
         │ ✅ VALIDO
         ├──────────────┬──────────────┐
         │              │              │
         ↓              ↓              ↓
┌───────────────┐ ┌──────────────┐ ┌──────────────┐
│ Exame OK?     │ │ Crítico?     │ │ Padrão/      │
│ Publicar      │ │ Publicar     │ │ Alerta?      │
│ exame_created │ │ exame_critico│ │ Publicar     │
│               │ │              │ │ alerta_novo  │
└───────────────┘ └──────────────┘ └──────────────┘
         │              │              │
         └──────────────┴──────────────┘
                        │
                        ↓
            ┌─────────────────────┐
            │   RabbitMQ Queues   │
            │                     │
            │ · exame_created     │
            │ · exame_critico     │
            │ · alerta_novo       │
            └────────────┬────────┘
                         │
                    ⏳ Aguardando
                    implementação
                    Oswaldo...
                         │
            ┌────────────↓─────────┐
            │                      │
            ↓                      ↓
        ┌────────────┐      ┌──────────────┐
        │ Oswaldo    │      │ Oswaldo      │
        │ (Futuro)   │      │ (Futuro)     │
        │ Subscriber │      │ Processador  │
        │ conecta    │      │ algoritmos   │
        │ aqui!      │      │              │
        └────────────┘      └──────────────┘
```

---

## 🔐 SEGURANÇA & CONFORMIDADE

### PII (Personally Identifiable Information)
- ✅ **NUNCA** incluir CPF direto
- ✅ **NUNCA** incluir nome do paciente
- ✅ **SEMPRE** usar id_hash (SHA256 do CPF)
- ✅ Conformidade LGPD Art. 7 (anonimização)

### Confidencialidade de Eventos
- [ ] RabbitMQ com TLS/SSL
- [ ] Credenciais em variáveis de ambiente
- [ ] Rate limiting (evitar DOS)
- [ ] Validação de schema em ambas as pontas

### Rastreabilidade
- ✅ Cada evento tem event_id único
- ✅ Cada evento tem timestamp ISO-8601
- ✅ Cada evento registra origem (usuario_criacao)

---

## 📋 VERSIONING & EVOLUÇÃO

**Versão Atual**: 1.0
**Data**: 12 FEV 2026

### Como Evoluir Schemas (sem quebrar Oswaldo):
1. **Adicionar campos opcionais** → Compatível ✅ (Oswaldo ignora)
2. **Remover campos opcionais** → Compatível ✅ (já não-obrigatórios)
3. **Mudar campos obrigatórios** → Incompatível ❌ (novo event_type)
4. **Mudar tipos de dados** → Incompatível ❌ (ex: string → number)

### Se Precisar Quebra Compatibilidade
```json
{
  "version": "2.0",  ← Incrementar
  "event_type": "exame_critico_v2",  ← Novo tipo
  ...
}
```

---

## 🧪 TESTE DE CONTRATO

Para garantir que Oswaldo vai conseguir processsoar quando for implementado:

### Teste 1: Validar Schema
```bash
# Validar JSON contra schema
python -m jsonschema \
  -i evento_exemplo.json \
  schema_exame_critico.json
```

### Teste 2: Publicar & Receber
```python
# Simular publicação Florence
publisher = FlorenaceEventPublisher()
publisher.publicar_exame_critico(exame_id="exm_123", criticidade=5)

# Simular Oswaldo subscriber recebebroken
subscriber = OswaldoSubscriberStub()
subscriber.processar_exame_critico(evento=dict(...))
```

### Teste 3: Compatibilidade Versão
```python
# Validar que versão 1.0 do evento
# continua processável na versão 2.0 de Oswaldo
evento_v1 = {"version": "1.0", ...}
assert subscriber_v2.pode_processar(evento_v1) == True
```

---

## 📞 CONTATO / DÚVIDAS

**Responsável Florence**: DEV2
**Data Criação**: 12/02/2026
**Próxima Review**: 20/02/2026 (antes de integração com Oswaldo)

---

*Este documento define o "contrato" entre Florence e Oswaldo.*
*Quando Oswaldo for implementado (Março), ele apenas "plugou" nestes eventos.*
*Mantém compatibilidade e zero surpresas na integração.*
