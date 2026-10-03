@echo off
title Atualizar do GitHub
cd /d "%~dp0"

echo Buscando as novidades no GitHub...
echo.
git pull
if errorlevel 1 goto erro

rem Junta o que o Claude enviou (so avanca; nunca mistura nem apaga nada seu)
git merge --ff-only origin/claude/stoic-bell-st8vmw
if errorlevel 1 goto erro

git push
if errorlevel 1 goto erro

echo.
echo Tudo atualizado!
pause
exit /b 0

:erro
echo.
echo Algo deu errado. Tire um print desta janela e mande para o Claude.
pause
exit /b 1
