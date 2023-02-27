import json
import os
import io
import discord
from PIL import Image
from pathlib import Path
import base64
from discord.ext import commands
from discord.ext.commands import Bot
import asyncio
import shutil
from colorama import Fore, Style
import sys

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('Usage: python discordbot.py <DISCORD_BOT_TOKEN> <ENDPOINT> <CHANNEL_ID>')
        sys.exit(1)
    DISCORD_BOT_TOKEN = sys.argv[1]
    ENDPOINT = sys.argv[2]
    CHANNEL_ID = sys.argv[3]
# Access environment variables like this


intents = discord.Intents.all()
bot = Bot(command_prefix="/", intents=intents, help_command=None)
bot.endpoint = ENDPOINT
bot.channel_id = CHANNEL_ID
characters_folder = 'Characters'
cards_folder = 'Cards'
characters = []

def upload_character(json_file, img, tavern=False):
    json_file = json_file if type(json_file) == str else json_file.decode('utf-8')
    data = json.loads(json_file)
    outfile_name = data["char_name"]
    i = 1
    while Path(f'{characters_folder}/{outfile_name}.json').exists():
        outfile_name = f'{data["char_name"]}_{i:03d}'
        i += 1
    if tavern:
        outfile_name = f'TavernAI-{outfile_name}'
    with open(Path(f'{characters_folder}/{outfile_name}.json'), 'w') as f:
        f.write(json_file)
    if img is not None:
        img = Image.open(io.BytesIO(img))
        img.save(Path(f'{characters_folder}/{outfile_name}.png'))
    print(f'New character saved to "{characters_folder}/{outfile_name}.json".')
    return outfile_name


def upload_tavern_character(img, name1, name2):
    _img = Image.open(io.BytesIO(img))
    _img.getexif()
    decoded_string = base64.b64decode(_img.info['chara'])
    _json = json.loads(decoded_string)
    _json = {"char_name": _json['name'], "char_persona": _json['description'], "char_greeting": _json["first_mes"], "example_dialogue": _json['mes_example'], "world_scenario": _json['scenario']}
    _json['example_dialogue'] = _json['example_dialogue'].replace('{{user}}', name1).replace('{{char}}', _json['char_name'])
    return upload_character(json.dumps(_json), img, tavern=True)


# CONVERT CARDS
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
            if not os.path.exists(f"{cards_folder}/Converted"):
                os.makedirs(f"{cards_folder}/Converted")
            os.rename(os.path.join(cards_folder, filename), os.path.join(f"{cards_folder}/Converted/", filename))
except:
    pass


# Load character data from JSON files in the character folder
for filename in os.listdir(characters_folder):
    if filename.endswith('.json'):
        with open(os.path.join(characters_folder, filename)) as read_file:
            character_data = json.load(read_file)
            # Add the filename as a key in the character data dictionary
            character_data['char_filename'] = filename
            # Check if there is a corresponding image file for the character
            image_file_jpg = f"{os.path.splitext(filename)[0]}.jpg"
            image_file_png = f"{os.path.splitext(filename)[0]}.png"
            if os.path.exists(os.path.join(characters_folder, image_file_jpg)):
                character_data['char_image'] = image_file_jpg
            elif os.path.exists(os.path.join(characters_folder, image_file_png)):
                character_data['char_image'] = image_file_png
            characters.append(character_data)

# Character selection
# Check if chardata.json exists
if os.path.exists('chardata.json'):
    with open("chardata.json") as read_file:
        character_data = json.load(read_file)
    # Prompt the user to use the same character
    print(f"\n\n{Fore.CYAN}✔ Found {character_data['char_name']} data file.{Style.RESET_ALL} Loading character...{Style.RESET_ALL}")
    # Set up the timer
    try:
        answer = input(f"\n❔ Load a new character?{Fore.RED} (y/n) {Fore.GREEN}[n]: {Style.RESET_ALL}")
    except:
        answer = "n"

else:
    answer = "y"

if answer.lower() == "y":
    for i, character in enumerate(characters):
        print(f"{i+1}. {character['char_name']}")
    selected_char = int(input("Please select a character: ")) - 1
    data = characters[selected_char]
    update_name = input("Update Bot name and pic? (y or n): ")
    # Get the character name, greeting, and image
    char_name = data["char_name"]
    char_filename = os.path.join(characters_folder, data['char_filename'])
    char_image = data.get("char_image")
    shutil.copyfile(char_filename, "chardata.json")
else:
    update_name = "n"

# on ready event that will update the character name and picture if you chose yes
@bot.event
async def on_ready():

    if update_name.lower() == "y":
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
                new_name = input('Too many users have this username, Enter a new name(tip: üse án àccent lèttèr ): ')
                await bot.user.edit(username=new_name, avatar=avatar_data)
            elif error.code == 50035 and 'You are changing your username or Discord Tag too fast. Try again later.' in error.text:
                pass
            else:
                raise error
    print(f'\n{Fore.CYAN}{bot.user.name} {Style.RESET_ALL}has connected to Discord!\n')
    for guild in bot.guilds:
        print(f"I'm active in {Fore.GREEN}{guild}{Style.RESET_ALL}!")

async def on_message(message, bot):
    if message.author == bot.user:
        return
    await message.channe.send("hello world")

# COG LOADER
async def load_cogs() -> None:
    for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/cogs"):
        if file.endswith(".py"):
            extension = file[:-3]
            try:
                await bot.load_extension(f"cogs.{extension}")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                print(exception)

asyncio.run(load_cogs())
bot.run(DISCORD_BOT_TOKEN)
