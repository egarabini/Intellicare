# 🚀 ESPECIFICAÇÃO FUNCIONAL - INTEGRAÇÃO KEYCLOAK PARA DEV1

## 📋 CONTEXTO
Integrar os 9 módulos INTELLICARE com o **Keycloak externo já em produção**: `keycloak.gsi.srv.br`

## 🎯 OBJETIVOS
1. **SSO (Single Sign-On)**: Usuário autentica uma vez, acessa todos os módulos
2. **Controle de Acesso Centralizado**: RBAC + ABAC via Keycloak
3. **Segurança Avançada**: MFA, auditoria, conformidade
4. **Integração Transparente**: Mínimo impacto nos módulos existentes

## 🏗️ ARQUITETURA
```
┌─────────────────────────────────────────────────────────┐
│         KEYCLOAK GSI (keycloak.gsi.srv.br)              │
│  ┌─────────────────────────────────────────────────┐    │
│  │ • Realm: gsisaude (ou similar)                  │    │
│  │ • 9 Clients (1 por módulo INTELLICARE)          │    │
│  │ • Users: Do AD/LDAP do GSI                      │    │
│  │ • Roles: Hierarquia específica INTELLICARE      │    │
│  └─────────────────────────────────────────────────┘    │
└───────────────┬─────────────────────────────────────────┘
                │ (OAuth2/OIDC)
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ Módulos │ │ Módulos │ │ Portal  │
│ INTELLI-│ │ INTELLI-│ │ React   │
│ CARE    │ │ CARE    │ │         │
└─────────┘ └─────────┘ └─────────┘
```

## 📅 PLANO DE AÇÃO - 3 SEMANAS

### SEMANA 1: INVESTIGAÇÃO E CONFIGURAÇÃO
#### Dia 1-2: Acesso e Análise
1. **Obter acesso** ao Keycloak GSI
   - URL: `https://keycloak.gsi.srv.br/auth/admin/`
   - Credenciais: Solicitar ao time GSI
   
2. **Analisar ambiente existente**
   - Qual realm usar? (`gsisaude` ou outro)
   - Estrutura atual de clients/roles
   - Federação com AD/LDAP?
   - Políticas de segurança

3. **Documentar descobertas**
   - Criar `docs/keycloak_gsi_analysis.md`

#### Dia 3-5: Configurar Keycloak
1. **Criar 9 clients** (1 por módulo):
   - `intellicare-core`
   - `intellicare-wanda`
   - `intellicare-florence`
   - `intellicare-oswaldo`
   - `intellicare-zilda`
   - `intellicare-geralda`
   - `intellicare-donabedian`
   - `intellicare-portal`
   - `intellicare-comunicacao`

2. **Configurar cada client**:
   - Access Type: `confidential`
   - Valid Redirect URIs: URLs dos módulos
   - Service Accounts: Habilitado
   - Salvar client secrets

3. **Criar roles INTELLICARE**:
   ```
   gsisaude:intellicare:admin
   ├── gsisaude:intellicare:hospital_admin
   ├── gsisaude:intellicare:health_professional
   │   ├── gsisaude:intellicare:doctor
   │   ├── gsisaude:intellicare:nurse
   │   └── gsisaude:intellicare:nutritionist
   └── gsisaude:intellicare:care_coordinator
   ```

4. **Configurar Protocol Mappers**:
   - `hospital_id` → token claim
   - `specialty` → token claim
   - `license_number` → token claim
   - `department` → token claim

### SEMANA 2: BIBLIOTECA E PRIMEIRA INTEGRAÇÃO
#### Dia 6-8: Criar Biblioteca `intellicare-auth`
```bash
# Estrutura do projeto
intellicare-auth/
├── pyproject.toml
├── requirements.txt
├── setup.py
└── intellicare_auth/
    ├── __init__.py
    ├── client.py          # Cliente Keycloak GSI
    ├── middleware.py      # Middleware FastAPI
    ├── decorators.py      # Decorators para roles
    └── config.py          # Configurações
```

#### Código Principal (`client.py`):
```python
class GSIKeycloakClient:
    """Cliente para Keycloak externo do GSI"""
    
    def __init__(self, realm: str = "gsisaude"):
        self.server_url = "https://keycloak.gsi.srv.br/auth"
        self.realm = realm
    
    async def validate_token(self, token: str) -> dict:
        """Valida token JWT do Keycloak GSI"""
        # Implementação com validação local (JWKS)
        # e fallback para introspection se necessário
    
    async def get_user_info(self, token: str) -> dict:
        """Obtém informações do usuário"""
        # Chamada ao endpoint /userinfo
```

#### Middleware FastAPI (`middleware.py`):
```python
from fastapi import Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Dependency para obter usuário atual"""
    token = credentials.credentials
    # Validar com GSIKeycloakClient
    return user_info
```

