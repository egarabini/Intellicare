# Guia Operacional - D3 Teleconsulta/Vídeo

## 📋 Visão Geral

Este guia descreve como operar e gerenciar teleconsultas usando o módulo D3 (Jitsi Meet).

---

## 🎯 Casos de Uso

### 1. Teleconsulta Individual

**Cenário**: Consulta médica 1:1 entre profissional e paciente.

**Fluxo**:
1. Wanda agenda teleconsulta
2. Sistema cria sala Jitsi
3. Profissional recebe link com role=MODERATOR
4. Paciente recebe link com role=PARTICIPANT
5. Ambos entram na sala no horário agendado
6. Após consulta, sala é finalizada automaticamente

### 2. Sala Multidisciplinar

**Cenário**: Discussão de caso clínico com múltiplos profissionais.

**Fluxo**:
1. Coordenador cria sala multidisciplinar
2. Convida profissionais (médicos, enfermeiros, etc.)
3. Todos recebem link com role=PRESENTER
4. Discussão do caso com compartilhamento de tela
5. Sala permanece ativa até finalização manual

### 3. Grupo Terapêutico

**Cenário**: Sessão de grupo com múltiplos pacientes.

**Fluxo**:
1. Terapeuta cria sala de grupo
2. Convida pacientes
3. Terapeuta tem role=MODERATOR
4. Pacientes têm role=PARTICIPANT
5. Lobby habilitado para controle de entrada

### 4. Emergência

**Cenário**: Sala de emergência com acesso rápido.

**Fluxo**:
1. Sistema cria sala de emergência
2. Profissionais de plantão recebem link
3. Sala permanece ativa 24/7
4. Acesso imediato sem lobby

---

## 🔧 Operações Comuns

### Criar Sala de Teleconsulta

```bash
curl -X POST http://localhost:8005/api/v1/jitsi/rooms \
  -H "Content-Type: application/json" \
  -d '{
    "room_type": "teleconsulta",
    "scheduled_start": "2026-02-20T10:00:00Z",
    "scheduled_end": "2026-02-20T11:00:00Z",
    "title": "Teleconsulta - Dr. Maria Silva",
    "description": "Consulta de cardiologia",
    "patient_id": "patient-123",
    "max_participants": 2
  }'
```

**Resposta**:
```json
{
  "id": "uuid-da-sala",
  "room_name": "intellicare-teleconsulta-abc123",
  "room_url": "https://meet.gsi.srv.br/intellicare-teleconsulta-abc123",
  "status": "scheduled",
  "participants": []
}
```

### Adicionar Participante

```bash
curl -X POST http://localhost:8005/api/v1/jitsi/rooms/{room_id}/participants \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "doctor-001",
    "user_name": "Dr. Maria Silva",
    "user_email": "maria@hospital.com",
    "role": "moderator",
    "expires_in_minutes": 120
  }'
```

**Resposta**:
```json
{
  "id": "uuid-do-participante",
  "room_id": "uuid-da-sala",
  "user_id": "doctor-001",
  "user_name": "Dr. Maria Silva",
  "role": "moderator",
  "room_url": "https://meet.gsi.srv.br/intellicare-teleconsulta-abc123?jwt=eyJhbGc..."
}
```

### Iniciar Sala

```bash
curl -X POST http://localhost:8005/api/v1/jitsi/rooms/{room_id}/start
```

### Finalizar Sala

```bash
curl -X POST http://localhost:8005/api/v1/jitsi/rooms/{room_id}/end
```

### Cancelar Sala

```bash
curl -X POST http://localhost:8005/api/v1/jitsi/rooms/{room_id}/cancel
```

### Listar Salas Ativas

```bash
curl "http://localhost:8005/api/v1/jitsi/rooms?status=active&limit=10"
```

---

## 👥 Roles e Permissões

### MODERATOR

**Permissões**:
- ✅ Iniciar/finalizar sala
- ✅ Remover participantes
- ✅ Silenciar participantes
- ✅ Gravar sessão
- ✅ Compartilhar tela
- ✅ Controlar lobby

**Uso**: Profissionais de saúde, coordenadores

### PRESENTER

**Permissões**:
- ✅ Compartilhar tela
- ✅ Falar e mostrar vídeo
- ❌ Remover participantes
- ❌ Gravar sessão

**Uso**: Profissionais em salas multidisciplinares

### PARTICIPANT

**Permissões**:
- ✅ Falar e mostrar vídeo
- ✅ Chat
- ❌ Compartilhar tela
- ❌ Remover participantes

**Uso**: Pacientes, observadores

---

## ⚙️ Configurações

### Duração de Sala

**Padrão**: 60 minutos  
**Mínimo**: 5 minutos  
**Máximo**: 8 horas

### Participantes

**Padrão**: 10 participantes  
**Máximo**: Configurável via `JITSI_MAX_PARTICIPANTS`

### Gravação

**Habilitado**: `JITSI_ENABLE_RECORDING=true`  
**Desabilitado**: `JITSI_ENABLE_RECORDING=false`

**Nota**: Gravações requerem consentimento do paciente (LGPD).

### Lobby

**Habilitado**: `JITSI_ENABLE_LOBBY=true`  
**Uso**: Controle de entrada em salas de grupo

---

## 🔍 Monitoramento

### Métricas Prometheus

- `communication_messages_sent_total{channel="jitsi"}`: Total de convites enviados
- `communication_messages_failed_total{channel="jitsi"}`: Total de falhas
- `communication_dispatch_duration_seconds{channel="jitsi"}`: Latência

### Logs

```bash
# Ver logs de criação de salas
grep "Sala Jitsi criada" /var/log/comunicacao.log

# Ver logs de participantes
grep "Participante adicionado" /var/log/comunicacao.log

# Ver logs de webhooks
grep "Jitsi webhook recebido" /var/log/comunicacao.log
```

---

## 🚨 Troubleshooting

### Problema: Token JWT inválido

**Sintoma**: Participante não consegue entrar na sala

**Solução**:
1. Verificar `JITSI_APP_ID` e `JITSI_APP_SECRET`
2. Verificar expiração do token (`token_expires_at`)
3. Gerar novo token via API

### Problema: Sala não inicia

**Sintoma**: Status permanece SCHEDULED

**Solução**:
1. Chamar endpoint `/rooms/{room_id}/start`
2. Verificar se `scheduled_start` não está no passado

### Problema: Participante não aparece na lista

**Sintoma**: Participante entrou mas não aparece em `/rooms/{room_id}`

**Solução**:
1. Verificar webhook do Jitsi está configurado
2. Atualizar manualmente via API

---

## 📞 Suporte

**Equipe**: DevOps IntelliCare  
**Email**: devops@intellicare.com  
**Slack**: #intellicare-comunicacao

