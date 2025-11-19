@echo off
echo Removing unnecessary files...
echo.

REM Remove documentation files that aren't needed for deployment
del /Q "CONVERSION_SUMMARY.md" 2>nul
del /Q "DEPLOYMENT_GUIDE.md" 2>nul
del /Q "DEPLOYMENT_STEPS.md" 2>nul
del /Q "QUICK_DEPLOY.md" 2>nul
del /Q "READY_TO_DEPLOY.md" 2>nul
del /Q "START_HERE.md" 2>nul
del /Q "SYSTEM_READY.md" 2>nul
del /Q "UI_MATCHING_COMPLETE.md" 2>nul
del /Q "WEB_VERSION_README.md" 2>nul
del /Q "SPONSORSHIP_SETUP.md" 2>nul

REM Remove desktop-only files (not needed for web version)
del /Q "Indian_Scam_Software.py" 2>nul
del /Q "launcher.py" 2>nul
del /Q "email_search_gui.py" 2>nul
del /Q "modern_gui.py" 2>nul
del /Q "example.py" 2>nul
del /Q "demo.py" 2>nul

REM Remove batch files for local testing
del /Q "run_web_app.bat" 2>nul
del /Q "restart_web_app.bat" 2>nul

REM Remove secrets template (not needed on GitHub)
del /Q ".streamlit\secrets.toml.template" 2>nul

echo.
echo Done! Removed unnecessary files.
echo.
echo Files kept:
echo - web_app.py (main web application)
echo - main_windows.py (email searcher backend)
echo - requirements.txt (dependencies)
echo - README.md (documentation)
echo - .gitignore (git configuration)
echo - .streamlit\config.toml (theme configuration)
echo - Procfile (for Heroku deployment)
echo.
pause
