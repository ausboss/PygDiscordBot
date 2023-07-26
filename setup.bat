@echo off

REM Set the console window size to 80 columns by 25 lines
mode con lines=25

echo ===========================================
echo S E T T I N G   U P   E N V I R O N M E N T
echo ===========================================

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
python -m venv venv



rem Activate the virtual environment
call venv\Scripts\activate

rem Install the required packages
pip install -r requirements.txt
pip install torch==1.12.1+cu116 torchvision==0.13.1+cu116 --extra-index-url https://download.pytorch.org/whl/cu116
pip install --upgrade transformers
rem clear console
cls

rem echo Set up Complete 
rem echo Configure your .env file then launch run.bat
rem echo or run using "python discordbot.py <DISCORD_BOT_TOKEN> <ENDPOINT> <CHANNEL_ID>"

REM Check if .env file exists
if not exist .env (
    echo ===========================================
	echo         S E T U P     C O M P L E T E
	echo ===========================================
	echo.
	echo Configure your .env file then launch run.bat
	echo.
	echo or run using "python discordbot.py"
    pause
    exit /b
)

REM load the virtual environment
call venv\Scripts\activate



REM Run the Python script with the environment variables as arguments
python discordbot.py


pause
