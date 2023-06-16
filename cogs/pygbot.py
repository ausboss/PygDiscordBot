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
        )
        response.raise_for_status()

        return response.json()["results"][0]["text"].strip().replace("```", " ")

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {

        }



class Chatbot:
    def __init__(self, char_filename, bot):
        self.stop_token = "</s>"

        # read character data from JSON file
        with open(char_filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.char_name = data["char_name"]
            self.char_persona = data["char_persona"]
            self.char_greeting = data["char_greeting"]
            self.world_scenario = data["world_scenario"]
            self.example_dialogue = data["example_dialogue"]
        self.history = "[Beginning of Conversation]"
        self.llm = KoboldApiLLM()
        self.memory = CustomBufferWindowMemory(k=8, memory_key="chat_history")

        # self.memory = ConversationBufferMemory(memory_key="chat_history", ai_prefix=self.char_name)
    async def remove_char_name_from_string(self, string):
        prefix_to_remove = self.char_name + "@"

        if string.startswith(prefix_to_remove):
            return string[len(prefix_to_remove):].lstrip()  # lstrip() is used to remove any leading whitespace
        else:
            return string



    async def generate_response(self, message, message_content) -> None:

        
        name = message.author.display_name
        # save the conversation to the chatlog 
        self.template = f"""
### Instructions:
The following is group chat. Use the provided input for context. Reply as {self.char_name}.

### Input:
{self.char_persona}
Current conversation:
{self.char_greeting}
{self.memory.load_memory_variables('chat_history')['chat_history']}
{{input}}

### Response:
Tensor:"""
        self.PROMPT = PromptTemplate(input_variables=["input"], template=self.template)
        self.conversation = LLMChain(
            prompt=self.PROMPT,
            llm=self.llm,
            verbose=True
        )
        final_message = remove_char_name_from_string(message_content)
        formatted_message = f"{name}: {final_message}"

        # first, add the user's message to the memory
        # self.memory.add_user_message(formatted_message)

        # then, generate the AI's response
        result = self.conversation(formatted_message)
        response = result["text"].split("\n\n")[0]

        # add the AI's response to the memory
        # self.memory.add_ai_message(f"{self.char_name}: {response}")
        self.memory.save_context({"input": f"{formatted_message}{self.stop_token}"}, {"output": f"{self.char_name}: {response}{self.stop_token}"})
        # dicts = messages_to_dict(self.memory.messages)
        # self.history = '\n'.join(message['data']['content'] for message in dicts)

        return response

    async def add_history(self, message, message_content) -> None:
        
        name = message.author.display_name
        self.memory.add_input_only(f"{name}: {message_content}{self.stop_token}")
        # dicts = messages_to_dict(self.memory.messages)
        # self.history = '\n'.join(message['data']['content'] for message in dicts)
        print(f"added to history: {name}: {message_content}{self.stop_token}")




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


    # Embedders
    
    async def instruct_embedder(self, interaction, prompt, message):
        embed = discord.Embed(
                title="Instruct 👨‍🏫:",
                description=f"Author: {interaction.user.name}\nPrompt: {prompt}\nResponse:\n{message}",
                color=0x9C84EF
            )
        return embed

    async def wait_embedder(self, name):
        embedder = discord.Embed(
                title="Instruct 👨‍🏫:",
                description=f"Generating response for \n{name}\n\nPlease wait..",
                color=0x9C84EF
            )
        return embedder

    


    # create a slash command that will do a regular instruct api call with a specific prompt. This will not get added to history.
    @app_commands.command(name="instruct", description="Instruct the bot to say something")
    async def instruct(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.send_message(embed=await self.wait_embedder(interaction.user.name))
        
        # await interaction.response.send_message("", delete_after=0.1)
        # await interaction.delete_original_response()
        user_message = prompt
        self.prompt = {"prompt": f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.
        ### Instruction:\{prompt}\n
    
        ### Response:
        """
        }
        # send a post request to the API endpoint
        response = requests.post(f"{self.endpoint}/api/v1/generate", json=self.prompt)
        # check if the request was successful
        if response.status_code == 200:
            # Get the results from the response
            results = response.json()['results']
            response = results[0]['text']
            print(response)
            # await interaction.channel.send(response)
            await interaction.channel.send(embed=await self.instruct_embedder(interaction, user_message, response))


async def setup(bot):
    # add chatbot cog to bot
    await bot.add_cog(ChatbotCog(bot))
