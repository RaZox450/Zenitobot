@echo off
echo ============================================================
echo TEST DE CONFIGURATION - ZENITOBOT RECHERCHE
echo ============================================================
echo.

REM Vérifie Python
echo [1/4] Verification Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python non trouve
    echo     Installe Python 3.8+ depuis https://www.python.org/
    goto :error
) else (
    python --version
    echo [OK] Python trouve
)
echo.

REM Vérifie les dépendances
echo [2/4] Verification dependances...
python -c "import psutil" >nul 2>&1
if errorlevel 1 (
    echo [!] psutil manquant
    echo     Installation: pip install psutil
    goto :error
)
echo [OK] psutil disponible

python -c "import vgamepad" >nul 2>&1
if errorlevel 1 (
    echo [!] vgamepad manquant
    echo     1. Installe ViGEmBus: https://github.com/ViGEm/ViGEmBus/releases
    echo     2. Puis: pip install vgamepad
    goto :error
)
echo [OK] vgamepad disponible

python -c "import torch" >nul 2>&1
if errorlevel 1 (
    echo [!] PyTorch manquant
    echo     Installation: pip install torch
    goto :error
)
echo [OK] PyTorch disponible
echo.

REM Test du memory reader
echo [3/4] Test du memory reader...
python memory_reader.py
echo.

REM Test du contrôleur virtuel
echo [4/4] Test du controleur virtuel...
echo.
echo ATTENTION: Ce test va simuler des inputs de manette pendant 5 secondes.
echo Si Rocket League est ouvert, tu verras le bot bouger!
echo.
pause

python input_simulator.py
echo.

echo ============================================================
echo CONFIGURATION TERMINEE
echo ============================================================
echo.
echo Prochaines etapes:
echo 1. Configure les offsets dans memory_reader.py (voir README_RESEARCH.md)
echo 2. Lance Rocket League
echo 3. Cree un match prive
echo 4. Lance: python online_bot.py
echo.
goto :end

:error
echo.
echo ============================================================
echo ERREUR DE CONFIGURATION
echo ============================================================
echo Consulte README_RESEARCH.md pour les instructions detaillees
pause
exit /b 1

:end
pause
