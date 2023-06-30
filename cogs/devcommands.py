import discord
from discord import app_commands
from discord.ext import commands
import os


def embedder(msg):
    embed = discord.Embed(
            description=f"{msg}",
            color=0x9C84EF
        )
    return embed


class ReloadCogSelect(discord.ui.Select):
    def __init__(self, parent):
        self.parent = parent
        options = [
            discord.SelectOption(label=cog[:-3], description="")
            for cog in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}")
            if cog.endswith('.py')
        ]
        super().__init__(
            placeholder="Choose a cog to reload...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
            cog = self.values[0]
            await self.parent.bot.reload_extension(f"cogs.{cog}")
            await interaction.response.send_message(f"Reloaded {cog} cog.")

class ReloadCogView(discord.ui.View):
    def __init__(self, parent):
        super().__init__()
        self.add_item(ReloadCogSelect(parent))


class DevCommands(commands.Cog, name="dev_commands"):
    def __init__(self, bot):
        self.bot = bot
        self.chanel_list = bot.channel_list
        self.endpoint = bot.endpoint

    @app_commands.command(name="reload", description="Reload a cog")
    async def reload(self, interaction: discord.Interaction):
        view = ReloadCogView(self)
        await interaction.response.send_message("Select a cog to reload:", view=view)




    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info("Dev Commands cog loaded.")

    @commands.command(name='sync', description='sync up')
    async def sync(self, interaction: discord.Interaction) -> None:
        await self.bot.tree.sync()

    @app_commands.command(name="test", description="Test command")
    async def test(self, interaction: discord.Interaction):
        await interaction.response.send_message("Test passed.", delete_after=3)



async def setup(bot):
    await bot.add_cog(DevCommands(bot))
