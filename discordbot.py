import requests
import json
import os
import io
import discord
from PIL import Image
from pathlib import Path
import base64
from dotenv import load_dotenv
# get .env variables
load_dotenv()
# Set the endpoint URL
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
ENDPOINT = os.getenv("ENDPOINT")
# Replace the client ID and token with your own Discord bot credentials
DEBUG = False

def upload_character(json_file, img, tavern=False):
    json_file = json_file if type(json_file) == str else json_file.decode('utf-8')
    data = json.loads(json_file)
    outfile_name = data["char_name"]
    i = 1
    while Path(f'characters/{outfile_name}.json').exists():
        outfile_name = f'{data["char_name"]}_{i:03d}'
        i += 1
    if tavern:
        outfile_name = f'TavernAI-{outfile_name}'
    with open(Path(f'characters/{outfile_name}.json'), 'w') as f:
        f.write(json_file)
    if img is not None:
        img = Image.open(io.BytesIO(img))
        img.save(Path(f'characters/{outfile_name}.png'))
    print(f'New character saved to "characters/{outfile_name}.json".')
    return outfile_name

def upload_tavern_character(img, name1, name2):
    _img = Image.open(io.BytesIO(img))
    _img.getexif()
    decoded_string = base64.b64decode(_img.info['chara'])
    _json = json.loads(decoded_string)
    _json = {"char_name": _json['name'], "char_persona": _json['description'], "char_greeting": _json["first_mes"], "example_dialogue": _json['mes_example'], "world_scenario": _json['scenario']}
    _json['example_dialogue'] = _json['example_dialogue'].replace('{{user}}', name1).replace('{{char}}', _json['char_name'])
    return upload_character(json.dumps(_json), img, tavern=True)

characters_folder = 'Characters'
cards_folder = 'Cards'
characters = []

# Check the Cards folder for cards and convert them to characters
try:
    for filename in os.listdir(cards_folder):
        if filename.endswith('.png'):
            with open(os.path.join(cards_folder, filename), 'rb') as read_file:
                img = read_file.read()
                name1 = 'User'
                name2 = 'Character'
                tavern_character_data = upload_tavern_character(img, name1, name2)
            with open(os.path.join(characters_folder, tavern_character_data + '.json')) as read_file:
                character_data = json.load(read_file)
                # characters.append(character_data)
            read_file.close()
            os.rename(os.path.join(cards_folder, filename), os.path.join(cards_folder, 'Converted', filename))
except:
    pass

# Load character data from JSON files in the character folder
for filename in os.listdir(characters_folder):
    if filename.endswith('.json'):
        with open(os.path.join(characters_folder, filename)) as read_file:
            character_data = json.load(read_file)
            # Check if there is a corresponding image file for the character
            image_file_jpg = f"{os.path.splitext(filename)[0]}.jpg"
            image_file_png = f"{os.path.splitext(filename)[0]}.png"
            if os.path.exists(os.path.join(characters_folder, image_file_jpg)):
                character_data['char_image'] = image_file_jpg
            elif os.path.exists(os.path.join(characters_folder, image_file_png)):
                character_data['char_image'] = image_file_png
            characters.append(character_data)



# Print a list of characters and let the user choose one
for i, character in enumerate(characters):
    print(f"{i+1}. {character['char_name']}")
selected_char = int(input("Please select a character: ")) - 1
data = characters[selected_char]

# Get the character name, greeting, and image
char_name = data["char_name"]
char_greeting = data["char_greeting"]
char_dialogue = data["char_greeting"]
char_image = data.get("char_image")


def get_prompt(conversation_history):
    return {
        "prompt": '\n'.join(conversation_history.split('\n')[-num_lines_to_keep:]) + f'{char_name}:',
        "use_story": False,
        "use_memory": False,
        "use_authors_note": False,
        "use_world_info": False,
        "max_context_length": 1818,
        "max_length": 180,
        "rep_pen": 1.03,
        "rep_pen_range": 1024,
        "rep_pen_slope": 0.9,
        "temperature": 0.98,
        "tfs": 0.9,
        "top_a": 0,
        "top_k": 0,
        "top_p": 0.9,
        "typical": 1,
        "sampler_order": [
            6, 0, 1, 2,
            3, 4, 5
        ],
        "frmttriminc": True,
        "frmtrmblln": True
    }

first_message = True
num_lines_to_keep = 20
intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)
@client.event
async def on_ready():
    # Set discord bot name
    await client.user.edit(username=char_name)
    # Set discord bot image
    try:
        with open(f"Characters/{char_image}", 'rb') as f:
            avatar_data = f.read()
        await client.user.edit(avatar=avatar_data)
    except FileNotFoundError:
        print(f"No image found for {char_name}.\nSave an image with the same name as the json in the Characters folder.")
        try:
            with open(f"Characters/default.png", 'rb') as f:
                avatar_data = f.read()
            await client.user.edit(avatar=avatar_data)
            print("setting image to default")
        except:
            pass
    print(f'{client.user} has connected to Discord!')
conversation_history = f"{char_name}'s Persona: {data['char_persona']}\n" + \
                        f"World Scenario: {data['world_scenario']}\n" + \
                        f'<START>\n' + \
                        f'{char_dialogue}' + \
                        f'<START>\n'
@client.event
async def on_message(message):
    global first_message
    global conversation_history
    if message.author == client.user:
        return

    # Initialize the conversation history to the starting prompt


    if first_message:
        first_message = False
        conversation_history += f"{char_name}: {char_greeting}\n"
        response_text = char_greeting
        await message.channel.send(response_text)
    else:
        conversation_history += f'You: {message.content}\n'
        # Get the prompt
        prompt = get_prompt(conversation_history)
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
                    if len(result['text'].split("You:")) > 0:
                        response_text = result['text'].split("You:")[0].replace(f"{char_name}:", "").strip()
                    else:
                        response_text = result['text']
                    if DEBUG:
                        print(f"response text: {response_text}")
                    await message.channel.send(response_text)
                    conversation_history = conversation_history + f'{char_name}: {response_text}\n'


client.run(DISCORD_BOT_TOKEN)