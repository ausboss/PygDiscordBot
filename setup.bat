@echo off
git pull
rem Check if python is installed
where python
if %errorlevel% neq 0 (
    echo Python is not installed on this computer. Please install Python and run this script again.
    pause
    exit /b
)

rem Check if virtualenv is installed
pip show virtualenv
if %errorlevel% neq 0 (
    echo virtualenv is not installed on this computer. Installing virtualenv...
    pip install virtualenv
)

rem Create the virtual environment
virtualenv venv



rem Activate the virtual environment
call venv\Scripts\activate

rem Install the required packages
pip install -r requirements.txt
pip install torch==1.12.1+cu116 torchvision==0.13.1+cu116 --extra-index-url https://download.pytorch.org/whl/cu116
pip install --upgrade transformers
rem clear console
cls
echo Set up Complete 
echo Configure your .env file then launch run.bat
echo or run using "python discordbot.py <DISCORD_BOT_TOKEN> <ENDPOINT> <CHANNEL_ID>"

pause
