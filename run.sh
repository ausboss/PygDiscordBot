#!/bin/bash

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
echo "Installing required packages..."
pip install -r requirements.txt

# run the python code
echo "Starting the bot..."
python run.py
