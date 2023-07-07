import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import unicodedata
import discord
from discord import app_commands
from discord.ext import commands

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

DEFAULT_SUMMARIZE_PARAMS = {
    "temperature": 1.0,
    "repetition_penalty": 1.0,
    "max_length": 500,
    "min_length": 200,
    "length_penalty": 1.5,
    "bad_words": [
        "\n",
        '"',
        "*",
        "[",
        "]",
        "{",
        "}",
        ":",
        "(",
        ")",
        "<",
        ">",
        "Â",
        "The text ends",
        "The story ends",
        "The text is",
        "The story is",
    ],
}


def embedder(msg):
    embed = discord.Embed(
            description=f"{msg}",
            color=0x9C84EF
        )
    return embed


class TextSummarizerCog(commands.Cog, name="text_summarizer"):

    def __init__(self, bot):
        self.bot = bot
        self.device = device
        self.summarization_transformer = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn").to(self.device)
        self.summarization_tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")

    async def summarize_chunks(self, text: str, params: dict) -> str:
        try:
            return await self.summarize(text, params)
        except IndexError:
            print(
                "Sequence length too large for model, cutting text in half and calling again"
            )
            new_params = params.copy()
            new_params["max_length"] = new_params["max_length"] // 2
            new_params["min_length"] = new_params["min_length"] // 2
            return await self.summarize_chunks(
                text[: (len(text) // 2)], new_params
            ) + self.summarize_chunks(text[(len(text) // 2):], new_params)

    async def summarize(self, text: str, params: dict) -> str:
        # Tokenize input
        inputs = self.summarization_tokenizer(text, return_tensors="pt").to(device)
        token_count = len(inputs[0])

        bad_words_ids = [
            self.summarization_tokenizer(bad_word, add_special_tokens=False).input_ids
            for bad_word in params["bad_words"]
        ]
        summary_ids = self.summarization_transformer.generate(
            inputs["input_ids"],
            num_beams=2,
            max_length=max(token_count, int(params["max_length"])),
            min_length=min(token_count, int(params["min_length"])),
            repetition_penalty=float(params["repetition_penalty"]),
            temperature=float(params["temperature"]),
            length_penalty=float(params["length_penalty"]),
            bad_words_ids=bad_words_ids,
        )
        summary = self.summarization_tokenizer.batch_decode(
            summary_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True
        )[0]
        summary = await self.normalize_string(summary)
        return summary

    async def normalize_string(self, input: str) -> str:
        output = " ".join(unicodedata.normalize("NFKC", input).strip().split())
        return output

    async def local_summarize(self, text, params=None):
        if params is None:
            params = DEFAULT_SUMMARIZE_PARAMS.copy()

        print("Summary input:", text, sep="\n")
        summary = await self.summarize_chunks(text, params)
        print("Summary output:", summary, sep="\n")
        return summary

    # this command will summarize text and send it back to the user. 
    @app_commands.command(name="summarizetext", description="summarize text")
    async def summarize_text(self, interaction: discord.Interaction, input_text: str):
        truncated_text = input_text[:30] + "..." if len(input_text) > 30 else input_text
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{interaction.user.display_name} used Summarize 📃",
                description=f"Instructions: {truncated_text}\nGenerating response\nPlease wait..",
                color=0x9C84EF,
            )
        )

        summary = await self.summarize(input_text, DEFAULT_SUMMARIZE_PARAMS.copy())

        await interaction.channel.send(summary)


async def setup(bot):
    await bot.add_cog(TextSummarizerCog(bot))
