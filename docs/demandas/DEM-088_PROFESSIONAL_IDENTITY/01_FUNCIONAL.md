# DEM-088 — Professional Identity Integration

## Contexto

A DEM-084 integrou identidade centralizada ao cadastro de **pacientes** — quando o CPF é informado, o sistema cria ou recupera uma entrada em `platform.pessoa_fisica` e vincula o `pessoa_id` ao registro do paciente.

Profissionais de saúde (médicos, enfermeiros, coordenadores) são igualmente pessoas físicas registradas no sistema. A tabela `professionals` (migration 006) ainda não possui o campo `pessoa_id`, criando uma assimetria: pacientes têm identidade centralizada, profissionais não.

## O que esta DEM entrega

- Campo `pessoa_id UUID` nullable adicionado à tabela `professionals` (migration 024)
- Ao criar ou atualizar um profissional com CPF preenchido, o sistema chama `find_or_create_by_cpf()` e vincula o `pessoa_id` automaticamente
- Comportamento idêntico ao DEM-084: transparente para o usuário, sem mudança visual no formulário
- Um profissional com `pessoa_id` pode futuramente ter seu perfil consultado de forma centralizada entre estabelecimentos

## Impacto no usuário

Nenhum visível. O formulário de cadastro de profissional não muda. A integração acontece no backend quando o campo CPF está preenchido.

## Critério de aceite

```
POST /clinico/professionals
Body: { "nome": "Dr. Costa", "cpf": "99988877700", ... }
→ professionals.pessoa_id preenchido com UUID de platform.pessoa_fisica

POST /clinico/professionals (mesmo CPF, outro estabelecimento)
→ mesmo pessoa_id retornado (idempotência confirmada)
```

## Dependências

- DEM-083 (identity foundation) ✅ concluída
- DEM-084 (patient identity) ✅ concluída — padrão a seguir
- `platform.pessoa*` migrations 021 ✅ aplicadas
