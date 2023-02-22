import re
import json
import requests
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import nltk
from nltk.tokenize import word_tokenize
nltk.download('punkt')

# load environment variables
load_dotenv()
ENDPOINT = os.getenv("ENDPOINT")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# Put the configuration settings in the api
model_config = {
    "max_context_length": 1488,
    "max_length": 50,
    "rep_pen": 1.03,
    "rep_pen_range": 1024,
    "rep_pen_slope": 0.9,
    "temperature": 0.6,
    "tfs": 0.9,
    "top_p": 0.9,
    "typical": 1,
    "sampler_order": [6, 0, 1, 2, 3, 4, 5]
}
# Send a PUT request to modify the settings
response = requests.put(f"{ENDPOINT}/config", json=model_config)

class Chatbot:
    def __init__(self, char_filename):
        # read character data from JSON file
        with open(char_filename, "r") as f:
            data = json.load(f)
            self.char_name = data["name"]
            self.char_persona = data["char_persona"]
            self.char_greeting = data["char_greeting"]
            self.world_scenario = data["world_scenario"]
            self.example_dialogue = data["example_dialogue"]

        # initialize conversation history and character information
        self.conversation_history = f"<START>\n{self.char_name}: {self.char_greeting}\n"
        self.character_info = f"{self.char_name}'s Persona: {self.char_persona}\nScenario: {self.world_scenario}\n"
        self.num_lines_to_keep = 20

    def prompt_tokens(self, prompt):
        # tokenize the prompt and return the number of tokens
        tokens = word_tokenize(prompt["prompt"])
        num_tokens = len(tokens)
        return num_tokens

    def save_conversation(self, message, message_content, bot):
        # add user message to conversation history
        self.conversation_history += f'{message.author.name}: {message_content}\n'

        # define the prompt
        prompt = {
            "prompt": self.character_info + '\n'.join(
                self.conversation_history.split('\n')[-self.num_lines_to_keep:]) + f'{self.char_name}:',
        }

        # get the number of tokens in the prompt
        tokens = self.prompt_tokens(prompt)
        print(tokens)

        # send a post request to the API endpoint
        response = requests.post(f"{ENDPOINT}/api/v1/generate", json=prompt)

        # check if the request was successful
        if response.status_code == 200:
            # get the results from the response
            results = response.json()['results']
            text = results[0]['text']
            # split the response to remove excess dialogue
            parts = re.split(r'\n[a-zA-Z]', text)[:1]
            response_text = parts[0][1:]
            # add bot response to conversation history
            self.conversation_history = self.conversation_history + f'{self.char_name}: {response_text}\n'
        else:
            print("endpoint issue")

        return response_text


class ChatbotCog(commands.Cog, name="chatbot"):
    def __init__(self, bot):
        self.bot = bot
        self.chatbot = Chatbot("chardata.json")

    @commands.command(name="chat")
    async def chat_command(self, message: discord.Message, message_content, bot) -> None:
        # get response message from chatbot and return it
        response_message = self.chatbot.save_conversation(message, message_content, bot)
        return response_message


async def setup(bot):
    # add chatbot cog to bot
    await bot.add_cog(ChatbotCog(bot))
