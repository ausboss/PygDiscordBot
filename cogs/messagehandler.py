from discord.ext import commands
import asyncio
import threading
import random
import re


class ListenerCog(commands.Cog, name="listener"):
    def __init__(self, bot):
        self.bot = bot
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.thread.start()
        self.lock = threading.Lock()
        self.msg_counter = 0

    async def has_image_attachment(self, message_content):
        url_pattern = re.compile(
            r"http[s]?://[^\s/$.?#].[^\s]*\.(jpg|jpeg|png|gif)", re.IGNORECASE
        )
        tenor_pattern = re.compile(r"https://tenor.com/view/[\w-]+")
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

    async def generate_response(self, message):
        # image handling
        if await self.has_image_attachment(message):
            image_response = await self.bot.get_cog("image_caption").image_comment(
                message, message.content
            )
            response = await self.bot.get_cog("chatbot").chat_command(
                message, image_response
            )
            return response
        else:
            # No image. Normal text response
            response = await self.bot.get_cog("chatbot").chat_command(
                message, message.content
            )
            return response

    @commands.Cog.listener()
    async def on_message(self, message):
        # if message starts with ".", "/"" or is by the bot - do nothing
        if message.author == self.bot.user or message.content.startswith((".", "/")):
            return

        # if a reply message is not for the bot - do nothing
        if message.mentions and self.bot.user.name not in [
            mention.name for mention in message.mentions
        ]:
            return

        """
		Main On Message Handler
		This part needs to be as basic as possible
		"""
        # if message is channel id argument or DM or
        if (
            message.channel.id in [int(channel_id) for channel_id in self.bot.guild_ids]
            or message.guild is None
        ):
            response = None

            with self.lock:
                self.msg_counter += 1

            msg_count_at_start = self.msg_counter
            async with message.channel.typing():
                future = asyncio.run_coroutine_threadsafe(
                    self.generate_response(message), self.loop
                )
                while not future.done():
                    await asyncio.sleep(1)
                response = future.result()
            msg_count_at_end = self.msg_counter

            if response:
                if msg_count_at_end != msg_count_at_start:
                    with self.lock:
                        self.msg_counter += 1
                    await message.reply(response)
                else:
                    await message.channel.send(response)


async def setup(bot):
    await bot.add_cog(ListenerCog(bot))
