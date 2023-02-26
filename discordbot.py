import json
import os
import io
import discord
from PIL import Image
from pathlib import Path
import re
import base64
from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Context
import asyncio
import random
import shutil


# get .env variables
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
ENDPOINT = os.getenv("ENDPOINT")
PERIOD_IGNORE = os.getenv("PERIOD_IGNORE")
CHANNEL_ID = os.getenv("CHANNEL_ID")
intents = discord.Intents.all()
bot = Bot(command_prefix=commands.when_mentioned_or("/"), intents=intents, help_command=None)


def upload_character(json_file, img, tavern=False):
    json_file = json_file if type(json_file) == str else json_file.decode('utf-8')
    data = json.loads(json_file)
    outfile_name = data["char_name"]
    i = 1
    while Path(f'Characters/{outfile_name}.json').exists():
        outfile_name = f'{data["char_name"]}_{i:03d}'
        i += 1
    if tavern:
        outfile_name = f'TavernAI-{outfile_name}'
    with open(Path(f'Characters/{outfile_name}.json'), 'w') as f:
        f.write(json_file)
    if img is not None:
        img = Image.open(io.BytesIO(img))
        img.save(Path(f'Characters/{outfile_name}.png'))
    print(f'New character saved to "Characters/{outfile_name}.json".')
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

# # Check if chardata.json exists
if os.path.exists('chardata.json'):
    # Prompt the user to use the same character
    new_character_load = input("load new character?(y/n): ")
    update_name = "n"
else:
    new_character_load = "y"

if new_character_load.lower() == "y":
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
                await bot.user.edit(username=char_name + "BOT", avatar=avatar_data)
            elif error.code == 50035 and 'You are changing your username or Discord Tag too fast. Try again later.' in error.text:
                pass
            else:
                raise error
    print(f'{bot.user} has connected to Discord!')


# This function is triggered every time a message is sent in a Discord server
# Simple
async def on_message(message):
    if message.author == bot.user:
        return
    if PERIOD_IGNORE and not message.content.startswith("."):
        if message.channel.id == int(CHANNEL_ID):

            if message.attachments and message.attachments[0].filename.lower().endswith(
                    (".jpg", ".jpeg", ".png", ".gif")):
                # The message has an attached image, pass it to the imagecaption cog
                image_response = await bot.get_cog("image_caption").image_comment(message, message.content)
                response = await bot.get_cog("chatbot").chat_command(message, image_response, bot)
                async with message.channel.typing():
                    await asyncio.sleep(2)  # Simulate some work being done
                    await message.reply(response)
            else:
                response = await bot.get_cog("chatbot").chat_command(message, message.content, bot)
                await message.channel.send(response)


# Add the message handler function to the bot
bot.event(on_message)


################beginning###########################################################
# functions for the more complex on_message function

# async def replace_user_mentions(content, bot):
#     user_ids = re.findall(r'<@(\d+)>', content)
#     for user_id in user_ids:
#         user = await bot.fetch_user(int(user_id))
#         if user:
#             display_name = user.display_name
#             content = content.replace(f"<@{user_id}>", display_name)
#     return content
# 
# async def extract_message_contents(messages):
#     message_contents = [message.content for message in sorted(messages, key=lambda m: m.created_at)]
#     joined_messages = "\n".join(message_contents)
#     cleaned_joined = await replace_user_mentions(joined_messages, bot)
#     return cleaned_joined


# same as above but this is the version with more complex logic
# This function is triggered every time a message is sent in a Discord server
# async def on_message(message):
#     if message.author == bot.user:
#         return
#     if PERIOD_IGNORE and not message.content.startswith("."):
#         # Check if the message is sent in a server or a private message
#         if message.channel.id == int(CHANNEL_ID) or message.guild is None:
#             message_content = message.content
#             # Get the message content and the bot's name for pattern matching
#             content = message.content.lower()
#             name_pattern = r"(\b|^){}(\b|$)".format(bot.user.name.split()[0].lower())
#             if message.reference is not None:
#                 pass
#             if content.startswith(f"<@{bot.user.id}>"):
#                 # The bot is mentioned at the beginning of the message
#                 message_content = content.replace(f"<@{bot.user.id}>", "").strip()
#                 if not message_content and not message.attachments:
#                     # No message content after the bot mention, check last few messages for context
#                     message_log = []
#                     async for msg in message.channel.history(limit=5):
#                         if msg.author == message.author:
#                             message_log.append(msg)
#                     if len(message_log) > 0:
#                         extracted_message = await extract_message_contents(message_log)
#                         print(extracted_message)
#                         # message = message_log[1]
#                         message_content = extracted_message
#
#             # Replace user mentions with display names
#             if not message_content:
#                 message_content = await replace_user_mentions(message_content, bot)
#             # checks whether the message is a private message, whether the bot's name or mention is included, whether the message is a reply targeting the bot, or whether a random number is less than 0.35
#             if message.guild is None or re.search(name_pattern, content) or f"<@{bot.user.id}>" in content or (message.type == discord.MessageType.reply and message.reference.resolved != bot.user) or random.random() < 0.35:
#                 # The bot is mentioned in the message, reply 100% of the time
#                 if message.attachments and message.attachments[0].filename.lower().endswith(
#                         (".jpg", ".jpeg", ".png", ".gif")):
#                     # The message has an attached image, pass it to the imagecaption cog
#                     image_response = await bot.get_cog("image_caption").image_comment(message, message_content)
#                     response = await bot.get_cog("chatbot").chat_command(message, image_response, bot)
#                     async with message.channel.typing():
#                         await asyncio.sleep(2)  # Simulate some work being done
#                         await message.reply(response)
#                 else:
#                     response = await bot.get_cog("chatbot").chat_command(message, message_content, bot)
#                     if random.random() < 0.35:
#                         await message.channel.send(response)
#                     else:
#                         response = await bot.get_cog("chatbot").chat_command(message, message_content, bot)
#                         async with message.channel.typing():
#                             await asyncio.sleep(2)  # Simulate some work being done
#                             await message.reply(response)
#
# # Add the message handler function to the bot
# bot.event(on_message)
#
################end###########################################################

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
