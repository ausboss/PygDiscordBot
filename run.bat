@echo off

REM Set the console window size to 80 columns by 25 lines
mode con lines=25

REM Check if .env file exists
if not exist .env (
    @echo on
    cls
    @echo.
    @echo.
    @echo.
    echo *********************************************************************
    echo Error: .env file not found
    echo Please configure sample.env with your parameters and save it as .env
    echo *********************************************************************
    @echo.
    @echo.
    pause
    exit /b 1
)

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Load environment variables from .env file
for /f "delims=" %%a in ('type .env') do set "%%a"

REM Run the Python script with the environment variables as arguments
python discordbot.py

REM Deactivate the virtual environment
call venv\Scripts\deactivate.bat

pause
