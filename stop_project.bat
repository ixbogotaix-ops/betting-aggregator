@echo off
echo Stopping AI Sports Aggregator...

echo Stopping Backend (Uvicorn)...
wmic process where "commandline like '%%uvicorn app.main:app%%' and name!='wmic.exe'" call terminate >nul 2>&1

echo Stopping Frontend (Vite/Node)...
wmic process where "commandline like '%%npm run dev%%' and name!='wmic.exe'" call terminate >nul 2>&1
wmic process where "commandline like '%%vite%%' and name!='wmic.exe'" call terminate >nul 2>&1

echo All services stopped!
pause
