@echo off
echo Iniciando servidor Flask...
start /MIN cmd /k "python iniciar.py"

timeout /t 5 >nul

echo Iniciando ngrok...
start /MIN cmd /k "ngrok http 5000"
