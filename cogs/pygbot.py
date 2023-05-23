import re
import json
import requests
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from typing import Any, List, Mapping, Optional
import langchain
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory, ChatMessageHistory
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.llms.base import LLM
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    PromptTemplate,
)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
import requests
import os
from discord.ext import commands
from discord.ext.commands import Bot


endpoint = ""

# configuration settings for the api
model_config = {
    "prompt" : "hello world",
    "use_story": False,
    "use_authors_note": False,
    "use_world_info": False,
    "use_memory": False,
    "max_context_length": 1800,
    "max_length": 120,
    "rep_pen": 1.02,
    "rep_pen_range": 1024,
    "rep_pen_slope": 0.9,
    "temperature": 0.6,
    "tfs": 0.9,
    "top_p": 0.9,
    "typical": 1,
    "sampler_order": [6, 0, 1, 2, 3, 4, 5]
}

def embedder(msg):
    embed = discord.Embed(
            description=f"{msg}",
            color=0x9C84EF
        )
    return embed




def kobold_api_call(prompt: str) -> str:
    global endpoint
    url = endpoint + "/api/v1/generate"
    data = {"prompt": prompt}
    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()["results"]

class KoboldLLM(LLM):
    
    @property
    def _llm_type(self) -> str:
        return "kobold"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> str:
        if stop is not None:
            raise ValueError("stop kwargs are not permitted.")
        
        # Call the Kobold API here and get the results
        results = kobold_api_call(prompt)

        # Get the first result
        result = results[0]["text"]
        
        # Split the result into lines
        bot_lines = result.split("\n")[0].strip()
        # print(f"Kobold: {result} bot_lines: {bot_lines}")
    
        return bot_lines
    
    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {}




class Chatbot:
    def __init__(self, char_filename, bot):
        self.prompt = None
        self.endpoint = endpoint
        # Send a PUT request to modify the settings
        requests.put(f"{self.endpoint}/api/v1/generate", json=model_config)
        # read character data from JSON file
        with open(char_filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.char_name = data["char_name"]
            self.char_persona = data["char_persona"]
            self.char_greeting = data["char_greeting"]
            self.world_scenario = data["world_scenario"]
            self.example_dialogue = data["example_dialogue"]

        # initialize conversation history and character information
        self.convo_filename = None
        self.llm = KoboldLLM()
        self.ai_prefix = self.char_name
        self.human_prefix = ""
        self.memory = ConversationBufferMemory(ai_prefix=self.char_name)
        self.num_lines_to_keep = 20




    async def set_convo_filename(self, convo_filename):
        # set the conversation filename and load conversation history from file
        self.convo_filename = convo_filename
        if not os.path.isfile(convo_filename):
            # create a new file if it does not exist
            with open(convo_filename, "w", encoding="utf-8") as f:
                f.write("<START>\n")
        with open(convo_filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
            num_lines = min(len(lines), self.num_lines_to_keep)
            self.conversation_history = "<START>\n" + "".join(lines[-num_lines:])

    async def save_conversation(self, message, message_content):
        print(f"message.author.name: {message.author.name}")
        self.human_prefix = message.author.name
        self.memory.human_prefix = message.author.name
        self.template = f"""{self.char_name}'s Persona: {self.char_persona}
        Scenario: {self.world_scenario}
        {self.example_dialogue}
        {{history}}
        {message.author.name}: {{input}}
        {self.char_name}:"""
        
        self.PROMPT = PromptTemplate(input_variables=["history", "input"], template=self.template)
        self.conversation = ConversationChain(prompt=self.PROMPT, llm=self.llm, verbose=True, memory=self.memory)

        response = self.conversation.run(input=message.clean_content).strip()
        with open(self.convo_filename, "a", encoding="utf-8") as f:
            f.write(f'{message.author.name}: {message_content}\n')
            f.write(f'{self.char_name}: {response}\n')  # add a separator between

        return response


class ChatbotCog(commands.Cog, name="chatbot"):
    def __init__(self, bot):
        self.bot = bot
        self.chatlog_dir = bot.chatlog_dir
        self.chatbot = Chatbot("chardata.json", bot)

        # create chatlog directory if it doesn't exist
        if not os.path.exists(self.chatlog_dir):
            os.makedirs(self.chatlog_dir)


    # Normal Chat handler
    @commands.command(name="chat")
    async def chat_command(self, message, message_content) -> None:
        if message.guild:
            server_name = message.channel.name
        else:
            server_name = message.author.name
        chatlog_filename = os.path.join(self.chatlog_dir, f"{self.chatbot.char_name}_{server_name}_chatlog.log")
        if message.guild and self.chatbot.convo_filename != chatlog_filename or \
                not message.guild and self.chatbot.convo_filename != chatlog_filename:
            await self.chatbot.set_convo_filename(chatlog_filename)
        response = await self.chatbot.save_conversation(message, message.clean_content)
        return response


async def setup(bot):
    # add chatbot cog to bot
    await bot.add_cog(ChatbotCog(bot))