import re
import json
import requests
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import nltk

nltk.download('punkt')  # download the punkt tokenizer if you haven't already




load_dotenv()
ENDPOINT = os.getenv("ENDPOINT")

class Chatbot:
    def __init__(self, char_filename):
        with open(char_filename, "r") as f:
            data = json.load(f)
            self.char_name = data["char_name"]
            self.char_persona = data["char_persona"]
            self.char_greeting = data["char_greeting"]
            self.world_scenario = data["world_scenario"]
            self.example_dialogue = data["example_dialogue"]

        self.history = [
            f"{self.char_name}\n{self.char_name}'s Persona: {self.char_persona}\nWorld Scenario: {self.world_scenario}\n{self.example_dialogue}\n{self.char_name}: {self.char_greeting}\n"]
        self.prompt = None


    def generate_response(self):
        # Generate response based on the user's message and the prompt
        response = requests.post(f"{ENDPOINT}/api/v1/generate", json=self.prompt)
        results = response.json()['results']

        # extract the correct bot reponse from the large json of information
        text = results[0]['text']
        parts = re.split(r'\n[a-zA-Z]', text)[:1]
        response_text = parts[0][1:]
        if len(self.history) > 30:
            self.history = self.history[-10:]
        return response_text

    def add_message(self, speaker, message_content):
        self.history.append(f"{speaker}: {message_content}")

    def save_conversation(self, message, message_content, bot):
        message_content = message_content.replace(f"<@{bot.user.id}>", "").strip()
        self.add_message(message.author.name, message_content)
        print(f"{message.author.name}: {message_content}")

        prompt = f"{self.char_name}:"

        # separate each part of the history and prompt on a new line
        if len(self.history) < 26:
            # Include char_name and char_persona at the beginning of the history
            history_lines = [f"{self.char_name}\n", f"{self.char_name}'s Persona: {self.char_persona}\n"]
            history_lines.extend(self.history)
            history = '\n'.join(history_lines)
        else:
            # Include char_name and char_persona at the beginning of the history
            history_lines = [f"{self.char_name}\n", f"{self.char_name}'s Persona: {self.char_persona}\n",
                             f"World Scenario: {self.world_scenario}\n", f"{self.char_greeting}\n"]
            for line in self.history:
                if f"{self.char_name}: {self.char_greeting}" not in line:
                    history_lines.append(line)
            history = '\n'.join(history_lines)

        # set the new prompt by joining the history and prompt together
        self.prompt = {"prompt": f"{history}\n{prompt}", "use_story": False, "use_memory": False,
                       "use_authors_note": False, "use_world_info": False, "max_context_length": 1400,
                       "max_length": 70, "rep_pen": 1.05, "rep_pen_range": 800, "rep_pen_slope": 0.9,
                       "temperature": 0.5, "tfs": 0.9, "top_a": 0, "top_k": 0, "top_p": 0.9,
                       "typical": 1.0, "sampler_order": [6, 0, 1, 2, 3, 4, 5], "frmttriminc": True, "frmtrmblln": True}
        prompt_tokens = nltk.word_tokenize(self.prompt["prompt"])
        num_prompt_tokens = len(prompt_tokens)
        print(num_prompt_tokens)
        print(self.prompt)
        print(len(self.history))
        bot_response = self.generate_response()
        self.add_message(self.char_name, bot_response)
        print(f"{self.char_name}: {bot_response}")
        return bot_response


# Here we name the cog and create a new class for the cog.
class ChatbotCog(commands.Cog, name="chatbot"):
    def __init__(self, bot):
        self.bot = bot
        self.chatbot = Chatbot("chardata.json")

    @commands.command(name="chat")
    async def chat_command(self, message: discord.Message, message_content, bot) -> None:
        response = self.chatbot.save_conversation(message, message_content, bot)
        return response


async def setup(bot):
    await bot.add_cog(ChatbotCog(bot))
