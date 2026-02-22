@echo off
echo ========================================
echo INICIANDO SERVIDOR INTELLICARE-DONABEDIAN
echo ========================================
echo.

cd /d %~dp0

echo.
echo Iniciando servidor na porta 8003...
echo URL: http://localhost:8003
echo Docs: http://localhost:8003/docs
echo.

python -m uvicorn src.donabedian.api.main:app --reload --port 8003 --host 0.0.0.0

pause

