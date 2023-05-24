#!/bin/bash

# activate the virtual environment
source venv/bin/activate

# Load environment variables from .env file
while read -r line || [[ -n "$line" ]]; do
  export "$line"
done < .env

# Run the Python script with the environment variables as arguments
python discordbot.py $DISCORD_BOT_TOKEN $ENDPOINT $CHANNEL_ID
