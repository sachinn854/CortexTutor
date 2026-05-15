@echo off
echo Starting CortexTutor backend...
cd /d "%~dp0backend"
set PYTHONUTF8=1
call ..\venv\Scripts\activate.bat 2>nul || call venv\Scripts\activate.bat 2>nul
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
