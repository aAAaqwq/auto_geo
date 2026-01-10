@echo off
chcp 65001 >nul
echo ========================================
echo   AutoGeo 智能发布助手
echo ========================================
echo.
echo 正在启动应用...
cd /d "%~dp0fronted"
start "" npm run dev
echo.
echo 应用正在启动，请稍候...
echo.
timeout /t 3 /nobreak >nul
echo 如果窗口没有自动打开，请检查控制台输出。
echo.
echo 按 Ctrl+C 可以停止应用
echo ========================================
pause
