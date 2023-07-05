import os
import sys
import platform
import random
import asyncio
import json
import logging
import traceback

import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Context
from dotenv import load_dotenv
import aiosqlite
from helpers import db_manager

# assuming exceptions is a custom module, otherwise remove this
import exceptions


if not os.path.isfile(f"{os.path.realpath(os.path.dirname(__file__))}/config.json"):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open(f"{os.path.realpath(os.path.dirname(__file__))}/config.json") as file:
        config = json.load(file)


# Load .env file
load_dotenv()

# Initialize bot
intents = discord.Intents.all()
bot = Bot(command_prefix="/", intents=intents, help_command=None)

# Get environment variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OOBAENDPOINT = os.getenv("OOBAENDPOINT")
KOBOLDENDPOINT = os.getenv("KOBOLDENDPOINT")
CHANNEL_ID = os.getenv("CHANNEL_ID")
OWNERS = os.getenv("OWNERS")
OPENAI = os.getenv("OPENAI")

intents = discord.Intents.all()
bot = Bot(command_prefix="/", intents=intents, help_command=None)
# Check OOBAENDPOINT and KOBOLDENDPOINT variables to see which is in use
if KOBOLDENDPOINT:
    ENDPOINT = KOBOLDENDPOINT
    bot.llm = "kobold"
elif OOBAENDPOINT:
    ENDPOINT = OOBAENDPOINT
    bot.llm = "ooba"
else:
    print("One or more required environment variables are missing.")
    print("Make sure to set OOBAENDPOINT or KOBOLDENDPOINT in the .env file.")
    sys.exit(1)

bot.endpoint = ENDPOINT
bot.openai = OPENAI
if len(bot.endpoint.split("/api")) > 0:
    bot.endpoint = bot.endpoint.split("/api")[0]
bot.chatlog_dir = "chatlog_dir"
bot.endpoint_connected = False
bot.channel_list = [int(x) for x in CHANNEL_ID.split(",")]
bot.owners = [int(x) for x in OWNERS.split(",")]


class LoggingFormatter(logging.Formatter):
    # Colors
    black = "\x1b[30m"
    red = "\x1b[31m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    blue = "\x1b[34m"
    gray = "\x1b[38m"
    # Styles
    reset = "\x1b[0m"
    bold = "\x1b[1m"

    COLORS = {
        logging.DEBUG: gray + bold,
        logging.INFO: blue + bold,
        logging.WARNING: yellow + bold,
        logging.ERROR: red,
        logging.CRITICAL: red + bold,
    }

    def format(self, record):
        log_color = self.COLORS[record.levelno]
        format = "(black){asctime}(reset) (levelcolor){levelname:<8}(reset) (green){name}(reset) {message}"
        format = format.replace("(black)", self.black + self.bold)
        format = format.replace("(reset)", self.reset)
        format = format.replace("(levelcolor)", log_color)
        format = format.replace("(green)", self.green + self.bold)
        formatter = logging.Formatter(format, "%Y-%m-%d %H:%M:%S", style="{")
        return formatter.format(record)


logger = logging.getLogger("discord_bot")
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(LoggingFormatter())
# File handler
file_handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
file_handler_formatter = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}", "%Y-%m-%d %H:%M:%S", style="{"
)
file_handler.setFormatter(file_handler_formatter)

# Add the handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)
bot.logger = logger


async def init_db():
    async with aiosqlite.connect(
        f"{os.path.realpath(os.path.dirname(__file__))}/database/database.db"
    ) as db:
        with open(
            f"{os.path.realpath(os.path.dirname(__file__))}/database/schema.sql"
        ) as file:
            await db.executescript(file.read())
        await db.commit()


bot.config = config


# on ready event that will update the character name and picture if you chose yes
@bot.event
async def on_ready():
    await db_manager.setup_db()
    bot.logger.info(f"Setting up database...")
    bot.logger.info(f"Logged in as {bot.user.name}")
    bot.logger.info(f"discord.py API version: {discord.__version__}")
    bot.logger.info(f"Python version: {platform.python_version()}")
    bot.logger.info(f"Running on: {platform.system()} {platform.release()} ({os.name})")
    bot.logger.info("-------------------")
    status_task.start()
    if config["sync_commands_globally"]:
        bot.logger.info("Syncing commands globally...")
        await bot.tree.sync()
    bot.logger.info(f"{bot.user.name} has connected to:")
    for items in bot.channel_list:
        try:
            # get the channel object from the channel ID
            channel = bot.get_channel(int(items))
            # get the guild object from the channel object
            guild = channel.guild
            # check that the channel is a text channel
            if isinstance(channel, discord.TextChannel):
                channel_name = channel.name
                bot.logger.info(f"{guild.name} \ {channel_name}")
            else:
                bot.logger.info(f"Channel with ID {items} is not a text channel")
        except AttributeError:
            bot.logger.info(
                "\n\n\n\nERROR: Unable to retrieve channel from .env \nPlease make sure you're using a valid channel ID, not a server ID."
            )


