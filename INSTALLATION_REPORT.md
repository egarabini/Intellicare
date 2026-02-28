# IntelliCare . - Installation Report

## Installation Date
2026-02-24

## Prerequisites Check
- Python: 3.14.0 ✓
- Node.js: v24.11.1 ✓
- Docker: 28.4.0 ✓
- Docker Compose: v2.39.2 ✓

## Successfully Installed Modules

### Core SDK
- ✓ intellicare-core - Shared SDK and contracts

### Agent Modules
- ✓ intellicare-wanda - Central orchestrator
- ✓ intellicare-donabedian - Quality assessment
- ✓ intellicare-comunicacao - Notifications (Rocket.Chat, WhatsApp, etc.)
- ✓ intellicare-geralda - Patient accompaniment
- ✓ intellicare-zilda - Brazilian public health data
- ✓ intellicare-nise - Chatbot + Flowise orchestration
- ✓ intellicare-grahame - FHIR R4 interop
- ✓ intellicare-gestor - Multi-tenant RBAC
- ✓ intellicare-pierre - Scientific search (MCP Server)

### Frontend
- ✓ intellicare-portal (frontend) - React 19 + Vite portal

## Modules Requiring Visual Studio C++ Build Tools

The following modules require C++ compilation and could not be installed:

- ✗ intellicare-auth - Keycloak/SMART-on-FHIR integration (requires asyncpg)
- ✗ intellicare-admin - Admin panel (Poetry configuration issue)
- ✗ intellicare-florence - Lab analysis, RAG (requires asyncpg, chroma-hnswlib, tiktoken)
- ✗ intellicare-oswaldo - Chronic disease engine (requires asyncpg)
- ✗ intellicare-ocr - OCR + doc extraction (requires C++ build tools)

## How to Install Remaining Modules

### Option 1: Install Visual Studio (Recommended)

1. Download Visual Studio 2022 Community (free): https://visualstudio.microsoft.com/downloads/
2. During installation, select "Desktop development with C++" workload
3. Re-run the installation script

### Option 2: Install Pre-built Wheels

Some packages may have pre-built wheels available:

```bash
pip install asyncpg chroma-hnswlib tiktoken
```

Then install the modules individually.

## Quick Start Commands

### 1. Start Infrastructure Services
```bash
docker compose up -d
```

### 2. Run a Module (Example - Wanda)
```bash
cd intellicare-wanda
.venv\Scripts\activate
uvicorn wanda.api.app:app --reload --port 8004
```

### 3. Run Frontend
```bash
cd intellicare-portal\frontend
npm run dev
```

### 4. Run Health Checks
```bash
python scripts/smoke_tests.py
```

### 5. Run All Services with Docker
```bash
docker compose -f docker-compose.full.yml up -d
```

## Module Ports Reference

| Port | Module | Agent Name |
|------|--------|------------|
| 8004 | intellicare-wanda | WANDA |
| 8003 | intellicare-donabedian | DONABEDIAN |
| 8005 | intellicare-comunicacao | — |
| 8006 | intellicare-geralda | GERALDA |
| 8007 | intellicare-zilda | ZILDA |
| 8011 | intellicare-gestor | — |
| 8012 | intellicare-grahame | GRAHAME |
| 8013 | intellicare-nise | NISE |
| 8009 | intellicare-pierre | PIERRE |
| 3000/5173 | intellicare-portal | — |

## Notes

- All installed modules use Python virtual environments (.venv directory in each module)
- The frontend is installed in intellicare-portal/frontend/node_modules
- Each module can be run independently using the commands above
- Docker Compose configurations are available for running all services together

## Installation Scripts

The following installation scripts were created:

- `install.sh` - Bash script for Unix/Linux/macOS (with Windows Git Bash adaptations)
- `install.ps1` - PowerShell script for Windows
- `install-simple.ps1` - Simplified PowerShell script that skips modules requiring C++ build tools

To re-run installation:
```bash
# Windows PowerShell
powershell.exe -ExecutionPolicy Bypass -File install-simple.ps1

# Windows Git Bash
bash install.sh
```

