@echo off
cd /d %~dp0
call venv\Scripts\activate.bat
python manage.py send_scheduled_messages
deactivate 