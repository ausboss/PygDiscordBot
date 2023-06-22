import re
import json
import requests
import asyncio
from typing import Any, List, Mapping, Optional

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Bot

import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings
import uuid
import langchain
from langchain.chains import ConversationChain, LLMChain, LLMMathChain, TransformChain, SequentialChain
from langchain.chat_models import ChatOpenAI
from langchain.docstore import InMemoryDocstore
from langchain.llms.base import LLM, Optional, List, Mapping, Any
from langchain.embeddings.openai import OpenAIEmbeddings
from textwrap import dedent
from langchain.memory import (
    ChatMessageHistory,
    ConversationBufferMemory,
    ConversationBufferWindowMemory,
    ConversationSummaryBufferMemory,
    VectorStoreRetrieverMemory,
)
from langchain.prompts.prompt import PromptTemplate
from langchain.schema import messages_from_dict, messages_to_dict
from langchain.vectorstores import Chroma
from langchain.agents import load_tools
from langchain.agents import initialize_agent
import os
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from dotenv import load_dotenv
from memory.custom_memory import CustomBufferWindowMemory

import os

Kobold_api_url = str(os.getenv("ENDPOINT")).rstrip("/")

print("Endpoint used:")
print(str(os.getenv("ENDPOINT")).rstrip("/") + "/api/v1/generate")

def embedder(msg):
    embed = discord.Embed(
            description=f"{msg}",
            color=0x9C84EF
        )
    return embed


class KoboldApiLLM(LLM):
    @property
    def _llm_type(self) -> str:
        return "custom"

    def _call(self, prompt: str, stop: Optional[List[str]]=None) -> str:
        response = requests.post(
            Kobold_api_url + "/api/v1/generate",
            json = {
                "prompt": prompt,
                "use_story": False,
                "use_authors_note": False,
                "use_world_info": False,
                "use_memory": False,
                "max_context_length": 1800,
                "max_length": 512,
                "rep_pen": 1.08,
                "rep_pen_range": 1024,
                "rep_pen_slope": 0.9,
                "temperature": 0.5,
                "tfs": 0.9,
                "top_p": 0.7,
                "frmttriminc": True,
                "typical": 1,
                "sampler_order": [6, 0, 1, 2, 3, 4, 5]
            }
        )
        response.raise_for_status()

        return response.json()["results"][0]["text"].strip()

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {

        }


    
