import json
import os
import io
import discord
from PIL import Image
from pathlib import Path
import base64
from helpers.textgen import TextGen
from langchain.llms import KoboldApiLLM, OpenAI
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Bot
import asyncio
import shutil
import sys
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
ENDPOINT = str(os.getenv("ENDPOINT"))
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHAT_HISTORY_LINE_LIMIT = os.getenv("CHAT_HISTORY_LINE_LIMIT")
try:
    ALWAYS_REPLY = os.getenv("ALWAYS_REPLY")
except:
    ALWAYS_REPLY = True
if os.getenv("MAX_NEW_TOKENS") is not None:
    MAX_NEW_TOKENS = os.getenv("MAX_NEW_TOKENS")
else:
    MAX_NEW_TOKENS = 300

intents = discord.Intents.all()
bot = Bot(command_prefix="/", intents=intents, help_command=None)
bot.endpoint = str(ENDPOINT)
if len(bot.endpoint.split("/api")) > 0:
    bot.endpoint = bot.endpoint.split("/api")[0]
bot.chatlog_dir = "chatlog_dir"
bot.endpoint_connected = False
bot.always_reply = True if ALWAYS_REPLY.lower() == "t" else False
print(f'ALWAYS_REPLY: {bot.always_reply}')
bot.channel_id = CHANNEL_ID
bot.num_lines_to_keep = int(CHAT_HISTORY_LINE_LIMIT)
bot.guild_ids = [int(x) for x in CHANNEL_ID.split(",")]
bot.debug = True
bot.char_name = ""
bot.endpoint_type = ""
characters_folder = "Characters"
cards_folder = "Cards"
characters = []


def upload_character(json_file, img, tavern=False):
    json_file = json_file if type(json_file) == str else json_file.decode("utf-8")

    data = json.loads(json_file)
    outfile_name = data["char_name"]
    i = 1
    while Path(f"{characters_folder}/{outfile_name}.json").exists():
        outfile_name = f'{data["char_name"]}_{i:03d}'
        i += 1
    if tavern:
        outfile_name = f"TavernAI-{outfile_name}"
    with open(Path(f"{characters_folder}/{outfile_name}.json"), "w") as f:
        f.write(json_file)
    if img is not None:
        img = Image.open(io.BytesIO(img))
        img.save(Path(f"{characters_folder}/{outfile_name}.png"))
    print(f'New character saved to "{characters_folder}/{outfile_name}.json".')
    return outfile_name


def upload_tavern_character(img, name1, name2):
    _img = Image.open(io.BytesIO(img))
    _img.getexif()
    decoded_string = base64.b64decode(_img.info["chara"])
    _json = json.loads(decoded_string)
    _json = {
        "char_name": _json["name"],
        "char_persona": _json["description"],
        "char_greeting": _json["first_mes"],
        "example_dialogue": _json["mes_example"],
        "world_scenario": _json["scenario"],
    }
    _json["example_dialogue"] = (
        _json["example_dialogue"]
        .replace("{{user}}", name1)
        .replace("{{char}}", _json["char_name"])
    )
    return upload_character(json.dumps(_json), img, tavern=True)


try:
    for filename in os.listdir(cards_folder):
        if filename.endswith(".png"):
            with open(os.path.join(cards_folder, filename), "rb") as read_file:
                img = read_file.read()

                name1 = "User"
                name2 = "Character"
                tavern_character_data = upload_tavern_character(img, name1, name2)
            with open(
                os.path.join(characters_folder, tavern_character_data + ".json")
            ) as read_file:
                character_data = json.load(read_file)
                # characters.append(character_data)
            read_file.close()
            if not os.path.exists(f"{cards_folder}/Converted"):
                os.makedirs(f"{cards_folder}/Converted")
            os.rename(
                os.path.join(cards_folder, filename),
                os.path.join(f"{cards_folder}/Converted/", filename),
            )
except:
    pass


# Load character data from JSON files in the character folder
for filename in os.listdir(characters_folder):
    if filename.endswith(".json"):
        with open(
            os.path.join(characters_folder, filename), encoding="utf-8"
        ) as read_file:
            character_data = json.load(read_file)
            # Add the filename as a key in the character data dictionary
            character_data["char_filename"] = filename
            # Check if there is a corresponding image file for the character
            image_file_jpg = f"{os.path.splitext(filename)[0]}.jpg"
            image_file_png = f"{os.path.splitext(filename)[0]}.png"
            if os.path.exists(os.path.join(characters_folder, image_file_jpg)):
                character_data["char_image"] = image_file_jpg
            elif os.path.exists(os.path.join(characters_folder, image_file_png)):
                character_data["char_image"] = image_file_png
            characters.append(character_data)

