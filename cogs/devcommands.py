import discord
from discord import app_commands
from discord.ext import commands



def embedder(msg):
    embed = discord.Embed(
            description=f"{msg}",
            color=0x9C84EF
        )
    return embed

class DevCommands(commands.Cog, name="dev_commands"):
    def __init__(self, bot):
        self.bot = bot
        self.chanel_list = bot.channel_list
        self.endpoint = bot.endpoint

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info("Dev Commands cog loaded.")

    @commands.command(name='sync', description='sync up')
    async def sync(self, interaction: discord.Interaction) -> None:
        await self.bot.tree.sync()

    @app_commands.command(name="test", description="Test command")
    async def test(self, interaction: discord.Interaction):
        await interaction.response.send_message("Test passed.", delete_after=3)

    @app_commands.command(name="reload", description="reload cog")
    async def reload(self, interaction: discord.Interaction, cog: str):
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
            await interaction.response.send_message(embed=embedder(f"Reloaded `{cog}`"), delete_after=3)
        except Exception:
            await interaction.response.send_message(embed=embedder(f"Reloaded `{cog}`"), delete_after=3)

    async def embedder(self, msg):
        embed = discord.Embed(
                description=f"{msg}",
                color=0x9C84EF
            )
        return embed





async def setup(bot):
    await bot.add_cog(DevCommands(bot))
