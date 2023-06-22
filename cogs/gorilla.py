import discord
from discord import app_commands
from discord.ext import commands
import openai
import urllib.parse

openai.api_key = "EMPTY" # Key is ignored and does not matter
openai.api_base = "http://34.132.127.197:8000/v1"



class GorillaLLMCog(commands.Cog, name="gorilla_llm"):
    def __init__(self, bot):
        self.bot = bot
        self.model = "gorilla-7b-hf-v0"

    # Report issues
    async def raise_issue(self, e, model, prompt):
        issue_title = urllib.parse.quote("[bug] Hosted Gorilla: <Issue>")
        issue_body = urllib.parse.quote(f"Exception: {e}\nFailed model: {model}, for prompt: {prompt}")
        issue_url = f"https://github.com/ShishirPatil/gorilla/issues/new?assignees=&labels=hosted-gorilla&projects=&template=hosted-gorilla-.md&title={issue_title}&body={issue_body}"
        print(f"An exception has occurred: {e} \nPlease raise an issue here: {issue_url}")


    @commands.command(name="gorilla_query")
    async def gorilla_query(self, interaction: discord.Interaction) -> None:
        try:
            prompt = interaction
            completion = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            gorilla_message = completion.choices[0].message.content
        except Exception as e:
            await self.raise_issue(e, self.model, interaction)
            gorilla_message = f"There was an error. Additional information: {e}"
        try:
            raw_message_no_code = gorilla_message.split('<<<code>>>:')[0]
            clean_message = raw_message_no_code.replace("<<<", "\n").replace(">>>", "").replace("1.", "\n1.")
            message_code = f"code:\n```{gorilla_message.split('<<<code>>>:')[1]}```"
            gorilla_message_final = f"{clean_message}\n{message_code}"
        except:
            clean_message = raw_message_no_code.replace("<<<", "\n").replace(">>>", "").replace("1.", "\n1.")
            message_code = ""
            gorilla_message_final = f"{clean_message}\n{message_code}"

        return gorilla_message_final




async def setup(bot):
    await bot.add_cog(GorillaLLMCog(bot))
