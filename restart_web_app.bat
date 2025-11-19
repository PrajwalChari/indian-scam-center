@echo off
echo Stopping any running Streamlit processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Streamlit*" 2>nul
taskkill /F /IM python3.12.exe /FI "WINDOWTITLE eq Streamlit*" 2>nul
timeout /t 2 /nobreak >nul

cls
echo ========================================
echo   Indian Scam Center - Web Version
echo ========================================
echo.
echo Starting fresh web server...
echo The app will open in your browser at:
echo   http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.
timeout /t 2 /nobreak >nul
start http://localhost:8501
C:\Users\prajwv\AppData\Local\Microsoft\WindowsApps\python3.12.exe -m streamlit run web_app.py --server.headless=true
