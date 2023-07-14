import discord
from discord import app_commands
from discord.ext import commands

import os
from langchain.tools import DuckDuckGoSearchRun
from dotenv import load_dotenv

# Load .env file
load_dotenv()

OPENAI = os.getenv('OPENAI')

def embedder(msg):
    embed = discord.Embed(
            description=f"{msg}",
            color=0x9C84EF
        )
    return embed



class AgentCommands(commands.Cog, name="agent_commands"):
    def __init__(self, bot):
        self.bot = bot
        self.llm = ""

        self.search = DuckDuckGoSearchRun() # DuckDuckGo tool

    
    @app_commands.command(name="searchweb", description="Query Web")
    async def search_web(self, interaction: discord.Interaction, prompt: str):

        response = self.search(prompt)

        await interaction.channel.send(response)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info("Agent Commands cog loaded.")









async def setup(bot):
    await bot.add_cog(AgentCommands(bot))
