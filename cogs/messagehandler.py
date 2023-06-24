# from discord.ext import commands
# from dotenv import load_dotenv
# import asyncio
# import random

# load_dotenv()
# import re

# print('listener loaded')

# class ListenerCog(commands.Cog, name="listener"):
#     def __init__(self, bot):
#         self.bot = bot

#     async def has_image_attachment(self, message_content):
#         url_pattern = re.compile(r'http[s]?://[^\s/$.?#].[^\s]*\.(jpg|jpeg|png|gif)', re.IGNORECASE)
#         tenor_pattern = re.compile(r'https://tenor.com/view/[\w-]+')
#         for attachment in message_content.attachments:
#             if attachment.filename.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
#                 return True
#             # Check if the message content contains a URL that ends with an image file extension
#         if url_pattern.search(message_content.content):
#             return True
#         # Check if the message content contains a Tenor GIF URL

#         elif tenor_pattern.search(message_content.content):
#             return True
#         else:
#             return False

# @commands.Cog.listener()
# async def on_message(self, message):
#     print('test')

#     # if message starts with ".", "/"" or is by the bot - do nothing
#     if message.author == self.bot.user or message.content.startswith((".", "/")):
#         return

#     name_check_string = message.clean_content.lower()
#     bot_name_lower = self.bot.user.name.lower()
#     # create a list of possible greetings + self.bot.user to use for name checking
#     # if message is a mention of the bot or a reply then continue
#     if message.channel.id in [int(channel_id) for channel_id in self.bot.guild_ids] or message.guild is None:
#         """
#         Main On Message Handler

#         This part needs to be as basic as possible

#         """
#         # if message 
#         if self.bot.user.name in [mention.name for mention in message.mentions] or message.clean_content.startswith(name_check_string):
#             if await self.has_image_attachment(message):
#                 image_response = await self.bot.get_cog("image_caption").image_comment(message)
#                 async with message.channel.typing():
#                     response = await self.bot.get_cog("chatbot").chat_command(message, image_response)
#                     if response:
#                         await message.reply(response)
#             else:
#                 # No image. Normal text response
#                 response = await self.bot.get_cog("chatbot").chat_command(message, message.clean_content)
#                 async with message.channel.typing():
#                     if response:
#                         await message.reply(response)
#                         return
#         else:
#             # if message is not a mention of the bot or a reply then use the no response handler
#             if await self.has_image_attachment(message):
#                 image_response = await self.bot.get_cog("image_caption").image_comment(message)
#                 response = await self.bot.get_cog("chatbot").chat_command_nr(message, message.clean_content)
#             else:
#                 await self.bot.get_cog("chatbot").chat_command_nr(message, message.clean_content)



# async def setup(bot):
#     await bot.add_cog(ListenerCog(bot))
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