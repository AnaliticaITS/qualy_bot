@echo off
set logfile="logs\qualy_bat_log.txt"
echo Script started at %date% %time% > %logfile%

REM Cambiar al directorio de trabajo
cd C:\Users\gmunoz02\OneDrive - ITS InfoCom\ANALITICA ITS\QUALY BOT\Qualy
echo Changed directory to %cd% >> %logfile%

REM Ejecutar el script del bot desde el entorno virtual
echo Running qualy.py... >> %logfile%
pipenv run python qualy.py qualy.py >> %logfile% 2>&1

echo Script finished at %date% %time% >> %logfile%
