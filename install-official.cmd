@echo off
chcp 65001 >nul
echo 艾丽妮 2.0.0 官方小人
echo 1. 默认
echo 2. 飞羽
echo 3. 至高判决
set "petSkin=default"
set /p "petChoice=输入 1、2 或 3，按回车使用默认："
if "%petChoice%"=="2" set "petSkin=synesthesia"
if "%petChoice%"=="3" set "petSkin=game"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-official.ps1" -Skin %petSkin%
pause
