# ESPECIFICAÇÃO FUNCIONAL: INTEGRAÇÃO KEYCLOAK EM 8 MÓDULOS

## 📌 ID: DEV1-FUNC-001
## 🎯 Objetivo: Integrar autenticação Keycloak GSI em todos os módulos INTELLICARE
## 📅 Data: 12/02/2026
## 👤 Responsável: Product Owner/Arquiteto
## 👨‍💻 Responsável Técnico: DEV1
## ⚠️ Prioridade: ALTA
## ⏱️ Estimativa PO: 40 horas

## 1. CONTEXTO
O sistema INTELLICARE possui 8 módulos replicados que atualmente não possuem autenticação centralizada. O Keycloak do GSI (keycloak.gsi.srv.br) já está configurado e funcionando. É necessário integrar todos os módulos para usar autenticação única (SSO) com controle de acesso baseado em roles.

## 2. REQUISITOS FUNCIONAIS

### RF-001: Autenticação Única (SSO)
**Descrição**: Usuário autentica uma vez no Keycloak e acessa todos os 8 módulos sem necessidade de novo login.
**Critérios de Aceite**:
- [ ] Token do Keycloak válido em todos os módulos
- [ ] Logout global (logout em um módulo = logout em todos)
- [ ] Sessão única gerenciada pelo Keycloak
- [ ] Redirecionamento automático para login quando não autenticado

### RF-002: Controle de Acesso Baseado em Roles (RBAC)
**Descrição**: Controle de acesso granular baseado em roles definidas no Keycloak.
**Critérios de Aceite**:
- [ ] Roles do Keycloak mapeadas para permissões nos módulos
- [ ] Hierarquia de roles respeitada (admin > médico > enfermeiro > paciente)
- [ ] Endpoints protegidos conforme role do usuário
- [ ] Mensagem de erro clara quando acesso negado

### RF-003: Atributos Customizados no Token
**Descrição**: Informações específicas do usuário disponíveis no token JWT.
**Critérios de Aceite**:
- [ ] Token contém: hospital_id, specialty, license_number, department
- [ ] Atributos usados para regras de negócio (ex: médico só vê pacientes do seu hospital)
- [ ] Atributos validados no Keycloak antes de ir para o token

### RF-004: Validação de Token Local
**Descrição**: Validação eficiente de tokens sem chamar Keycloak a cada request.
**Critérios de Aceite**:
- [ ] Validação local com JWKS (JSON Web Key Set)
- [ ] Cache de chaves públicas (TTL: 5 minutos)
- [ ] Fallback para validação no Keycloak se cache expirar
- [ ] Performance: validação < 50ms

### RF-005: Middleware de Autenticação
**Descrição**: Middleware padrão para todos os módulos FastAPI.
**Critérios de Aceite**:
- [ ] Middleware configurável por módulo
- [ ] Exceção para endpoints públicos (health, docs)
- [ ] Extração automática de usuário do token
- [ ] Logs de tentativas de acesso não autorizado

## 3. REQUISITOS NÃO FUNCIONAIS

### RNF-001: Performance
**Descrição**: Autenticação não pode impactar performance do sistema.
**Métrica**:
- Latência autenticação: < 200ms (p95)
- Throughput: suportar 1000 auth/segundo
- Cache hit rate: > 95%

### RNF-002: Segurança
**Descrição**: Implementação segura seguindo OWASP.
**Métrica**:
- Tokens JWT com assinatura RSA 2048+
- Refresh tokens com vida curta (15 minutos)
- Access tokens com vida curta (1 hora)
- Proteção contra replay attacks

### RNF-003: Disponibilidade
**Descrição**: Sistema deve funcionar mesmo se Keycloak estiver indisponível temporariamente.
**Métrica**:
- Cache de JWKS válido por 5 minutos sem Keycloak
- Fallback para modo offline com tokens pré-validados
- Degradação graciosa

### RNF-004: Manutenibilidade
**Descrição**: Fácil manutenção e extensão.
**Métrica**:
- Biblioteca centralizada (`intellicare-auth`)
- Configuração via environment variables
- Documentação completa
- Testes com cobertura > 90%

