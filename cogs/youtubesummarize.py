import discord
from discord import app_commands
from discord.ext import commands
import langchain

from langchain.document_loaders import YoutubeLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain

import torch


class YoutubeSummaryCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.llm = self.bot.llm

    @app_commands.command(name="youtubesummary", description="Summarize a YouTube video given its URL")
    async def summarize(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()

        # Notifies the user that the bot is processing their command.
        await interaction.followup.send(
            embed=discord.Embed(
                title=f"{interaction.user.display_name} used Youtube Summary 📺",
                description=f"Summarizing {url} \nGenerating response\nPlease wait..",
                color=0x9C84EF
            )
        )
        try:
            # Load transcript
            loader = YoutubeLoader.from_youtube_url(url)
            transcript = loader.load()

            # Split text
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=50)
            texts = text_splitter.split_documents(transcript)

            # Create and configure chain
            chain = load_summarize_chain(llm=self.llm, chain_type="map_reduce", verbose=True)
#             chain.llm_chain.prompt.template = \
#             """### Instruction: 
# Write a 1-3 paragraph summary the following:
# "{text}"
# ### Response:
# 1-3 PARAGRAPH SUMMARY:"""

            # Run the chain and get summary
            summary = chain.run(texts)



            await interaction.followup.send(f'Summary:\n{summary}')

        except Exception as e:
            await interaction.channel.send(f'Sorry, an error occurred: {str(e)}')


async def setup(bot):
    await bot.add_cog(YoutubeSummaryCog(bot))

