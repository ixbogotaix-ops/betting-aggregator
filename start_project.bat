@echo off
title AI Sports Aggregator Launcher
echo =========================================
echo   Starting AI Sports Aggregator...
echo =========================================
echo.

echo [1/3] Checking for running instances and stopping them...
taskkill /F /IM uvicorn.exe /T >nul 2>&1
wmic process where "name='python.exe' and commandline like '%%uvicorn%%'" call terminate >nul 2>&1
wmic process where "name='node.exe' and commandline like '%%vite%%'" call terminate >nul 2>&1
wmic process where "name='node.exe' and commandline like '%%npm%%'" call terminate >nul 2>&1
echo       Done! Previous instances cleared.
echo.

echo [2/3] Launching services in the background...
wscript.exe start_hidden.vbs
echo       Done! No extra black windows will appear.
echo.

echo [3/3] Opening browser in 3 seconds...
timeout /t 3 >nul

echo.
echo All good! You can close this window.
exit
