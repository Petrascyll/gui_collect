@echo off

@REM Behold, possibly the laziest but simplest approach to
@REM learn if the minimum required python version is available
@REM and to run the collect script using it

@REM Try every single python version starting from 3.13 to 3.9
set "valid-python-version-list=3.13 3.12 3.11 3.10 3.9"
set "python-version=0"

@REM https://stackoverflow.com/a/40192472
@REM    "Whenever Windows command interpreter encounters
@REM    ( being interpreted as begin of a command block,
@REM    it parses the entire command block up to matching ) 
@REM    marking end of the command block and replaces all
@REM    %variable%  by current value of the variable
@REM    ... Delayed variable expansion is needed for variables set or 
@REM    modified and referenced within same command block..."
setlocal EnableDelayedExpansion

(for %%v in (%valid-python-version-list%) do (
    py -%%v --version >nul 2>&1
    if !errorlevel! == 0 (
        set "python-version=%%v"
        goto run-script
    )
))

echo You must have at least Python 3.9 installed! 
pause
goto end

:run-script
py -%python-version% --version
py -%python-version% ./collect.py

:end
