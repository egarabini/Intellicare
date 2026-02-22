# 🔐 Guia de Integração Keycloak - IntelliCare Portal (React)

**Módulo**: intellicare-portal  
**Tecnologia**: React  
**Port**: 3000  
**Client ID**: intellicare-portal  
**Client Secret**: xqK5rsRaH6n2Hw2BsuCQ3ZOpFdhwQOFa

---

## 📋 VISÃO GERAL

O portal React requer uma abordagem diferente dos módulos Python backend. Usaremos:
- **Keycloak JavaScript Adapter** para autenticação
- **Authorization Code Flow** (mais seguro para SPAs)
- **Token armazenado no sessionStorage**
- **Interceptor HTTP** para incluir token nas requisições

---

## 🔧 PASSO 1: Instalar Dependências

```bash
cd C:\DOCSHARE\INTELLICARE\MODULARIZACAO\intellicare-portal\frontend
npm install keycloak-js
# ou
yarn add keycloak-js
```

---

## 🔧 PASSO 2: Criar Configuração Keycloak

Criar arquivo `src/keycloak.js`:

```javascript
import Keycloak from 'keycloak-js';

const keycloak = new Keycloak({
  url: 'https://keycloak.gsi.srv.br/',
  realm: 'bemcuidar',
  clientId: 'intellicare-portal'
});

export default keycloak;
```

---

## 🔧 PASSO 3: Inicializar Keycloak no App

Modificar `src/App.js` ou `src/index.js`:

```javascript
import React, { useEffect, useState } from 'react';
import keycloak from './keycloak';

function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    keycloak.init({
      onLoad: 'login-required', // Força login
      checkLoginIframe: false,
      pkceMethod: 'S256' // PKCE para segurança
    }).then(authenticated => {
      setAuthenticated(authenticated);
      setLoading(false);
      
      if (authenticated) {
        console.log('✅ Usuário autenticado');
        console.log('Token:', keycloak.token);
        console.log('User Info:', keycloak.tokenParsed);
      }
    }).catch(error => {
      console.error('❌ Erro ao inicializar Keycloak:', error);
      setLoading(false);
    });

    // Refresh token automaticamente
    setInterval(() => {
      keycloak.updateToken(70).then(refreshed => {
        if (refreshed) {
          console.log('🔄 Token renovado');
        }
      }).catch(() => {
        console.error('❌ Falha ao renovar token');
        keycloak.login();
      });
    }, 60000); // A cada 60 segundos

  }, []);

  if (loading) {
    return <div>Carregando...</div>;
  }

  if (!authenticated) {
    return <div>Não autenticado</div>;
  }

  return (
    <div className="App">
      <h1>IntelliCare Portal</h1>
      <p>Bem-vindo, {keycloak.tokenParsed?.preferred_username}</p>
      <button onClick={() => keycloak.logout()}>Sair</button>
      
      {/* Seu app aqui */}
    </div>
  );
}

export default App;
```

---

## 🔧 PASSO 4: Criar Interceptor HTTP (Axios)

Criar arquivo `src/api/axios.js`:

```javascript
import axios from 'axios';
import keycloak from '../keycloak';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000'
});

// Interceptor para adicionar token
api.interceptors.request.use(
  config => {
    if (keycloak.token) {
      config.headers.Authorization = `Bearer ${keycloak.token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Interceptor para tratar erros de autenticação
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      console.error('❌ Token inválido ou expirado');
      keycloak.login();
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

## 🔧 PASSO 5: Usar API com Autenticação

Exemplo de componente usando a API:

```javascript
import React, { useEffect, useState } from 'react';
import api from './api/axios';

function PillarsList() {
  const [pillars, setPillars] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/pillars')
      .then(response => {
        setPillars(response.data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Erro ao carregar pillars:', error);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Carregando...</div>;

  return (
    <div>
      <h2>Pillars</h2>
      <ul>
        {pillars.map(pillar => (
          <li key={pillar.id}>{pillar.name}</li>
        ))}
      </ul>
    </div>
  );
}

export default PillarsList;
```

---

## 🔧 PASSO 6: Criar Context para Autenticação

Criar arquivo `src/contexts/AuthContext.js`:

```javascript
import React, { createContext, useContext, useState, useEffect } from 'react';
import keycloak from '../keycloak';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    keycloak.init({
      onLoad: 'login-required',
      checkLoginIframe: false,
      pkceMethod: 'S256'
    }).then(authenticated => {
      if (authenticated) {
        setUser({
          username: keycloak.tokenParsed?.preferred_username,
          email: keycloak.tokenParsed?.email,
          roles: keycloak.tokenParsed?.realm_access?.roles || [],
          firstName: keycloak.tokenParsed?.given_name,
          lastName: keycloak.tokenParsed?.family_name
        });
      }
      setLoading(false);
    });
  }, []);

  const logout = () => {
    keycloak.logout();
  };

  const hasRole = (role) => {
    return user?.roles?.includes(role) || false;
  };

  return (
    <AuthContext.Provider value={{ user, loading, logout, hasRole, keycloak }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
```

---

## 🔧 PASSO 7: Proteger Rotas

Criar componente `ProtectedRoute.js`:

```javascript
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';

function ProtectedRoute({ children, requiredRole }) {
  const { user, loading, hasRole } = useAuth();

  if (loading) {
    return <div>Carregando...</div>;
  }

  if (!user) {
    return <Navigate to="/login" />;
  }

  if (requiredRole && !hasRole(requiredRole)) {
    return <div>Acesso negado. Role necessária: {requiredRole}</div>;
  }

  return children;
}

export default ProtectedRoute;
```

**Uso**:
```javascript
<Route path="/admin" element={
  <ProtectedRoute requiredRole="intellicare_admin">
    <AdminPanel />
  </ProtectedRoute>
} />
```

---

## 🔧 PASSO 8: Variáveis de Ambiente

Criar arquivo `.env`:

```bash
REACT_APP_KEYCLOAK_URL=https://keycloak.gsi.srv.br/
REACT_APP_KEYCLOAK_REALM=bemcuidar
REACT_APP_KEYCLOAK_CLIENT_ID=intellicare-portal
REACT_APP_API_URL=http://localhost:8000
```

---

## 🧪 TESTE

### 1. Iniciar o portal
```bash
cd C:\DOCSHARE\INTELLICARE\MODULARIZACAO\intellicare-portal\frontend
npm start
```

### 2. Acessar
```
http://localhost:3000
```

### 3. Resultado esperado
- ✅ Redirecionamento para Keycloak
- ✅ Login com `dr.silva@saudeplanner.com.br` / `Test@123`
- ✅ Redirecionamento de volta para o portal
- ✅ Token armazenado
- ✅ Requisições com Authorization header

---

## 📚 RECURSOS ADICIONAIS

- [Keycloak JavaScript Adapter](https://www.keycloak.org/docs/latest/securing_apps/#_javascript_adapter)
- [React Keycloak](https://github.com/react-keycloak/react-keycloak)
- [PKCE Flow](https://oauth.net/2/pkce/)

---

## 🎯 PRÓXIMOS PASSOS

1. ✅ Instalar keycloak-js
2. ✅ Criar configuração Keycloak
3. ✅ Inicializar no App
4. ✅ Criar interceptor HTTP
5. ✅ Criar AuthContext
6. ✅ Proteger rotas
7. ✅ Testar autenticação

**Boa sorte!** 🚀

