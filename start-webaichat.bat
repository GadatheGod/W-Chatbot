@echo off
REM WebAI Chat Startup Script
cd /d "%~dp0"
call venv\Scripts\activate
python -m webaichat serve --port 13700
pause
