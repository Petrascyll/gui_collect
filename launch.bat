@echo off
setlocal enabledelayedexpansion

py --version >nul 2>&1
if %errorlevel% == 0 (
    for /f "tokens=2 delims= " %%A in ('py --version 2^>^&1') do set "ver=%%A"
    call :run_script py
    goto end
)

python --version >nul 2>&1
if %errorlevel% == 0 (
    for /f "tokens=2 delims= " %%A in ('python --version 2^>^&1') do set "ver=%%A"
    call :run_script python
    goto end
)

echo Python not found!
pause
goto end

:run_script
for /f "tokens=1,2 delims=." %%A in ("%ver%") do (
    set "major=%%A"
    set "minor=%%B"
)

if !major! EQU 3 if !minor! GTR 8 (
    %1 --version
    %1 ./collect.py
    goto :eof
) else (
    echo You must have at least Python 3.9 installed! 
    pause
)

:end
