@echo off
setlocal

REM Load environment variables from .env file
for /f "delims=" %%a in ('type .env') do set "%%a"

REM Run the Python script with the environment variables as arguments
python discordbot.py %DISCORD_BOT_TOKEN% %ENDPOINT% %CHANNEL_ID%

endlocal