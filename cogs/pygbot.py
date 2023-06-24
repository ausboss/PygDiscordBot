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
        # Prepare the JSON data
        data = {
            "prompt": prompt,
            "use_story": False,
            "use_authors_note": False,
            "use_world_info": False,
            "use_memory": False,
            "max_context_length": 1800,
            "max_length": 512,
            "rep_pen": 1.12,
            "rep_pen_range": 1024,
            "rep_pen_slope": 0.9,
            "temperature": 0.6,
            "tfs": 0.9,
            "top_p": 0.95,
            "top_k": 0.6,
            "typical": 1,
            "frmttriminc": True
        }

        # Add the stop sequences to the data if they are provided
        if stop is not None:
            data["stop_sequence"] = stop

        # Send a POST request to the Kobold API with the data
        response = requests.post(f"{Kobold_api_url}/api/v1/generate", json=data)

        # Raise an exception if the request failed
        response.raise_for_status()

        # Check for the expected keys in the response JSON
        json_response = response.json()
        if "results" in json_response and len(json_response["results"]) > 0 and "text" in json_response["results"][0]:
            # Return the generated text
            text = json_response["results"][0]["text"].strip().replace("'''", "```")

            # Remove the stop sequence from the end of the text, if it's there
            for sequence in stop:
                if text.endswith(sequence):
                    text = text[: -len(sequence)].rstrip()

            print(text)
            return text
        else:
            raise ValueError("Unexpected response format from Kobold API")


    
    def __call__(self, prompt: str, stop: Optional[List[str]]=None) -> str:
        return self._call(prompt, stop)

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {}


    
class Chatbot:
    def __init__(self, char_filename, bot):
        self.stop_token = "</s>"
        self.bot = bot
        self.histories = {}  # Initialize the history dictionary
        self.stop_sequences = {} # Initialize the stop sequences dictionary
        

        # read character data from JSON file
        with open(char_filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.char_name = data["char_name"]
            self.char_persona = data["char_persona"]
            self.char_greeting = data["char_greeting"]
            self.world_scenario = data["world_scenario"]
            self.example_dialogue = data["example_dialogue"]
        self.memory = CustomBufferWindowMemory(k=10, ai_prefix=self.char_name)
        self.history = "[Beginning of Conversation]"
        self.llm = KoboldApiLLM()
        self.template = f"""The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it does not know.
        
Current conversation:
{{history}}
{{input}}
{self.char_name}:"""
        self.PROMPT = PromptTemplate(input_variables=["history", "input"], template=self.template)
        self.conversation = ConversationChain(
            prompt=self.PROMPT,
            llm=self.llm,
            verbose=True,
            memory=self.memory,
        )




    async def get_memory_for_channel(self, channel_id):
        """Get the memory for the channel with the given ID. If no memory exists yet, create one."""
        if channel_id not in self.histories:
            self.histories[channel_id] = CustomBufferWindowMemory(k=10, ai_prefix=self.char_name)
            self.memory = self.histories[channel_id]
        return self.histories[channel_id]

    async def get_stop_sequence_for_channel(self, channel_id, name):
        name_token = f"{name}:"
        if channel_id not in self.stop_sequences:
            self.stop_sequences[channel_id] = []
        if name_token not in self.stop_sequences[channel_id]:
            self.stop_sequences[channel_id].append(name_token)
        return self.stop_sequences[channel_id]





        





    async def generate_response(self, message, message_content) -> None:
        channel_id = str(message.channel.id)
        name = message.author.display_name
        memory = await self.get_memory_for_channel(channel_id)
        stop_sequence = await self.get_stop_sequence_for_channel(channel_id, name)
        formatted_message = f"{name}: {message_content}"

        # Create a conversation chain using the channel-specific memory
        conversation = ConversationChain(
            prompt=self.PROMPT,
            llm=self.llm,
            verbose=True,
            memory=memory,
        )

        input_dict = {
            "input": formatted_message, 
            "stop": stop_sequence
        }
        response = conversation(input_dict)

        return response["response"]


    async def add_history(self, message, message_content) -> None:
        channel_id = str(message.channel.id)
        name = message.author.display_name
        memory = await self.get_memory_for_channel(channel_id)
        stop_sequence = await self.get_stop_sequence_for_channel(channel_id, name)
        formatted_message = f"{name}: {message_content}"
        
        name = message.author.display_name
        memory.add_input_only(f"{name}: {message_content}")
        # dicts = messages_to_dict(self.memory.messages)
        # self.history = '\n'.join(message['data']['content'] for message in dicts)
        print(f"added to history: {name}: {message_content}")


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

    @app_commands.command(name="instruct", description="Instruct the bot to say something")
    async def instruct(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.send_message(embed=discord.Embed(
                title=f"{interaction.user.display_name} used Instruct 👨‍🏫",
                description=f"Instructions: {prompt}\nGenerating response\nPlease wait..",
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
            await interaction.channel.send(response)
    


async def setup(bot):
    # add chatbot cog to bot
    await bot.add_cog(ChatbotCog(bot))
