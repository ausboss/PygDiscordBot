@echo off
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
    exit /b 1
)

REM Load environment variables from .env file
for /f "delims=" %%a in ('type .env') do set "%%a"

REM Run the Python script with the environment variables as arguments
python discordbot.py %DISCORD_BOT_TOKEN% %ENDPOINT% %CHANNEL_ID%

endlocal
