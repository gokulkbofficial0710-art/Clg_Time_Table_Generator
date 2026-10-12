@echo off
title Push to GitHub: timetable

cd /d "%~dp0"
set PATH=C:\laragon\bin\git\cmd;%PATH%

echo =====================================================================
echo   Pushing College Exam Timetable Generator to GitHub
echo   Repository: https://github.com/gokulkbofficial0710-art/timetable.git
echo =====================================================================
echo.

git push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo -----------------------------------------------------------------
    echo If authentication failed:
    echo 1. Enter your GitHub Personal Access Token (PAT) as the password.
    echo    (Create one at: https://github.com/settings/tokens)
    echo 2. Or sign in using the GitHub Web Browser prompt.
    echo -----------------------------------------------------------------
) else (
    echo.
    echo =================================================================
    echo [SUCCESS] Code successfully pushed to GitHub!
    echo Now go to https://railway.com and deploy from your repository.
    echo =================================================================
)

echo.
pause
