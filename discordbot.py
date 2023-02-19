import requests
import json
import os
import io
import discord
from PIL import Image
from pathlib import Path
import re
import base64
from dotenv import load_dotenv
from discord.ext import commands
# get .env variables
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ENDPOINT = os.getenv("ENDPOINT")
PERIOD_IGNORE = os.getenv("PERIOD_IGNORE")
SAVE_CHATS = os.getenv("SAVE_CHATS")
SEND_GREETING = os.getenv("SEND_GREETING")
def split_text(text):
    parts = re.split(r'\n[a-zA-Z]', text)
    parts = [part for part in parts if not part.startswith("You:")]
    return parts
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

def get_prompt(conversation_history, user, text):
    return {
        "prompt": conversation_history + f"{user}: {text}\n{char_name}:",
        "use_story": setting['use_story'],
        "use_memory": setting['use_memory'],
        "use_authors_note": setting['use_authors_note'],
        "use_world_info": setting['use_world_info'],
        "max_context_length": setting['max_context_length'],
        "max_length": setting['max_length'],
        "rep_pen": setting['rep_pen'],
        "rep_pen_range": setting['rep_pen_range'],
        "rep_pen_slope": setting['rep_pen_slope'],
        "temperature": setting['temperature'],
        "tfs": setting['tfs'],
        "top_a": setting['top_a'],
        "top_k": setting['top_k'],
        "top_p": setting['top_p'],
        "typical": setting['typical'],
        "sampler_order": setting['sampler_order'],
        "frmttriminc": setting['frmttriminc'],
        "frmtrmblln": setting['frmtrmblln']
    }

characters_folder = 'Characters'
cards_folder = 'Cards'
settings_folder = 'Settings'
characters = []
settings = []
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
                characters.append(character_data)
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
char_dialogue = data["example_dialogue"]
char_dialogue = char_dialogue.replace('"', "")
char_image = data.get("char_image")
# Get the settings for the generation.
for filename in os.listdir(settings_folder):
    if filename.endswith('.settings'):
        with open(os.path.join(settings_folder, filename)) as read_file:
            trimed_name = filename.replace('.settings', '')
            generation_settings = json.load(read_file)
            generation_settings['setting_name'] = trimed_name
            generation_settings['use_story'] = generation_settings.get('use_story', False)
            generation_settings['use_memory'] = generation_settings.get('use_memory', False)
            generation_settings['use_authors_note'] = generation_settings.get('use_authors_note', False)
            generation_settings['use_world_info'] = generation_settings.get('use_world_info', False)
            generation_settings['max_context_length'] = generation_settings.get('max_length', 1818)
            generation_settings['max_length'] = generation_settings.get('genamt', 60)
            generation_settings['rep_pen'] = generation_settings.get('rep_pen', 1.01)
            generation_settings['rep_pen_range'] = generation_settings.get('rep_pen_range', 1024)
            generation_settings['rep_pen_slope'] = generation_settings.get('rep_pen_slope', 0.9)
            generation_settings['temperature'] = generation_settings.get('temperature', 1)
            generation_settings['tfs'] = generation_settings.get('tfs', 0.9)
            generation_settings['top_a'] = generation_settings.get('top_a', 0)
            generation_settings['top_k'] = generation_settings.get('top_k', 40)
            generation_settings['top_p'] = generation_settings.get('top_p', 0.9)
            generation_settings['typical'] = generation_settings.get('typical', 1)
            generation_settings['sampler_order'] = generation_settings.get('sampler_order', [6, 0, 1, 2, 3, 4, 5])
            generation_settings['frmttriminc'] = generation_settings.get('frmttriminc', True)
            generation_settings['frmtrmblln'] = generation_settings.get('frmtrmblln', True)
            settings.append(generation_settings)
for i, setting in enumerate(settings):
    print(f"{i+1}. {generation_settings['setting_name']}")
selected_settings= int(input("Please select a settings file: ")) - 1
setting = settings[selected_settings]
num_lines_to_keep = 20
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)
conversation_history = f"{char_name}'s Persona: {data['char_persona']}\n" + \
                        f"Scenario: {data['world_scenario']}\n" + \
                        f'<START>\n' + \
                        f'f"{char_name}: {char_greeting}\n'
starting_dialogue = char_greeting.replace("{", "").replace("}", "").replace("'", "")
@bot.event
async def on_ready():
    try:
        with open(f"Characters/{char_image}", 'rb') as f:
            avatar_data = f.read()
        await bot.user.edit(username=char_name, avatar=avatar_data)
    except FileNotFoundError:
        with open(f"Characters/default.png", 'rb') as f:
            avatar_data = f.read()
        await bot.user.edit(username=char_name, avatar=avatar_data)
        print(f"No image found for {char_name}. Setting image to default.")
    except discord.errors.HTTPException as error:
        if error.code == 50035 and 'Too many users have this username, please try another' in error.text:
            await bot.user.edit(username=char_name + "BOT", avatar=avatar_data)
        elif error.code == 50035 and 'You are changing your username or Discord Tag too fast. Try again later.' in error.text:
            pass
        else:
            raise error
    print(f'{bot.user} has connected to Discord! The bot will use the following channel: ' + CHANNEL_ID)
    channel = bot.get_channel(int(CHANNEL_ID))
    if SEND_GREETING and not os.path.exists('Logs/chat_logs.txt') :
        await channel.send(char_greeting)
    elif SEND_GREETING and not SAVE_CHATS:
        await channel.send(char_greeting)
@bot.command()
async def reset(ctx):
    global conversation_history
    conversation_history = f"{char_name}'s Persona: {data['char_persona']}\n" + \
                            f"Scenario: {data['world_scenario']}\n" + \
                            f'<START>\n' + \
                            f'f"{char_name}: {char_greeting}\n'
    await ctx.send("Conversation history has been reset.")
@bot.event
async def on_message(message):
    if PERIOD_IGNORE and message.content.startswith(".") and not message.content.startswith("/") and not message.channel.id == CHANNEL_ID:
        return
    else:
        global conversation_history
        if message.author == bot.user:
            return
        your_message = message.content
        if SAVE_CHATS:
            with open("Logs/chat_logs.txt", "a") as file:
                file.write(f"You:{your_message}\n")
        print(f"{message.author.nickname}:{your_message}")
        prompt = get_prompt(conversation_history,message.author.name, message.content)
        print(prompt)
        response = requests.post(f"{ENDPOINT}/api/v1/generate", json=prompt)
        if response.status_code == 200:
            results = response.json()['results']
            text = results[0]['text']
            response_text = split_text(text)[0]
            if SAVE_CHATS:
                with open("Logs/chat_logs.txt", "a") as file:
                    file.write(f'{char_name}: {response_text}\n')
            conversation_history = conversation_history + f'{char_name}: {response_text}\n'
            response_text = response_text.replace(char_name+":", "")
            await message.channel.send(response_text)

bot.run(DISCORD_BOT_TOKEN)