"""FastAPI application bootstrap for intellicare-admin."""

from __future__ import annotations

import importlib
import logging
from typing import Any

from fastapi import FastAPI

logger = logging.getLogger(__name__)

app = FastAPI(
    title="IntelliCare Admin API",
    description="API para administracao da plataforma IntelliCare",
    version="1.0.0",
)


@app.get("/api/v1/health")
async def health() -> dict[str, Any]:
    """Liveness/readiness endpoint for container healthcheck."""
    return {"status": "healthy", "module": "intellicare-admin"}


from fastapi.responses import HTMLResponse

@app.get("/", include_in_schema=False)
async def admin_portal_root():
    """Admin Login Redirect frontend."""
    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>IntelliCare Admin</title>
        <script src="https://auth.intellicare.ia.br/js/keycloak.js"></script>
        <style>
            body { font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
            .card { background: #1e293b; padding: 2.5rem; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5); max-width: 500px; width: 100%; text-align: center; border: 1px solid #334155; }
            h2 { margin-top: 0; color: #38bdf8; }
            button { background: #0ea5e9; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 16px; margin-top: 15px; width: 100%; font-weight: bold; transition: background 0.2s; }
            button:hover { background: #0284c7; }
            .btn-danger { background: #ef4444; margin-top: 10px; }
            .btn-danger:hover { background: #dc2626; }
            pre { background: #0f172a; padding: 15px; border-radius: 6px; text-align: left; overflow-x: auto; font-size: 11px; margin-top: 20px; color: #a5b4fc; border: 1px solid #334155;}
            .roles { color: #f472b6; font-weight: bold; }
        </style>
    </head>
    <body onload="initKeycloak()">
        <div class="card" id="app">
            <h2>⚡ IntelliCare Admin</h2>
            <p style="color: #94a3b8;">Redirecionando para Autenticação Segura (SSO)...</p>
        </div>
        <script>
            var keycloak = new Keycloak({
                url: 'https://auth.intellicare.ia.br',
                realm: 'intellicare',
                clientId: 'intellicare-admin'
            });

            function initKeycloak() {
                keycloak.init({ onLoad: 'login-required', checkLoginIframe: false }).then(function(authenticated) {
                    if (authenticated) {
                        showProfile();
                    } else {
                        document.getElementById('app').innerHTML = '<h2>Falha na Autenticação</h2><p>Acesso negado.</p>';
                    }
                }).catch(function() {
                    document.getElementById('app').innerHTML = '<h2>Erro de Conexão</h2><p>Servidor Keycloak indisponível.</p>';
                });
            }

            function copyToken() {
                navigator.clipboard.writeText("Bearer " + keycloak.token);
                const btn = document.getElementById('copybtn');
                btn.innerText = "Token Copiado!";
                setTimeout(() => btn.innerText = "Copiar Bearer Token", 2000);
            }

            function showProfile() {
                const roles = keycloak.realmAccess ? keycloak.realmAccess.roles.join(', ') : 'Nenhuma';
                const name = keycloak.tokenParsed.name || keycloak.tokenParsed.preferred_username;
                const email = keycloak.tokenParsed.email || 'N/A';
                
                document.getElementById('app').innerHTML = `
                    <h2>🛡️ Painel Admin Conectado</h2>
                    <p style="margin-bottom: 5px;">Seja bem-vindo(a), <strong>${name}</strong></p>
                    <p style="margin-top: 0; font-size: 0.9em; color: #94a3b8;">${email}</p>
                    <p style="margin-top: 20px;">Perfil Nível Plataforma:<br> <span class="roles">${roles}</span></p>
                    
                    <button onclick="window.location.href='/api/v1/docs'">Acessar OpenAPI (Swagger)</button>
                    <button id="copybtn" onclick="copyToken()" style="background: #475569;">Copiar Bearer Token</button>
                    <button onclick="keycloak.logout()" class="btn-danger">Encerrar Sessão</button>
                `;
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/api/v1/info")
async def info() -> dict[str, Any]:
    """Minimal module metadata."""
    return {
        "module": "intellicare-admin",
        "version": "1.0.0",
        "description": "Platform administration module",
    }


from admin.api.tenant_routes import router as tenant_router
from admin.api.billing_routes import router as billing_router
from admin.api.audit_routes import router as audit_router
from admin.api.plan_routes import plan_router, dashboard_router
from admin.api.gestor_routes import router as gestor_router
from admin.api.contrato_routes import router as contrato_router

app.include_router(tenant_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(plan_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(gestor_router, prefix="/api/v1/admin")
app.include_router(contrato_router, prefix="/api/v1/admin")

