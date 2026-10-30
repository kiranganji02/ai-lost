@echo off
echo ====================================================
echo   AI Lost ^& Found Object Matching System
echo ====================================================
echo.

REM Check if database exists, if not seed with demo data
if not exist "data\lost_found.db" (
    echo [INFO] First run - seeding demo data...
    python seed.py
    echo.
)

echo [INFO] Starting server at http://localhost:8000
echo [INFO] Press Ctrl+C to stop.
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
