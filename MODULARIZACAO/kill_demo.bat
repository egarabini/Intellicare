@echo off
title IntelliCare Demo Killer
color 0C

echo ===================================================
echo   STOPPING INTELLICARE SERVICES
echo ===================================================
echo.

echo Killing processes on port 8000 (Nise)...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo Killing processes on port 8001 (Florence)...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8001" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo Killing processes on port 8002 (Oswaldo)...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8002" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo Killing processes on port 8003 (Zilda)...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8003" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo Killing processes on port 8004 (Grahame)...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8004" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo Killing processes on port 8006 (Geralda)...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8006" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo Killing processes on port 5173 (Portal)...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5173" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo.
echo ===================================================
echo   ALL SERVICES STOPPED!
echo ===================================================
echo.
pause