class Chatbot:
    def __init__(self, char_filename, bot):
        self.stop_token = "</s>"
        self.bot = bot
        self.histories = {}  # Initialize the history dictionary
        self.llm = KoboldApiLLM()
        self.stop_names = bot.stop_names


        # read character data from JSON file
        with open(char_filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.char_name = data["char_name"]
            self.char_persona = data["char_persona"]
            self.char_greeting = data["char_greeting"]
            self.world_scenario = data["world_scenario"]
            self.example_dialogue = data["example_dialogue"]
        self.history = "[Beginning of Conversation]"
        



    async def get_memory_for_channel(self, channel_id):
        """Get the memory for the channel with the given ID. If no memory exists yet, create one."""
        if channel_id not in self.histories:
            self.histories[channel_id] = CustomBufferWindowMemory(k=10, memory_key="chat_history")
        return self.histories[channel_id]


    async def remove_char_name_from_string(self, string):
        prefix_to_remove = self.char_name + "@"

        if string.startswith(prefix_to_remove):
            return string[len(prefix_to_remove):].lstrip()  # lstrip() is used to remove any leading whitespace
        else:
            return string


    
    #create a function that will check if a name.lower() is in the self.stop_names list. If not it will add it to the list
    async def check_stop_names(self, name):
        if name.lower() not in self.stop_names:
            self.stop_names.append(name.lower())
        return name

    #function that will check if an item from the list "\n" + name.lower() + ":" is in a string. if so it will split it and return everything before that to prevent the bot from responding as others.
    async def use_stop_names(self, string):
        for name in self.stop_names:
            check_name = "\n" + name.lower() + ":"
            if "\n" + name.lower() + ":" in string:
                return string.split("\n" + name.lower() + ":")[0]
        return string



    async def generate_response(self, message, message_content) -> None:

        channel_id = str(message.channel.id)
        name = await self.check_stop_names(message.author.display_name)

        memory = await self.get_memory_for_channel(channel_id)
        # save the conversation to the chatlog 
        self.template = f"""
### Instructions:
The following is group chat. Use the provided input for context. Only reply as {self.char_name}.

### Input:
{self.char_persona}
Current conversation:
{self.char_greeting}
{memory.load_memory_variables('chat_history')['chat_history']}
{{input}}

### Response:
Tensor:"""
        self.PROMPT = PromptTemplate(input_variables=["input"], template=self.template)
        self.conversation = LLMChain(
            prompt=self.PROMPT,
            llm=self.llm,
            verbose=True
        )
        final_message = await self.remove_char_name_from_string(message_content)
        formatted_message = f"{name}: {final_message}"

        # first, add the user's message to the memory
        # self.memory.add_user_message(formatted_message)

        # then, generate the AI's response
        result = self.conversation(formatted_message)

        response = result["text"].split("### Response:")[0]
        result_text = result["text"]
        trimmed = await self.use_stop_names(result_text) 
        response = trimmed.replace("'''", "```")

        # add the AI's response to the memory
        memory.save_context({"input": f"{formatted_message}{self.stop_token}"}, {"output": f"{self.char_name}: {response}{self.stop_token}"})
        # memory.save_context({"input": f"{formatted_message}"}, {"output": f"{self.char_name}: {response}"})
        # dicts = messages_to_dict(self.memory.messages)
        # self.history = '\n'.join(message['data']['content'] for message in dicts)

        return response

    async def add_history(self, message, message_content) -> None:
        channel_id = str(message.channel.id)

        memory = await self.get_memory_for_channel(channel_id)
        
        name = await self.check_stop_names(message.author.display_name)
        # memory.add_input_only(f"{name}: {message_content}")
        memory.add_input_only(f"{name}: {message_content}{self.stop_token}")
        # dicts = messages_to_dict(self.memory.messages)
        # self.history = '\n'.join(message['data']['content'] for message in dicts)
        print(f"added to history: {name}: {message_content}")

    async def add_input_output(self, interaction, message_content, response) -> None:
        channel_id = str(interaction.channel.id)

        memory = await self.get_memory_for_channel(channel_id)

        name = await self.check_stop_names(interaction.user.display_name)
        formatted_message = f"{name}: {message_content}"
        memory.save_context({"input": f"{formatted_message}{self.stop_token}"}, {"output": f"{self.char_name}: {response}{self.stop_token}"})
        # memory.save_context({"input": f"{formatted_message}"}, {"output": f"{self.char_name}: {response}"})
        print("interaction added to history")





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
        response = await self.chatbot.generate_response(message, message_content)
        return response

    # No Response Handler
    @commands.command(name="chatnr")
    async def chat_command_nr(self, message, message_content) -> None:
        response = await self.chatbot.add_history(message, message_content)
        return None

    # Normal Chat handler
    @commands.command(name="agent")
    async def agent_command(self, interaction, prompt, response) -> None:
        response = await self.chatbot.add_input_output(interaction, prompt, response)
        return response

    @app_commands.command(name="instruct", description="Instruct the bot to say something")
    async def instruct(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.send_message(embed=discord.Embed(
                title=f"{interaction.user.display_name} used Instruct 👨‍🏫",
                description=f"Instructions: {prompt}",
                color=0x9C84EF
            ))
        
        # if user
        user_message = prompt
        self.prompt = {"prompt": f"""
Below is an instruction that describes a task. Write a response that appropriately completes the request.
### Instruction:\{prompt}\n

### Response:
"""
        }
        # send a post request to the API endpoint
        response = requests.post(f"{self.bot.endpoint}/api/v1/generate", json=self.prompt)
        # check if the request was successful
        if response.status_code == 200:
            # Get the results from the response
            results = response.json()['results']
            response = results[0]['text']
            print(response)
            # await interaction.channel.send(response)
            await self.agent_command(interaction, prompt, response)
            await interaction.channel.send(response)
    


async def setup(bot):
    # add chatbot cog to bot
    await bot.add_cog(ChatbotCog(bot))
