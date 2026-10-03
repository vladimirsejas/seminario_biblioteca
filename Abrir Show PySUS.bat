@echo off
title Show de gestos - PySUS
cd /d "%~dp0"

rem Na primeira vez neste computador, prepara o ambiente do show sozinho
if not exist "venv_gestos\Scripts\python.exe" (
    echo Primeira vez neste computador: preparando o show.
    echo Isso leva alguns minutos e precisa de internet...
    echo.
    py -3.12 -m venv venv_gestos
    if errorlevel 1 (
        echo.
        echo Nao encontrei o Python 3.12. Instale pelo site python.org e tente de novo.
        pause
        exit /b 1
    )
    venv_gestos\Scripts\python.exe -m pip install -r gestos\requirements.txt
    if errorlevel 1 (
        echo.
        echo A instalacao falhou. Confira a internet e de dois cliques de novo.
        rmdir /s /q venv_gestos
        pause
        exit /b 1
    )
)

echo Abrindo o show... a janela aparece em alguns segundos.
echo (Pode deixar esta janela preta aberta: ela fecha sozinha quando o show acabar.)
venv_gestos\Scripts\python.exe gestos\show_gestos.py
if errorlevel 1 pause
