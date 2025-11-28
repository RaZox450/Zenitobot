@echo off
chcp 65001 >nul
echo ========================================
echo   CHECKPOINT COMPARISON TOOL
echo ========================================
echo.
python training\compare_checkpoints.py
pause
