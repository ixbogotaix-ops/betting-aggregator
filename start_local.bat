@echo off
chcp 65001 > nul
echo =======================================================
echo   Запуск локальной версии Betting Aggregator (AI 2.0)
echo =======================================================
echo.

cd /d "%~dp0"

echo [*] Запуск бэкенда FastAPI (порт 8000)...
start "Betting Backend" cmd /k "cd backend && venv\Scripts\activate && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 2 /nobreak > nul

echo [*] Запуск фронтенда Vite React (порт 3000)...
start "Betting Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo =======================================================
echo   Все сервисы запущены!
echo   Бэкенд API:  http://127.0.0.1:8000
echo   Фронтенд UI: http://localhost:3000
echo =======================================================
echo.
pause
