@echo off
chcp 65001 > nul
echo ========================================================
echo   Синхронизация локального кода с сервером play2go.cloud
echo ========================================================
backend\venv\Scripts\python sync_to_server.py
pause
