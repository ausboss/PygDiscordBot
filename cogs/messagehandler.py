# import discord
# from discord.ext import commands
# from discord import app_commands
# from dotenv import load_dotenv
# import asyncio
# import random
# from datetime import datetime, timedelta
# from discord import InteractionType


# load_dotenv()
# import re

# def embedder(msg):
#     embed = discord.Embed(
#             description=f"{msg}",
#             color=0x9C84EF
#         )
#     return embed


# class ListenerCog(commands.Cog, name="listener"):
#     def __init__(self, bot):
#         self.bot = bot
#         self.listen_only_mode = False  # New variable for tracking listen-only mode
#         self.last_message_times = {}  # Dictionary to store last message time for each channel


#     @app_commands.command(name="listen", description="listen-only mode")
#     async def listen(self, interaction: discord.Interaction, cog: str):
#         if cog.lower() == "on":
#             self.listen_only_mode = True
#         elif cog.lower() == "off":
#             self.listen_only_mode = False
#         else:
#             await interaction.response.send_message(".Invalid argument. Please use `on` or `off`.")
#             return
#         await interaction.response.send_message(f".Listen-only mode is now {'on' if self.listen_only_mode else 'off'}.")


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



#     @commands.Cog.listener()
#     async def on_message(self, message):

#         # Ignore messages from the bot or that start with ".", "/", or are not in the bot's channels.
#         if (
#             message.author == self.bot.user
#             or message.content.startswith((".", "/"))
#             or message.channel.id not in [int(channel_id) for channel_id in self.bot.channel_list]
#         ):
#             return
        
        

#         # Checks if the message is a reply or contains the bot's name.
#         is_reply_to_bot = message.reference and message.reference.resolved.author == self.bot.user
#         mentions_bot = self.bot.user in message.mentions
#         contains_bot_name = self.bot.user.name.lower() in message.clean_content.lower()
#         directed_at_bot = is_reply_to_bot or mentions_bot or contains_bot_name

#         now = datetime.utcnow()

#         if (
#             message.channel.id in self.last_message_times 
#             and now - self.last_message_times[message.channel.id] < timedelta(seconds=10)
#         ):
#             # Last message was less than 10 seconds ago, route to chat_message_nr
#             if await self.has_image_attachment(message):
#                 image_response = await self.bot.get_cog("image_caption").image_comment(message, message.clean_content)
#                 response = await self.bot.get_cog("chatbot").chat_command_nr(message, image_response)
#             else:
#                 response = await self.bot.get_cog("chatbot").chat_command_nr(message, message.clean_content)
#             return

#         self.last_message_times[message.channel.id] = now  # Update last message time

#         # If the message isn't directed at the bot, and handle if it has an image or not sending to chat_command_nr
#         if not directed_at_bot:
#             if await self.has_image_attachment(message):
#                 image_response = await self.bot.get_cog("image_caption").image_comment(message, message.clean_content)
#                 response = await self.bot.get_cog("chatbot").chat_command_nr(message, image_response)
#             else:
#                 response = await self.bot.get_cog("chatbot").chat_command_nr(message, message.clean_content)
#             return

#         # If listen-only mode is enabled, handle accordingly
#         if self.listen_only_mode:
#             if await self.has_image_attachment(message):
#                 image_response = await self.bot.get_cog("image_caption").image_comment(message, message.clean_content)
#                 response = await self.bot.get_cog("chatbot").chat_command_nr(message, image_response)
#             else:
#                 response = await self.bot.get_cog("chatbot").chat_command_nr(message, message.clean_content)
#             return

#         else:
#             # Image handling
#             if await self.has_image_attachment(message):
#                 image_response = await self.bot.get_cog("image_caption").image_comment(message, message.clean_content)
#                 response = await self.bot.get_cog("chatbot").chat_command(message, image_response)
#             else:
#                 # No image. Normal text response
#                 response = await self.bot.get_cog("chatbot").chat_command(message, message.clean_content)

#             if response:
#                 async with message.channel.typing():
#                     await asyncio.sleep(1)  # Simulate some work being done
#                     if random.random() < 0.8:
#                         await message.channel.send(response)
#                     else:
#                         await message.reply(response)


# async def setup(bot):
#     await bot.add_cog(ListenerCog(bot))




