import asyncio
from datetime import datetime, timedelta
import re
import discord
from discord.ext import commands
from discord import app_commands

# from helpers.db_manager import log_message

SLEEPTIMER = 2
WAITTIMER = 45


def embedder(msg):
    embed = discord.Embed(description=f"{msg}", color=0x9C84EF)
    return embed


class ListenerCog(commands.Cog, name="listener"):
    def __init__(self, bot):
        self.bot = bot
        self.llm = self.bot.llm
        self.aliases = []
        # self.aliases = self.bot.config['ALIASES']
        # create a dictionary of messages where the channel id is the key and the value is the message
        self.message_dict = {}
        # self.listen_only_mode needs to be a dictionary with the guild id as the key and the value as the boolean
        self.listen_only_mode = {
            str(guild_id): False for guild_id in self.bot.guild_ids
        }
        # self.bot.sent_last_message = {str(channel_id): True for channel_id in self.bot.channel_list}
        self.timer_running = {}

        self.ping_mode = self.bot.always_reply

    # create a function that will take a message and add it to the message dictionary wit the channel id as the key. if the key already exists, it will append the message to the list of messages
    async def add_message_to_dict(self, message, message_content):
        if str(message.channel.id) in self.message_dict:
            self.message_dict[str(message.channel.id)].append(
                f"{message.author.display_name}: {message_content}"
            )
        else:
            self.message_dict[str(message.channel.id)] = [
                f"{message.author.display_name}: {message_content}"
            ]

    # # function that will send the list of messages for a channel to the logic cog
    # async def send_message_list(self, channel_id):
    #     # get the list of messages for the channel
    #     message_list = self.message_dict[str(channel_id)]
    #     print(f"message_list: {message_list}")
    #     # join message list by \n
    #     message_list = "\n".join(message_list)
    #     print(f" joined message_list: {message_list}")

    #     # send the prompt to the logic cog
    #     response = await self.bot.get_cog("extra_logic").my_turn(message_list)
    #     # return the response
    #     return response

    # async def set_timer(self, channel_id):
    #     if not self.timer_running.get(channel_id, False):
    #         self.timer_running[channel_id] = True

    #         if not self.bot.sent_last_message.get(channel_id, False):
    #             print(f"Message wait Timer started for channel {channel_id}")
    #             await asyncio.sleep(WAITTIMER)
    #             print(f"Message wait Timer ended for channel {channel_id}")

    #             # Check if self.bot.sent_last_message is still False for the channel
    #             if not self.bot.sent_last_message.get(channel_id, False):
    #                 bot_turn = await self.send_message_list(channel_id)
    #                 if bot_turn and len(self.bot.chat_participants[str(channel_id)]) == 0:
    #                 # if bot_turn or len(self.bot.chat_participants[str(channel_id)]) == 2:
    #                     channel = self.bot.get_channel(channel_id)
    #                     async with channel.typing():
    #                         message = await self.bot.get_cog("chatbot").force_generate_message(str(channel_id))
    #                         response_obj = await channel.send(message)
    #                         self.bot.sent_last_message[str(channel_id)] = True
    #                         await log_message(response_obj)
    #                         bot_turn = False

    #         self.timer_running[channel_id] = False

    # Create a select menu for the listen-only mode command
    class ListenOnlyModeSelect(discord.ui.Select):
        def __init__(self, parent):
            self.parent = parent
            options = [
                discord.SelectOption(
                    label="Enable", description="Enable listen-only mode.", emoji="🙊"
                ),
                discord.SelectOption(
                    label="Disable", description="Disable listen-only mode.", emoji="🐵"
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
            if channel_id in self.parent.bot.guild_ids:
                if self.values[0] == "Enable":
                    self.parent.listen_only_mode[str(channel_id)] = True
                    await interaction.response.send_message(
                        embed=embedder(
                            f".Listen-only mode is now set to {self.parent.listen_only_mode[channel_id]}"
                        ),
                        delete_after=5,
                    )
                else:
                    self.parent.listen_only_mode[str(channel_id)] = False
                    await interaction.response.send_message(
                        embed=embedder(
                            f".Listen-only mode is now set to {self.parent.listen_only_mode[channel_id]}"
                        ),
                        delete_after=5,
                    )
            else:
                await interaction.response.send_message(
                    embed=embedder(f".Listen-only mode is not enabled in this channel"),
                    delete_after=5,
                )

    # Create a view for the listen-only mode command
    class ListenOnlyModeView(discord.ui.View):
        def __init__(self, parent):
            super().__init__()
            self.add_item(ListenerCog.ListenOnlyModeSelect(parent))

    # This command will toggle listen-only mode for the bot in the server it is used in.
    @app_commands.command(name="listen", description="listen-only mode")
    async def listen(self, interaction: discord.Interaction):
        view = self.ListenOnlyModeView(self)
        await interaction.response.send_message("Toggle listen-only mode:", view=view)

    # Create a select menu for the ping mode command
    class PingModeSelect(discord.ui.Select):
        def __init__(self, parent):
            self.parent = parent
            options = [
                discord.SelectOption(
                    label="Enable", description="Enable ping mode.", emoji="🔔"
                ),
                discord.SelectOption(
                    label="Disable", description="Disable ping mode.", emoji="🔕"
                ),
            ]
            super().__init__(
                placeholder="Choose...",
                min_values=1,
                max_values=1,
                options=options,
            )

        async def callback(self, interaction: discord.Interaction):
            if self.values[0] == "Enable":
                self.parent.ping_mode = True
                await interaction.response.send_message(
                    embed=embedder(f".Ping mode is now set to {self.parent.ping_mode}"),
                    delete_after=5,
                )
            else:
                self.parent.ping_mode = False
                await interaction.response.send_message(
                    embed=embedder(f".Ping mode is now set to {self.parent.ping_mode}"),
                    delete_after=5,
                )

    # This command will switch the bot to ping mode, where it will respond to every message sent in the channel.
    @app_commands.command(name="pingmode", description="ping mode")
    async def pingmode(self, interaction: discord.Interaction):
        self.ping_mode = True
        await interaction.response.send_message(
            embed=embedder(f".Ping mode is now set to {self.ping_mode}"), delete_after=5
        )

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

    async def handle_image_message(self, message, mode=""):
        # await log_message(message)
        image_response = await self.bot.get_cog("image_caption").image_comment(
            message, message.clean_content
        )

        if mode == "nr":
            await self.bot.get_cog("chatbot").chat_command_nr(
                message.author.display_name, message.channel.id, image_response
            )
            # self.bot.sent_last_message[str(message.channel.id)] = False
            await self.add_message_to_dict(message, image_response)
            # await self.set_timer(message.channel.id)
        else:
            async with message.channel.typing():
                response = await self.bot.get_cog("chatbot").chat_command(
                    message.author.display_name,
                    message.channel.id,
                    image_response,
                    message,
                )
                await self.add_message_to_dict(message, image_response)
                if response:
                    # If the response is more than 2000 characters, split it
                    chunks = [
                        response[i : i + 1998] for i in range(0, len(response), 1998)
                    ]
                    for chunk in chunks:
                        print(chunk)
                        response_obj = await message.channel.send(chunk)
                        await self.add_message_to_dict(
                            response_obj, response_obj.clean_content
                        )
                        # self.bot.sent_last_message[str(message.channel.id)] = True
                        # await log_message(response_obj)

    async def handle_text_message(self, message, mode=""):
        # await log_message(message)
        if mode == "nr":
            await self.bot.get_cog("chatbot").chat_command_nr(
                message.author.display_name, message.channel.id, message.clean_content
            )
            # self.bot.sent_last_message[str(message.channel.id)] = False
            await self.add_message_to_dict(message, message.clean_content)
            # await self.set_timer(message.channel.id)
        else:
            response = await self.bot.get_cog("chatbot").chat_command(
                message.author.display_name,
                message.channel.id,
                message.clean_content,
                message,
            )
            await self.add_message_to_dict(message, message.clean_content)
            if response:
                async with message.channel.typing():
                    # If the response is more than 2000 characters, split it
                    chunks = [response[i : i + 1998] for i in range(0, len(response), 1998)]
                    for chunk in chunks:
                        print(chunk)
                        response_obj = await message.channel.send(chunk)
                        await self.add_message_to_dict(
                            response_obj, response_obj.clean_content
                        )
                        # self.bot.sent_last_message[str(message.channel.id)] = True
                        # await log_message(response_obj)

    async def set_listen_only_mode_timer(self, channel_id):
        # Start the timer
        self.listen_only_mode[str(channel_id)] = True
        print(f"Message Sleep Timer started for channel {channel_id}")
        await asyncio.sleep(SLEEPTIMER)  # Wait for 10 seconds
        print(f"Message Sleep Timer ended for channel {channel_id}")

        # Reset the listen-only mode
        self.listen_only_mode[str(channel_id)] = False

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from the bot or that start with ".", "/", or are not in the bot's channels.
        if message.author == self.bot.user or message.content.startswith((".", "/")):
            return

        if (
            message.channel.id
            not in [int(channel_id) for channel_id in self.bot.guild_ids]
            and message.guild is not None
        ):
            return

        if not self.ping_mode:
            # We define is_false_positive first.
            is_false_positive = (
                message.reference
                and message.reference.resolved.author != self.bot.user
                and self.bot.user.name.lower() in message.clean_content.lower()
            )

            # Checking if the message is a reply to the bot
            is_reply_to_bot = (
                message.reference and message.reference.resolved.author == self.bot.user
            )

            # Checking if the message mentions the bot
            mentions_bot = self.bot.user in message.mentions

            # Checking if the message contains the bot's name or any of the aliases
            contains_bot_name = (
                self.bot.user.name.lower() in message.clean_content.lower()
                or any(
                    alias.lower() in message.clean_content.lower()
                    for alias in self.aliases
                )
            )

            # The message is considered directed at the bot if `is_reply_to_bot`, `mentions_bot`, or `contains_bot_name` is true,
            # but `is_false_positive` is not true.
            directed_at_bot = (
                is_reply_to_bot or mentions_bot or contains_bot_name
            ) and not is_false_positive
        else:
            directed_at_bot = True

        # Determine message type
        message_type = (
            "nr"
            if self.listen_only_mode[str(message.channel.id)] or not directed_at_bot
            else None
        )

        # Handle the message appropriately
        if await self.has_image_attachment(message):
            await self.handle_image_message(message, message_type)
        else:
            await self.handle_text_message(message, message_type)

        # Reset the cooldown timer for the channel if the message is directed at the bot and not in cooldown
        if directed_at_bot and not self.listen_only_mode[str(message.channel.id)]:
            asyncio.create_task(
                self.set_listen_only_mode_timer(str(message.channel.id))
            )


async def setup(bot):
    await bot.add_cog(ListenerCog(bot))
