import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import asyncio
import random
from datetime import datetime, timedelta

load_dotenv()
import re

def embedder(msg):
    embed = discord.Embed(
            description=f"{msg}",
            color=0x9C84EF
        )
    return embed


class ListenerCog(commands.Cog, name="listener"):
    def __init__(self, bot):
        self.bot = bot
        self.listen_only_mode = False  # New variable for tracking listen-only mode
        self.last_message_times = {}  # Dictionary to store last message time for each channel


    @app_commands.command(name="listen", description="listen-only mode")
    async def listen(self, interaction: discord.Interaction, cog: str):
        if cog.lower() == "on":
            self.listen_only_mode = True
        elif cog.lower() == "off":
            self.listen_only_mode = False
        else:
            await interaction.response.send_message(".Invalid argument. Please use `on` or `off`.")
            return
        await interaction.response.send_message(f".Listen-only mode is now {'on' if self.listen_only_mode else 'off'}.")


    async def has_image_attachment(self, message_content):
        url_pattern = re.compile(r'http[s]?://[^\s/$.?#].[^\s]*\.(jpg|jpeg|png|gif)', re.IGNORECASE)
        tenor_pattern = re.compile(r'https://tenor.com/view/[\w-]+')
        for attachment in message_content.attachments:
            if attachment.filename.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                return True
            # Check if the message content contains a URL that ends with an image file extension
        if url_pattern.search(message_content.content):
            return True
        # Check if the message content contains a Tenor GIF URL

        elif tenor_pattern.search(message_content.content):
            return True
        else:
            return False

    @commands.Cog.listener()
    async def on_message(self, message):

        # Ignore messages from the bot or that start with ".", "/", or are not in the bot's channels.
        if (
            message.author == self.bot.user
            or message.content.startswith((".", "/"))
            or message.channel.id not in [int(channel_id) for channel_id in self.bot.guild_ids]
        ):
            return

        # Checks if the message is a reply or contains the bot's name.
        is_reply_to_bot = message.reference and message.reference.resolved.author == self.bot.user
        mentions_bot = self.bot.user in message.mentions
        contains_bot_name = self.bot.user.name.lower() in message.clean_content.lower()
        directed_at_bot = is_reply_to_bot or mentions_bot or contains_bot_name



        # If the message isn't directed at the bot, and handle if it has an image or not sending to chat_command_nr
        if not directed_at_bot:
            if await self.has_image_attachment(message):
                image_response = await self.bot.get_cog("image_caption").image_comment(message, message.clean_content)
                response = await self.bot.get_cog("chatbot").chat_command_nr(message, image_response)
            else:
                response = await self.bot.get_cog("chatbot").chat_command_nr(message, message.clean_content)
            return

        now = datetime.utcnow()

        # If listen-only mode is enabled, handle accordingly
        if self.listen_only_mode:
            if await self.has_image_attachment(message):
                image_response = await self.bot.get_cog("image_caption").image_comment(message, message.clean_content)
                response = await self.bot.get_cog("chatbot").chat_command_nr(message, image_response)
            else:
                response = await self.bot.get_cog("chatbot").chat_command_nr(message, message.clean_content)
            return

        else:
            # Image handling
            if await self.has_image_attachment(message):
                image_response = await self.bot.get_cog("image_caption").image_comment(message, message.clean_content)
                response = await self.bot.get_cog("chatbot").chat_command(message, image_response)
            else:
                # No image. Normal text response
                response = await self.bot.get_cog("chatbot").chat_command(message, message.clean_content)

            if response:
                async with message.channel.typing():
                    await asyncio.sleep(1)  # Simulate some work being done
                    if random.random() < 0.8:
                        await message.channel.send(response)
                    else:
                        await message.reply(response)



async def setup(bot):
    await bot.add_cog(ListenerCog(bot))