@echo off
REM clean.bat - apaga out\ do projeto
if exist "%~dp0out\" rmdir /s /q "%~dp0out"
mkdir "%~dp0out"
echo [CLEAN OK] %~dp0out
