# a quick implementation of a discord bot
import discord
import requests
import json
import os
from dotenv import load_dotenv
# get .env variables
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
ENDPOINT = os.getenv("ENDPOINT")
BOT_NAME = os.getenv("BOT_NAME")

# set to True if you want various data printed to the console for debugging
DEBUG = True
# Initialize the discord client
intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)
BOT_NAME = ""
BOT_PERSONALITY = BOT_NAME + "'s Persona: A virtual AI partner. Loving, caring, and always willing to make you happy.\n"
CONVERSATION_HISTORY = ""
@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    global CONVERSATION_HISTORY
    message_text = message.content
    if DEBUG:
        print(f"message sent:{message_text}")
    CONVERSATION_HISTORY += f"You: {message_text}\n"
    # Add the user input to the conversation history
    # Define the prompt

    prompt = {
        "prompt": BOT_PERSONALITY + CONVERSATION_HISTORY,
        'use_story': False,
        'use_memory': False,
        'use_authors_note': False,
        'use_world_info': False,
        'max_context_length': 1818,
        'max_length': 50,
        'rep_pen': 1.03,
        'rep_pen_range': 1024,
        'rep_pen_slope': 0.9,
        'temperature': 0.98,
        'tfs': 0.9,
        'top_a': 0,
        'top_k': 0,
        'top_p': 0.9,
        'typical': 1,
        'sampler_order': [
            6, 0, 1, 2,
            3, 4, 5
        ]
    }
    if DEBUG:
        print(json.dumps(prompt, indent=4))
    # Send a post request to the API endpoint
    response = requests.post(f"{ENDPOINT}/api/v1/generate", json=prompt)
    # Check if the request was successful
    if response.status_code == 200:
        # Get the results from the response
        results = response.json()['results']
        # Print the results for debug
        if DEBUG:
            print(results)
        for result in results:
            if "\n" in result['text']:
                print(result['text'])
                response_text = result['text'].split("\n")[0]
                if DEBUG:
                    print(f"response text: {response_text[len(BOT_NAME)+2:]}")
                await message.channel.send(response_text[len(BOT_NAME)+2:])
                CONVERSATION_HISTORY += f'{BOT_NAME}: {response_text}\n'


    else:
        await message.channel.send("Error: there was a problem with the endpoint.")

# Run the discord client
client.run(DISCORD_BOT_TOKEN)
