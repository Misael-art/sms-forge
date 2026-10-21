@echo off
REM Delega ao wrapper. Logica de build NUNCA no projeto.
python "%~dp0..\..\tools\sms_wrapper\build_inner.py" --project "%~dp0." %*
