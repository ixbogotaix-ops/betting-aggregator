Set WshShell = CreateObject("WScript.Shell")

' Запускаем бэкенд скрыто (0 = Hide window)
WshShell.Run "cmd /c cd /d d:\AI\BK\betting_aggregator\backend && venv\Scripts\activate && uvicorn app.main:app", 0, False

' Ждем 3 секунды
WScript.Sleep 3000

' Запускаем фронтенд скрыто
WshShell.Run "cmd /c cd /d d:\AI\BK\betting_aggregator\frontend && npm run dev", 0, False

' Открываем браузер
WshShell.Run "http://localhost:3000", 1, False