## 4. REGRAS DE NEGÓCIO

### RN-001: Hierarquia de Roles
```
root_admin
├── hospital_admin
│   ├── clinical_director
│   └── quality_manager
├── health_professional
│   ├── doctor
│   ├── nurse
│   └── nutritionist
└── care_coordinator
    └── case_manager
```

### RN-002: Escopo por Hospital
- Médico só vê pacientes do seu hospital (hospital_id)
- Admin hospital só gerencia seu hospital
- Root admin vê todos os hospitais

### RN-003: Horário de Acesso
- Profissionais: 24/7
- Administrativos: 8h-18h (segunda a sexta)
- Pacientes: 6h-22h

## 5. INTERFACES/INTEGRAÇÕES

### 5.1. Keycloak GSI
- **URL**: https://keycloak.gsi.srv.br/auth
- **Realm**: bemcuidar (confirmar)
- **Clients**: 8 clients (1 por módulo) já criados
- **Protocol**: OAuth2/OIDC

### 5.2. Módulos a Integrar
1. `intellicare-core` (porta 8000)
2. `intellicare-wanda` (porta 8001)
3. `intellicare-florence` (porta 8002)
4. `intellicare-oswaldo` (porta 8003)
5. `intellicare-zilda` (porta 8004)
6. `intellicare-geralda` (porta 8005)
7. `intellicare-donabedian` (porta 8006)
8. `intellicare-comunicacao` (porta 8007)
9. `intellicare-portal` (porta 3000 - React)

## 6. RESTRIÇÕES

### Técnicas:
- Não pode modificar estrutura existente dos módulos (apenas adicionar)
- Deve manter compatibilidade com código atual
- Não pode adicionar overhead significativo de performance

### Temporais:
- Entrega em 2 semanas
- Testes completos necessários

### Orçamentárias:
- Usar apenas tecnologias open-source
- Não contratar serviços externos

## 7. ENTREGÁVEIS

### 7.1. Código
- [ ] Biblioteca `intellicare-auth` (PyPI interno)
- [ ] Configuração Keycloak em todos os 8 módulos
- [ ] Middleware FastAPI padronizado
- [ ] Decorators para controle de acesso
- [ ] Scripts de deploy/configuration

### 7.2. Testes
- [ ] Testes unitários (cobertura > 90%)
- [ ] Testes de integração com Keycloak
- [ ] Testes de performance
- [ ] Testes de segurança

### 7.3. Documentação
- [ ] Guia de integração para desenvolvedores
- [ ] Manual do administrador
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Troubleshooting guide

### 7.4. Deploy
- [ ] Ambiente de desenvolvimento
- [ ] Ambiente de staging
- [ ] Scripts de migração
- [ ] Monitoramento configurado

## 8. MÉTRICAS DE SUCESSO

### Técnicas:
- ✅ 100% dos módulos com autenticação Keycloak
- ✅ SSO funcionando entre todos os módulos
- ✅ Performance: autenticação < 200ms
- ✅ Segurança: zero vulnerabilidades críticas
- ✅ Cobertura testes: > 90%

### Operacionais:
- ✅ Usuários conseguem logar uma vez e acessar tudo
- ✅ Controle de acesso funcionando conforme roles
- ✅ Logs de auditoria completos
- ✅ Monitoramento em tempo real

### Negócio:
- ✅ Conformidade com políticas GSI
- ✅ Redução de tickets de login > 80%
- ✅ Experiência do usuário melhorada
- ✅ Base para governança completa

---

## 📋 APROVAÇÕES

- [ ] **Aprovação Técnica (DEV1)**: _________________ Data: __/__/____
- [ ] **Aprovação Product Owner**: _________________ Data: __/__/____
- [ ] **Aprovação Segurança**: _________________ Data: __/__/____

## 🔄 PRÓXIMOS PASSOS

1. DEV1 analisa e cria especificação técnica
2. Revisão técnica com arquiteto
3. Aprovação formal
4. Implementação
5. Testes e validação
6. Entrega

---

**STATUS**: 📄 ESPECIFICAÇÃO FUNCIONAL PRONTA PARA ANÁLISE TÉCNICA