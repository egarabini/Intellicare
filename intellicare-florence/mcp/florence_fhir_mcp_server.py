# florence_fhir_mcp_server.py — MCP Server para Florence (FHIR)
# Baseado em FHIR-AgentEval:environment/mcp/baseline_server/fhir_mcp_server.py
# Adaptação inicial: 2026-02-17

import os, sys, argparse, asyncio, logging, json
from typing import Any, Optional, Dict, List, Annotated

import httpx
from pydantic import Field, BaseModel, ConfigDict
from fastmcp import FastMCP
import jwt  # PyJWT para autenticação JWT

# Logging
LOG_LEVEL = os.getenv("MCP_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("florence-mcp")

# Configuração do endpoint FHIR
DEFAULT_FHIR_BASE = os.getenv("FLORENCE_FHIR_BASE_URL", "http://localhost:7070/fhir")
MCP_SECRET = os.getenv("MCP_JWT_SECRET", "changeme")  # Segredo JWT para dev
mcp = FastMCP(name="florence-fhir")

# --- Autenticação JWT ---
def validate_jwt(token: str) -> bool:
    try:
        payload = jwt.decode(token, MCP_SECRET, algorithms=["HS256"])
        return True
    except Exception as e:
        log.warning(f"JWT inválido: {e}")
        return False

def require_auth(headers: Dict[str, str]) -> None:
    auth = headers.get("authorization") or headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise Exception("Token JWT ausente ou malformado")
    token = auth.split(" ", 1)[1]
    if not validate_jwt(token):
        raise Exception("Token JWT inválido")

# --- Helpers HTTP ---
def base_url_or_default(base_url: Optional[str]) -> str:
    return (base_url or DEFAULT_FHIR_BASE).rstrip("/")

async def json_request(
    method: str,
    url: str,
    *,
    headers: Dict[str, str] | None = None,
    json: Any | None = None,
    require_authentication: bool = True,
) -> Dict[str, Any]:
    base_headers = {"Accept": "application/fhir+json"}
    if json is not None:
        base_headers["Content-Type"] = "application/fhir+json"
    if headers:
        base_headers.update(headers)
    # Autenticação
    if require_authentication:
        require_auth(base_headers)
    if method == "GET":
        base_headers["Cache-Control"] = "no-cache"
    log.debug("HTTP %s %s headers=%s", method, url, base_headers or {})
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        resp = await client.request(method, url, headers=base_headers, json=json)
        log.info("HTTP %s %s -> %s", method, url, resp.status_code)
        text = resp.text or ""
        parsed = None
        try:
            parsed = resp.json()
        except Exception:
            parsed = None
        if 200 <= resp.status_code < 300:
            return parsed if isinstance(parsed, dict) else {}
        err: Dict[str, Any] = {
            "error": "HTTP_ERROR",
            "status": resp.status_code,
            "method": method,
            "url": str(resp.request.url if resp.request else url),
        }
        if isinstance(parsed, dict) and parsed.get("resourceType") == "OperationOutcome":
            issues = parsed.get("issue", []) or []
            diagnostics = "; ".join(i.get("diagnostics", "") for i in issues if i.get("diagnostics"))
            codes = ", ".join(i.get("code", "") for i in issues if i.get("code"))
            first_expr = None
            for i in issues:
                expr = i.get("expression") or []
                if expr:
                    first_expr = expr[0]
                    break
            err.update({
                "error": "OPERATION_OUTCOME",
                "operationOutcome": parsed,
                "diagnostics": diagnostics or None,
                "issue_codes": codes or None,
                "issue_count": len(issues),
                "first_expression": first_expr,
            })
        else:
            err["body_excerpt"] = text[:3000]
        log.error("HTTP error %s %s: %s | %s", method, url, err.get("error"), err.get("diagnostics") or err.get("body_excerpt", "")[:240])
        return err

# ... (demais MCP tools: listResourceTypes, getResourceById, searchResources, createResource, updateResource, deleteResource)
# ... (copiar/adaptar do fhir_mcp_server.py, mantendo assinatura e lógica, mas usando base_url_or_default e json_request)

# --- Main ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true", help="Rodar teste rápido de conectividade FHIR.")
    parser.add_argument("--base-url", default=DEFAULT_FHIR_BASE, help="FHIR base URL para selftest e tools.")
    parser.add_argument("--host", default="0.0.0.0", help="Host HTTP para SSE.")
    parser.add_argument("--port", type=int, default=8000, help="Porta HTTP para SSE.")
    parser.add_argument("--path", default="/florence_mcp", help="Path HTTP para endpoint SSE.")
    args = parser.parse_args()
    DEFAULT_FHIR_BASE = args.base_url
    log.info("Iniciando MCP SSE server em http://%s:%d%s (FHIR=%s)", args.host, args.port, args.path, DEFAULT_FHIR_BASE)
    mcp.run(transport="sse", host=args.host, port=args.port, path=args.path)
