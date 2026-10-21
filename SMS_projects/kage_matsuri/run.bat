@echo off
REM run.bat - abre a ROM no emulador gate
if not exist "%~dp0out\rom\" (echo [FAIL] rode build.bat primeiro & exit /b 1)
for %%F in ("%~dp0out\rom\*.sms") do set ROM=%%F
if not defined ROM (echo [FAIL] nenhuma .sms em out\rom & exit /b 1)
echo [RUN] %ROM%
"%ROM%"
