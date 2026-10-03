@echo off
title Terminal PySUS - versao 1
cd /d "%~dp0"

rem Na primeira vez neste computador, prepara o ambiente do terminal sozinho
if not exist "venv\Scripts\python.exe" (
    echo Primeira vez neste computador: preparando o terminal.
    echo Isso leva alguns minutos e precisa de internet...
    echo.
    py -3.12 -m venv venv
    if errorlevel 1 (
        echo.
        echo Nao encontrei o Python 3.12. Instale pelo site python.org e tente de novo.
        pause
        exit /b 1
    )
    venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo A instalacao falhou. Confira a internet e de dois cliques de novo.
        rmdir /s /q venv
        pause
        exit /b 1
    )
)

venv\Scripts\python.exe main.py
pause