# Character selection
# Check if chardata.json exists

if os.path.exists("chardata.json"):
    with open("chardata.json", encoding="utf-8") as read_file:
        character_data = json.load(read_file)
    # Prompt the user to use the same character
    print(f"Last Character used: {character_data['char_name']}")
    # Set up the timer
    try:
        answer = input(f"\nUse this character? (y/n) [y]: ")
    except:
        answer = "y"

else:
    answer = "n"

if answer.lower() == "n":
    for i, character in enumerate(characters):
        print(f"{i+1}. {character['char_name']}")
    selected_char = None
    while selected_char is None:
        try:
            selected_char = int(input(f"\n\nPlease select a character: ")) - 1
            if selected_char < 0 or selected_char >= len(characters):
                raise ValueError
        except ValueError:
            print("Invalid input. Please enter a number between 1 and", len(characters))
            selected_char = None
    data = characters[selected_char]
    update_name = None
    while update_name not in ["y", "n"]:
        update_name = input("Update Bot name and pic? (y or n): ").lower()
        if update_name not in ["y", "n"]:
            print("Invalid input. Please enter 'y' or 'n'.")
    # Get the character name, greeting, and image
    char_name = data["char_name"]
    char_filename = os.path.join(characters_folder, data["char_filename"])
    char_image = data.get("char_image")
    shutil.copyfile(char_filename, "chardata.json")
else:
    update_name = "n"


# add error catching for invalid endpoint
llm_selected = input("Select LLM (1: Kobold, 2: Oobabooga): ")
if llm_selected == "1":
    bot.endpoint_type = "Kobold"
    bot.llm = KoboldApiLLM(endpoint=bot.endpoint, max_length=MAX_NEW_TOKENS)
elif llm_selected == "2":
    bot.endpoint_type = "Oobabooga"
    bot.llm = TextGen(model_url=bot.endpoint, max_new_tokens=MAX_NEW_TOKENS)


@bot.event
async def on_ready():
    if update_name.lower() == "y":
        try:
            with open(f"Characters/{char_image}", "rb") as f:
                avatar_data = f.read()
            await bot.user.edit(username=char_name, avatar=avatar_data)
        except FileNotFoundError:
            with open(f"Characters/default.png", "rb") as f:
                avatar_data = f.read()
            await bot.user.edit(username=char_name, avatar=avatar_data)
            print(f"No image found for {char_name}. Setting image to default.")
        except discord.errors.HTTPException as error:
            if (
                error.code == 50035
                and "Too many users have this username, please try another"
                in error.text
            ):
                new_name = input(
                    "Too many users have this username, Enter a new name(tip: üse án àccent lèttèr ): "
                )
                await bot.user.edit(username=new_name, avatar=avatar_data)
            elif (
                error.code == 50035
                and "You are changing your username or Discord Tag too fast. Try again later."
                in error.text
            ):
                pass
            else:
                raise error
    print(f"{bot.user.name} has connected to:")

    for items in bot.guild_ids:
        try:
            # get the channel object from the channel ID
            channel = bot.get_channel(int(items))
            # get the guild object from the channel object
            guild = channel.guild
            # check that the channel is a text channel
            if isinstance(channel, discord.TextChannel):
                channel_name = channel.name
                print(f"{guild.name} \ {channel_name}")
            else:
                print(f"Channel with ID {bot.channel_id} is not a text channel")
        except AttributeError:
            print(
                "\n\n\n\nERROR: Unable to retrieve channel from .env \nPlease make sure you're using a valid channel ID, not a server ID."
            )


# COG LOADER
async def load_cogs() -> None:
    for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/cogs"):
        if file.endswith(".py"):
            extension = file[:-3]
            try:
                await bot.load_extension(f"cogs.{extension}")
                if extension == "pygbot":
                    bot.endpoint_connected = True
            except commands.ExtensionError as e:
                if extension == "pygbot":
                    bot.endpoint_connected = False
                if not bot.debug:
                    logging.error(
                        f"\n\nIssue with ENDPOINT. Please check your ENDPOINT in the .env file"
                    )
                else:
                    exception = f"{type(e).__name__}: {e}"
                    print(f"Failed to load extension {extension}\n{exception}")


asyncio.run(load_cogs())
if bot.endpoint_connected:
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except discord.errors.LoginFailure:
        print(
            "\n\n\n\nThere is an error with the Discord Bot token. Please check your .env file"
        )