import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
from discord import app_commands
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
        #self.listen_only_mode needs to be a dictionary with the guild id as the key and the value as the boolean
        self.listen_only_mode = {int(guild_id): False for guild_id in self.bot.channel_list}

    class ListenOnlyModeSelect(discord.ui.Select):
        def __init__(self, parent):
            self.parent = parent
            options = [
                discord.SelectOption(
                    label="Enable", description="Enable listen-only mode.", emoji="🔊"
                ),
                discord.SelectOption(
                    label="Disable", description="Disable listen-only mode.", emoji="🔇"
                ),
            ]
            super().__init__(
                placeholder="Choose...",
                min_values=1,
                max_values=1,
                options=options,
            )

        async def callback(self, interaction: discord.Interaction):
            channel_id = interaction.channel_id
            if channel_id in self.parent.bot.channel_list:
                if self.values[0] == "Enable":
                    self.parent.listen_only_mode[channel_id] = True
                    await interaction.response.send_message(embed=embedder(f".Listen-only mode is now set to {self.parent.listen_only_mode[channel_id]}"), delete_after=5)
                else:
                    self.parent.listen_only_mode[channel_id] = False
                    await interaction.response.send_message(embed=embedder(f".Listen-only mode is now set to {self.parent.listen_only_mode[channel_id]}"), delete_after=5)
            else:
                await interaction.response.send_message(embed=embedder(f".Listen-only mode is not enabled in this channel"), delete_after=5)

    class ListenOnlyModeView(discord.ui.View):
        def __init__(self, parent):
            super().__init__()
            self.add_item(ListenerCog.ListenOnlyModeSelect(parent))

    # This command will toggle listen-only mode for the bot in the server it is used in.
    @app_commands.command(name="listen", description="listen-only mode")
    async def listen(self, interaction: discord.Interaction):
        view = self.ListenOnlyModeView(self)
        await interaction.response.send_message("Toggle listen-only mode:", view=view)

    # # This command will toggle listen-only mode for the bot in the server it is used in.
    # @app_commands.command(name="listen", description="listen-only mode")
    # async def listen(self, interaction: discord.Interaction, cog: str):
    #     # get channel id and then check if the channel id is in the channel_list and if its True or False
    #     # if its True then set it to False and vice versa
    #     channel_id = interaction.channel_id
    #     if channel_id in self.bot.channel_list:
    #         self.listen_only_mode[channel_id] = not self.listen_only_mode[channel_id]
    #         await interaction.response.send_message(embed=embedder(f".Listen-only mode is now set to {self.listen_only_mode[channel_id]}"), delete_after=5)
    #     else:
    #         await interaction.response.send_message(embed=embedder(f".Listen-only mode is not enabled in this channel"), delete_after=5)



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
    
    async def handle_image_message(self, message, mode=''):
    
        image_response = await self.bot.get_cog("image_caption").image_comment(message, message.clean_content)

        if mode == 'nr':
            response = await self.bot.get_cog("chatbot").chat_command_nr(message, image_response)
        else:
            response = await self.bot.get_cog("chatbot").chat_command(message, image_response)
            if response:
                async with message.channel.typing():
                        await message.reply(response)
            

    async def handle_text_message(self, message, mode=''):
        
        if mode == 'nr':
            response = await self.bot.get_cog("chatbot").chat_command_nr(message, message.clean_content)
        else:
            response = await self.bot.get_cog("chatbot").chat_command(message, message.clean_content)

            if response:
                async with message.channel.typing():
                        await message.reply(response)


    async def set_listen_only_mode_timer(self, channel_id):
        
        # Start the timer
        self.listen_only_mode[channel_id] = True
        print(f"Message Sleep Timer started for channel {channel_id}")
        await asyncio.sleep(10)  # Wait for 10 seconds
        print(f"Message Sleep Timer ended for channel {channel_id}")

        # Reset the listen-only mode
        self.listen_only_mode[channel_id] = False



    @commands.Cog.listener()
    async def on_message(self, message):

        # Ignore messages from the bot or that start with ".", "/", or are not in the bot's channels.
        if (
            message.author == self.bot.user
            or message.content.startswith((".", "/"))
            or message.channel.id not in [int(channel_id) for channel_id in self.bot.channel_list]
        ):
            return

        # We define is_false_positive first.
        is_false_positive = (message.reference and message.reference.resolved.author != self.bot.user and
                             self.bot.user.name.lower() in message.clean_content.lower())
        
        print(f'Is the message a false positive? {is_false_positive}')

        # Checking if the message is a reply to the bot
        is_reply_to_bot = message.reference and message.reference.resolved.author == self.bot.user
        print(f'Is the message a reply to the bot? {is_reply_to_bot}')

        # Checking if the message mentions the bot
        mentions_bot = self.bot.user in message.mentions
        print(f'Does the message mention the bot? {mentions_bot}')

        # Checking if the message contains the bot's name
        contains_bot_name = self.bot.user.name.lower() in message.clean_content.lower()
        print(f'Does the message contain the bot\'s name? {contains_bot_name}')

        # The message is considered directed at the bot if `is_reply_to_bot`, `mentions_bot`, or `contains_bot_name` is true,
        # but `is_false_positive` is not true.
        directed_at_bot = (is_reply_to_bot or mentions_bot or contains_bot_name) and not is_false_positive
        print(f'Is the message directed at the bot? {directed_at_bot}')


        # Determine message type
        message_type = 'nr' if self.listen_only_mode[message.channel.id] or not directed_at_bot else None

        # Handle the message appropriately
        if await self.has_image_attachment(message):
            await self.handle_image_message(message, message_type)
        else:
            await self.handle_text_message(message, message_type)

        # Reset the cooldown timer for the channel if the message is directed at the bot and not in cooldown
        if directed_at_bot and not self.listen_only_mode[message.channel.id]:
            asyncio.create_task(self.set_listen_only_mode_timer(message.channel.id))


async def setup(bot):
    await bot.add_cog(ListenerCog(bot))
