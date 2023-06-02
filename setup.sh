#!/bin/bash
git pull
# check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# activate the virtual environment
source venv/bin/activate

# check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "requirements.txt not found, exiting..."
    exit 1
fi

# install required packages
# Specific versions were removed because they were causing issues for me and I'm too lazy to figure out what
echo "Installing required packages..."
pip install -r requirements.txt
pip install --upgrade transformers

# run the python code
echo "Starting the bot..."
# Run the Python script with the environment variables as arguments
python discordbot.py
