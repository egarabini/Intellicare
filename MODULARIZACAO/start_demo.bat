@echo off
setlocal EnableExtensions
title IntelliCare Demo Launcher
color 0A

set "NO_PAUSE=0"
if /I "%~1"=="--no-pause" set "NO_PAUSE=1"
if /I "%INTELLICARE_NO_PAUSE%"=="1" set "NO_PAUSE=1"

echo ===================================================
echo   INTELLICARE PORTAL - DEMO LAUNCHER
echo ===================================================
echo.
echo Preconditions:
echo - Infrastructure up: docker-compose up -d
echo - Python deps installed per module virtual environment
echo.
echo Starting services...
echo.

echo [1/7] Starting Oswaldo (Chronic Care)...
call :launch_python_service "IntelliCare - Oswaldo (8002)" "intellicare-oswaldo" "-m src.oswaldo.api.main" "import src.oswaldo.api.main"

echo [2/7] Starting Florence (Lab Analysis)...
call :launch_python_service "IntelliCare - Florence (8001)" "intellicare-florence" "run_api_8001.py" "import run_api_8001"

echo [3/7] Starting Geralda (Primary Care)...
call :launch_python_service "IntelliCare - Geralda (8006)" "intellicare-geralda" "run_api_8006.py" "import run_api_8006"

echo [4/7] Starting Nise (Orchestration)...
call :launch_python_service "IntelliCare - Nise (8000)" "intellicare-nise" "run_api_lite.py" "import run_api_lite"

echo [5/7] Starting Zilda (Public Health)...
call :launch_python_service "IntelliCare - Zilda (8003)" "intellicare-zilda" "run_api_lite.py" "import run_api_lite"

echo [6/7] Starting Grahame (FHIR Mock)...
call :launch_python_service "IntelliCare - Grahame (8004)" "intellicare-grahame" "run_api_lite.py" "import run_api_lite"

echo [7/7] Starting Portal Frontend...
call :launch_frontend "IntelliCare - Portal (Frontend)" "intellicare-portal\\frontend"

echo.
echo ===================================================
echo   ALL SERVICES REQUESTED
echo ===================================================
echo.
echo Access the portal at: http://localhost:5173
echo.
if "%NO_PAUSE%"=="1" (
  exit /b 0
)
pause
exit /b 0

:launch_python_service
set "WINDOW_TITLE=%~1"
set "MODULE_DIR=%~2"
set "RUN_ARGS=%~3"
set "IMPORT_CHECK=%~4"
set "PYTHON_EXE=python"

if exist "%MODULE_DIR%\.venv39\Scripts\python.exe" (
  set "PYTHON_EXE=.venv39\Scripts\python.exe"
) else if exist "%MODULE_DIR%\.venv\Scripts\python.exe" (
  set "PYTHON_EXE=.venv\Scripts\python.exe"
) else if exist "%MODULE_DIR%\venv\Scripts\python.exe" (
  set "PYTHON_EXE=venv\Scripts\python.exe"
) else (
  echo [WARN] %MODULE_DIR% sem .venv/venv; usando python global.
)

if not "%PYTHON_EXE%"=="python" (
  if "%IMPORT_CHECK%"=="" (
    set "IMPORT_CHECK=import fastapi,uvicorn"
  )
  cmd /c "cd /d %MODULE_DIR% && %PYTHON_EXE% -c \"%IMPORT_CHECK%\"" >nul 2>&1
  if errorlevel 1 (
    echo [WARN] %MODULE_DIR% venv sem runtime valido; fallback para python global.
    set "PYTHON_EXE=python"
  )
)

start "%WINDOW_TITLE%" cmd /k "cd /d %MODULE_DIR% && %PYTHON_EXE% %RUN_ARGS%"
goto :eof

:launch_frontend
set "WINDOW_TITLE=%~1"
set "FRONTEND_DIR=%~2"
where npm >nul 2>&1
if errorlevel 1 (
  echo [ERROR] npm nao encontrado no PATH. Instale Node.js 18+.
  goto :eof
)
start "%WINDOW_TITLE%" cmd /k "cd /d %FRONTEND_DIR% && npm run dev"
goto :eof
