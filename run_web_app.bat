@echo off
cls
echo ========================================
echo   Indian Scam Center - Web Version
echo ========================================
echo.
echo Starting web server...
echo The app will open in your browser at:
echo   http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.
timeout /t 2 /nobreak >nul
start http://localhost:8501
C:\Users\prajwv\AppData\Local\Microsoft\WindowsApps\python3.12.exe -m streamlit run web_app.py --server.headless=true
