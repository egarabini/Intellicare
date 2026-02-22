@echo off
echo ========================================
echo TESTES DE INTEGRACAO KEYCLOAK
echo ========================================
echo.

cd /d %~dp0

echo.
echo Executando testes...
echo.

python test_keycloak_integration.py

pause