#### Decorators (`decorators.py`):
```python
def requires_role(role: str):
    """Decorator para exigir role específica"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Verificar role no usuário
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

#### Dia 9-10: Integrar Primeiro Módulo (`intellicare-core`)
1. **Instalar biblioteca**:
   ```bash
   cd MODULARIZACAO/intellicare-core
   pip install -e ../intellicare-auth
   ```

2. **Modificar `main.py`**:
   ```python
   from intellicare_auth import get_current_user, requires_role
   
   @app.get("/api/config")
   @requires_role("gsisaude:intellicare:admin")
   async def get_config(user: dict = Depends(get_current_user)):
       return {
           "config": "data",
           "user": user["preferred_username"]
       }
   ```

3. **Testar**:
   ```bash
   # Iniciar módulo
   uvicorn src.intellicare_core.api.main:app --reload --port 8000
   
   # Testar endpoints
   curl http://localhost:8000/health
   curl http://localhost:8000/api/config  # Deve retornar 401
   ```

#### Dia 11-12: Testes e Documentação
1. **Criar testes**:
   ```python
   # tests/test_auth_integration.py
   def test_protected_endpoint_no_auth():
       response = client.get("/api/config")
       assert response.status_code == 401
   ```

2. **Documentar**:
   - `INTEGRACAO_KEYCLOAK.md` no módulo core
   - Exemplos de uso
   - Troubleshooting

### SEMANA 3: EXPANSÃO E FINALIZAÇÃO
#### Dia 13-15: Integrar Outros Módulos
**Padrão para cada módulo:**
1. Adicionar `intellicare-auth` às dependências
2. Importar e usar `get_current_user` e `requires_role`
3. Proteger endpoints críticos
4. Testar

**Ordem sugerida:**
1. `intellicare-wanda` (orquestrador crítico)
2. `intellicare-portal` (frontend React)
3. `intellicare-florence` (análise clínica)
4. `intellicare-oswaldo` (doenças crônicas)
5. Demais módulos

#### Dia 16-17: Portal React
```javascript
// Configuração Keycloak-js
const keycloak = new Keycloak({
  url: 'https://keycloak.gsi.srv.br/auth',
  realm: 'gsisaude',
  clientId: 'intellicare-portal'
});

// Inicializar
keycloak.init({ onLoad: 'login-required' });
```

#### Dia 18-19: Testes Finais
1. **Testes de integração** entre módulos
2. **Testes de performance** (latência autenticação)
3. **Testes de segurança** (token validation, role checking)
4. **Testes de usabilidade** (fluxo de login)

#### Dia 20-21: Documentação Final
1. **Guia do desenvolvedor** (como integrar novos módulos)
2. **Manual do administrador** (gerenciar roles/usuários)
3. **Runbooks de operação** (troubleshooting, monitoramento)
4. **FAQ para usuários finais**

## 🔧 TECNOLOGIAS
- **Keycloak**: 22.0+ (externo, gerenciado pelo GSI)
- **Python**: 3.11+ com FastAPI
- **Bibliotecas**: `python-keycloak`, `authlib`, `pyjwt`, `httpx`
- **Frontend**: `keycloak-js` para React
- **Testes**: `pytest`, `httpx` para testes async

## 📊 MÉTRICAS DE SUCESSO
### Técnicas:
- ✅ Autenticação < 300ms (p95)
- ✅ 99.9% disponibilidade do SSO
- ✅ Zero vulnerabilidades críticas
- ✅ Cobertura de testes > 85%

### Operacionais:
- ✅ 100% dos módulos integrados
- ✅ Login único funcionando
- ✅ Controle de acesso granular
- ✅ Auditoria completa

### Negócio:
- ✅ Conformidade com políticas GSI
- ✅ Redução de tickets de login > 80%
- ✅ Experiência do usuário melhorada
- ✅ Base para expansão futura

## ⚠️ RISCOS E MITIGAÇÕES
1. **Keycloak externo indisponível**
   - Mitigação: Cache de tokens, fallback local (emergencial)
   
2. **Latência alta na autenticação**
   - Mitigação: Cache JWKS, validação local de tokens
   
3. **Problemas de compatibilidade**
   - Mitigação: Testes extensivos, versão específica do client
   
4. **Complexidade de configuração**
   - Mitigação: Documentação detalhada, scripts de setup

## 🎯 CHECKLIST FINAL
### Configuração Keycloak:
- [ ] 9 clients criados (1 por módulo)
- [ ] Client secrets gerados e armazenados
- [ ] Roles INTELLICARE configuradas
- [ ] Protocol Mappers para atributos
- [ ] Políticas de segurança aplicadas

### Biblioteca `intellicare-auth`:
- [ ] Cliente GSI Keycloak implementado
- [ ] Middleware FastAPI funcionando
- [ ] Decorators para controle de acesso
- [ ] Testes unitários > 90% cobertura
- [ ] Publicada no PyPI interno

### Módulos Integrados:
- [ ] `intellicare-core` ✅
- [ ] `intellicare-wanda` ✅
- [ ] `intellicare-florence` ✅
- [ ] `intellicare-oswaldo` ✅
- [ ] `intellicare-zilda` ✅
- [ ] `intellicare-geralda` ✅
- [ ] `intellicare-donabedian` ✅
- [ ] `intellicare-portal` ✅ (React)
- [ ] `intellicare-comunicacao` ✅

### Documentação:
- [ ] Guia do desenvolvedor
- [ ] Manual do administrador
- [ ] Runbooks de operação
- [ ] FAQ para usuários

## 📞 SUPORTE
### Níveis:
1. **DEV1**: Implementação principal
2. **Time GSI**: Suporte Keycloak
3. **Especialista Segurança**: Políticas e auditoria

### Contatos Críticos:
- **GSI Keycloak Admin**: [contato]
- **DEV1 Backup**: [contato]
- **Segurança da Informação**: [contato]

---

**📅 PRAZO TOTAL**: 3 semanas (15 dias úteis)  
**👥 RESPONSÁVEL**: DEV1  
**🔗 DEPENDÊNCIAS**: Acesso ao Keycloak GSI, módulos estáveis  
**🚀 ENTREGA**: Sistema com SSO, controle de acesso centralizado, pronto para produção  

**PRÓXIMO PASSO**: DEV1 solicitar acesso ao Keycloak GSI e iniciar fase de investigação.