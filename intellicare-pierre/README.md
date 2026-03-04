# intellicare-pierre

Modulo PIERRE do ecossistema IntelliCare.

Responsavel por inteligencia externa para suporte clinico:
- busca web (Tavily)
- literatura medica (PubMed, BIREME, SciELO)
- verificacao regulatoria
- analise e sumarizacao de texto com LLM

API principal:
- `GET /api/v1/health`
- `GET /api/v1/info`
- `GET /api/v1/mcp/tools`
- `POST /api/v1/mcp/call`
