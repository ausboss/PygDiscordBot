# a quick implementation of a discord bot with the help of chat gpt and the code from the main.py
# it needs work
import discord
import requests
import json
# Initialize the discord client
intents = discord.Intents.default()
intents.messages = True
CHANNEL_ID = "#######channel ID goes here######"
client = discord.Client(intents=intents)
debug = False

endpoint = "https://example-kobold-ui-link.trycloudflare.com"

conversation_history = "Chat Bot's Persona: A chat bot. Very cool personality and likes to talk.\n" + \
                       '<START>\n' + \
                       "Chat Bot: Lets Chat. Whats new with you?\n"

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == 'q':
        await message.channel.send("\n\nChat Ended\n\n")
        return


    message_content = message.content[8:].strip() # remove the prefix "ChatBot:"

    global conversation_history
    # Add the user input to the conversation history
    conversation_history += f'You: {message_content}\n'
    # Define the prompt

    prompt = {
        "prompt": conversation_history + 'Chat Bot:',
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
    if debug:
        print(json.dumps(prompt, indent=4))
    # Send a post request to the API endpoint
    response = requests.post(f"{endpoint}/api/v1/generate", json=prompt)
    # Check if the request was successful
    if response.status_code == 200:
        # Get the results from the response
        results = response.json()['results']
        # Print the results for debug

        for result in results:
            if "\n" in result['text']:
                print(result['text'])
                response_text = result['text'].split("\n")[0]
                await message.channel.send(response_text)
                conversation_history = conversation_history + 'Chat Bot:' + response_text + '\n'
    else:
        await message.channel.send("Error: there was a problem with the endpoint.")

# Run the discord client
client.run("replace this string with your discord bot token")
