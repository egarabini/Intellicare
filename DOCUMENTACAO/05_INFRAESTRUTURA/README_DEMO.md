# 🏥 IntelliCare Portal - Demo Guide

Welcome to the **IntelliCare** modular platform demo. This environment demonstrates the integration of multiple specialized healthcare modules into a unified portal.

## 🚀 Quick Start (One-Click)

1.  Start infrastructure in this directory:
    - `docker-compose up -d`
2.  Ensure each Python module has its own virtual environment:
    - `powershell -ExecutionPolicy Bypass -File .\setup_demo_venvs.ps1`
3.  Install module dependencies inside each virtual environment.
4.  **Double-click** `start_demo.bat`.
5.  Wait for all 7 terminal windows to open and initialize (6 backends + portal).
6.  Access the Portal at: **http://localhost:5173**

---

## 🧩 Active Modules

### 1. **OSWALDO (Chronic Care)**
   - **Focus**: Diabetes & Hypertension management.
   - **Demo**: Select the Oswaldo card and input a Creatinine value (e.g., `1.8`) to see CKD Staging calculation.

### 2. **FLORENCE (Lab Analysis)**
   - **Focus**: Intelligent validation of laboratory results.
   - **Demo**: Use the Florence module to validate Hemogram results. Try changing "Hematócrito" to an abnormal value (e.g., `30`) to trigger a validation error.

### 3. **GERALDA (Primary Care)**
   - **Focus**: Care Plans & Longitudinal tracking.
   - **Demo**: View the interactive timeline of daily tasks and the adherence chart. Click tasks to toggle their status.

### 4. **NISE (Orchestration)**
   - **Focus**: Process Orchestration & Chatbot.
   - **Demo**: 
     - **Workflow Monitor**: See active processes (simulated).
     - **Dr. Nise**: Chat with the assistant (try asking "Qual o resumo do paciente?").
     - **Trigger**: Click "Simular Alerta" to fire a new workflow.

### 5. **ZILDA (Public Health)**
   - **Focus**: National Health Data (CNES/DATASUS).
   - **Demo**: Search for health establishments and view territorial context data for São Paulo.

### 6. **GRAHAME (FHIR Interop)**
   - **Focus**: Standardization & Interoperability (HL7 FHIR).
   - **Demo**: Inspect raw JSON resources for Patients and Observations.

---

## 🛠️ Troubleshooting

- **Ports in use?**
  - Ensure ports `8000`, `8001`, `8002`, `8003`, `8004`, `8006`, and `5173` are free.
- **Backend fails to start?**
  - Check the specific terminal window for error messages.
  - Ensure you have dependencies installed in that module virtual environment (`.venv` or `venv`).
  - The launcher attempts `\.venv39`, `\.venv`, `\venv` and falls back to global `python` if runtime import check fails.
- **Need to stop everything quickly?**
  - Run `kill_demo.bat`.
- **Quick smoke test after startup**
  - Run `powershell -ExecutionPolicy Bypass -File .\check_demo_health.ps1`

## 📦 Architecture

- **Frontend**: React + Vite + TailwindCSS
- **Backends**: Python FastAPI (Microservices)
- **Communication**: REST API (Direct calls for demo)
