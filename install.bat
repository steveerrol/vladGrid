@echo off
echo Installing ES Trading Bot Dependencies...
echo.

REM Install Python dependencies
pip install -r requirements.txt

echo.
echo Installation complete!
echo.
echo Next steps:
echo 1. Start IBKR TWS or IB Gateway
echo 2. Enable API connections in TWS settings
echo 3. Run: python run_bot.py
echo.
pause
