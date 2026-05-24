@echo off
REM Install WebAI Chat as a Windows Scheduled Task (runs at login)
schtasks /Create /TN "WebAI Chat" /TR "C:\Opencode\Projects\W-Chatbot\WebAI-Chat\start-webaichat.bat" /RU %USERNAME% /SC ONLOGON /F
echo Scheduled task created. WebAI Chat will start on login.
