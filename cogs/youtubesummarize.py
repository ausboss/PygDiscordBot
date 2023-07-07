import discord
from discord.ext import commands

def embedder(msg):
    embed = discord.Embed(
            description=f"{msg}",
            color=0x9C84EF
        )
    return embed

class YoutubeSummarize(commands.Cog, name="generic_cog"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="generic_command")
    async def generic_function(self, ctx, *, text):

        await ctx.send(embed=embedder(text))

    @app_commands.command(name="generic_command", description="process text")
    async def generic_process(self, interaction: discord.Interaction, input_text: str):


        await self.generic_function(interaction, text=input_text)


async def setup(bot):
    await bot.add_cog(ChatbotCog(bot))
