@echo off
echo =========================================================
echo Starting Hyper Video Studio on Windows
echo =========================================================

if not exist node_modules\puppeteer-core (
    echo Installing node dependencies...
    call npm install
)

python core\sfx_generator.py
echo Opening Dashboard at http://localhost:8585
python dashboard\server.py
pause
