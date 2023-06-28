import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import unicodedata
import discord
from discord import app_commands
from discord.ext import commands


def embedder(msg):
    embed = discord.Embed(
            description=f"{msg}",
            color=0x9C84EF
        )
    return embed


class TextSummarizerCog(commands.Cog, name="text_summarizer"):
    def __init__(self, bot):
        self.bot = bot
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.summarization_transformer = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn").to(self.device)
        self.summarization_tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")

    @commands.command(name="summarize")
    async def summarize(self, ctx, *, text):
        # Tokenize input
        inputs = self.summarization_tokenizer(text, return_tensors="pt").to(self.device)
        # Generate summary
        summary_ids = self.summarization_transformer.generate(inputs["input_ids"], num_beams=4, max_length=100, length_penalty=2.0, min_length=30, no_repeat_ngram_size=3)
        summary = self.summarization_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        # Send summary
        return summary
        

    # this command will summarize text and send it back to the user. 
    @app_commands.command(name="summarizetext", description="summarize text")
    async def summarize_text(self, interaction: discord.Interaction, input_text: str):
        # get the text to summarize
        text = input_text
        # summarize the text
        summary = self.summarize(text, DEFAULT_SUMMARIZE_PARAMS)
        # send the summary back to the user
        await interaction.response.send_message(summary, ephemeral=True)
        



async def setup(bot):
    await bot.add_cog(TextSummarizerCog(bot))