@tasks.loop(minutes=6.0)
async def status_task() -> None:
    """
    Setup the game status task of the bot.
    """
    statuses = [
        "with Langchain🦜🔗",
    ]
    await bot.change_presence(activity=discord.Game(random.choice(statuses)))


@bot.event
async def on_command_completion(context: Context) -> None:
    """
    The code in this event is executed every time a normal command has been *successfully* executed.

    :param context: The context of the command that has been executed.
    """
    full_command_name = context.command.qualified_name
    split = full_command_name.split(" ")
    executed_command = str(split[0])
    if context.guild is not None:
        bot.logger.info(
            f"Executed {executed_command} command in {context.guild.name} (ID: {context.guild.id}) by {context.author} (ID: {context.author.id})"
        )
    else:
        bot.logger.info(
            f"Executed {executed_command} command by {context.author} (ID: {context.author.id}) in DMs"
        )


@bot.event
async def on_command_error(context: Context, error) -> None:
    """
    The code in this event is executed every time a
    normal valid command catches an error.

    :param context: The context of the normal command
    that failed executing.
    :param error: The error that has been faced.
    """
    if isinstance(error, commands.CommandOnCooldown):
        minutes, seconds = divmod(error.retry_after, 60)
        hours, minutes = divmod(minutes, 60)
        hours = hours % 24
        embed = discord.Embed(
            description=f"**Please slow down** - You can use this command again in {f'{round(hours)} hours' if round(hours) > 0 else ''} {f'{round(minutes)} minutes' if round(minutes) > 0 else ''} {f'{round(seconds)} seconds' if round(seconds) > 0 else ''}.",
            color=0xE02B2B,
        )
        await context.send(embed=embed)
    elif isinstance(error, exceptions.UserBlacklisted):
        """
        The code here will only execute if the error is an instance of 'UserBlacklisted', which can occur when using
        the @checks.not_blacklisted() check in your command, or you can raise the error by yourself.
        """
        embed = discord.Embed(
            description="You are blacklisted from using the bot!", color=0xE02B2B
        )
        await context.send(embed=embed)
        if context.guild:
            bot.logger.warning(
                f"{context.author} (ID: {context.author.id}) tried to execute a command in the guild {context.guild.name} (ID: {context.guild.id}), but the user is blacklisted from using the bot."
            )
        else:
            bot.logger.warning(
                f"{context.author} (ID: {context.author.id}) tried to execute a command in the bot's DMs, but the user is blacklisted from using the bot."
            )
    elif isinstance(error, exceptions.UserNotOwner):
        """
        Same as above, just for the @checks.is_owner() check.
        """
        embed = discord.Embed(
            description="You are not the owner of the bot!", color=0xE02B2B
        )

        await context.send(embed=embed)
        if context.guild:
            bot.logger.warning(
                f"{context.author} (ID: {context.author.id}) tried to execute an owner only command in the guild {context.guild.name} (ID: {context.guild.id}), but the user is not an owner of the bot."
            )
        else:
            bot.logger.warning(
                f"{context.author} (ID: {context.author.id}) tried to execute an owner only command in the bot's DMs, but the user is not an owner of the bot."
            )
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            description="You are missing the permission(s) `"
            + ", ".join(error.missing_permissions)
            + "` to execute this command!",
            color=0xE02B2B,
        )
        await context.send(embed=embed)
    elif isinstance(error, commands.BotMissingPermissions):
        embed = discord.Embed(
            description="I am missing the permission(s) `"
            + ", ".join(error.missing_permissions)
            + "` to fully perform this command!",
            color=0xE02B2B,
        )
        await context.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="Error!",
            description=str(error).capitalize(),
            color=0xE02B2B,
        )
        await context.send(embed=embed)
    else:
        raise error


# COG LOADER
async def load_cogs() -> None:
    for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/cogs"):
        if file.endswith(".py"):
            extension = file[:-3]
            try:
                await bot.load_extension(f"cogs.{extension}")
            except Exception as e:
                # log the error and continue with the next file
                error_info = (
                    f"Failed to load extension {extension}. {type(e).__name__}: {e}"
                )
                print(error_info)
                logging.error(f"Traceback: {traceback.format_exc()}")


asyncio.run(load_cogs())
asyncio.run(init_db())
bot.run(DISCORD_BOT_TOKEN)
