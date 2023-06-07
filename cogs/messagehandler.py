from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import random

load_dotenv()
import re


class ListenerCog(commands.Cog, name="listener"):
    def __init__(self, bot):
        self.bot = bot

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

        # if message starts with ".", "/"" or is by the bot - do nothing
        if message.author == self.bot.user or message.content.startswith((".", "/")):
            return
        name_check_string = message.clean_content.lower()
        # if message is a mention of the bot or a reply then continue
        if self.bot.user.name in [mention.name for mention in message.mentions] or self.bot.user.name.lower() in name_check_string:

            
            """
            Main On Message Handler

            This part needs to be as basic as possible

            """
            # if message is channel id argument or DM or
            if message.channel.id in [int(channel_id) for channel_id in self.bot.guild_ids] or message.guild is None:
                # image handling
                if await self.has_image_attachment(message):
                    image_response = await self.bot.get_cog("image_caption").image_comment(message, message.content)
                    response = await self.bot.get_cog("chatbot").chat_command(message, image_response)
                    if response:
                        async with message.channel.typing():
                            await asyncio.sleep(1)  # Simulate some work being done
                            await message.reply(response)
                else:
                    # No image. Normal text response
                    response = await self.bot.get_cog("chatbot").chat_command(message, message.content)
                    if response:
                        async with message.channel.typing():
                            await asyncio.sleep(1 + random.randint(0,2))  # Simulate some work being done
                            await message.reply(response)
                            return



async def setup(bot):
    await bot.add_cog(ListenerCog(bot))