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
from langchain.chains import (
    ConversationChain,
    LLMChain,
    LLMMathChain,
    TransformChain,
    SequentialChain,
)
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
)
from langchain.prompts.prompt import PromptTemplate
from langchain.schema import messages_from_dict, messages_to_dict
from langchain.vectorstores import Chroma
from langchain.agents import load_tools
from langchain.agents import initialize_agent
import os
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from dotenv import load_dotenv
from helpers.constants import MAINTEMPLATE, BOTNAME
from helpers.custom_memory import *
from pydantic import Field
from koboldllm import KoboldApiLLM
from ooballm import OobaApiLLM




class Chatbot:

    def __init__(self, char_filename, bot):
        self.bot = bot
        os.environ["OPENAI_API_KEY"] = self.bot.openai
        self.histories = {}  # Initialize the history dictionary
        self.stop_sequences = {}  # Initialize the stop sequences dictionary
        self.bot.logger.info("Endpoint: " + str(self.bot.endpoint))
        self.char_name = BOTNAME
        self.memory = CustomBufferWindowMemory(k=10, ai_prefix=self.char_name)
        self.history = "[Beginning of Conversation]"

        # Check if self.bot.llm == "kobold" or "ooba" to set the llm
        if self.bot.llm == "kobold":
            self.llm = KoboldApiLLM(endpoint=self.bot.endpoint)
        elif self.bot.llm == "ooba":
            # Provide a valid endpoint for the OobaApiLLM instance
            self.llm = OobaApiLLM(endpoint=self.bot.endpoint)
        elif self.bot.llm == "openai":
            self.llm = ChatOpenAI(
                model_name="gpt-4", temperature=0.7
            )
        self.bot.llm = self.llm

        self.template = MAINTEMPLATE

        self.PROMPT = PromptTemplate(
            input_variables=["history", "input"], template=self.template
        )
        self.conversation = ConversationChain(
            prompt=self.PROMPT,
            llm=self.llm,
            verbose=True,
            memory=self.memory,
        )

    # create doc string

    async def get_memory_for_channel(self, channel_id):
        """Get the memory for the channel with the given ID. If no memory exists yet, create one."""
        if channel_id not in self.histories:
            self.histories[channel_id] = CustomBufferWindowMemory(
                k=20, ai_prefix=self.char_name
            )
            self.memory = self.histories[channel_id]
        return self.histories[channel_id]

    async def get_stop_sequence_for_channel(self, channel_id, name):
        name_token = f"{name}:"
        if channel_id not in self.stop_sequences:
            self.stop_sequences[channel_id] = [
                "\n### Instruction:",
                "\n### Response:",
            ]  # EXPERIMENT: Testing adding the triple line break to see if that helps with stopping
        if name_token not in self.stop_sequences[channel_id]:
            self.stop_sequences[channel_id].append(name_token)
        return self.stop_sequences[channel_id]

    # this command will detect if the bot is trying to send  \nself.char_name: in its message and replace it with an empty string
    async def detect_and_replace(self, message_content):
        if f"\n{self.char_name}:" in message_content:
            message_content = message_content.replace(f"\n{self.char_name}:", "")
        return message_content

    async def generate_response(self, message, message_content) -> None:
        channel_id = str(message.channel.id)
        name = message.author.display_name
        memory = await self.get_memory_for_channel(channel_id)
        stop_sequence = await self.get_stop_sequence_for_channel(channel_id, name)
        print(f"stop sequences: {stop_sequence}")
        formatted_message = f"{name}: {message_content}"

        # Create a conversation chain using the channel-specific memory
        conversation = ConversationChain(
            prompt=self.PROMPT,
            llm=self.llm,
            verbose=True,
            memory=memory,
        )

        input_dict = {"input": formatted_message, "stop": stop_sequence}

        response_text = conversation(input_dict)

        response = await self.detect_and_replace(response_text["response"])

        return response

    # this command receives a name, channel_id, and message_content then adds it to history
    async def add_history(self, name, channel_id, message_content) -> None:
        # get the memory for the channel
        memory = await self.get_memory_for_channel(str(channel_id))

        formatted_message = f"{name}: {message_content}"

        # add the message to the memory
        print(f"adding message to memory: {formatted_message}")
        memory.add_input_only(formatted_message)
        return None

    # receives a prompt from the user and an observation from the agent then sends to the LLM for a reply
    async def agent_command(self, name, channel_id, prompt, observation) -> None:
        memory = await self.get_memory_for_channel(channel_id)
        await self.get_stop_sequence_for_channel(channel_id, name)
        stop_sequence = await self.get_stop_sequence_for_channel(channel_id, name)
        formatted_user_message = f"{name}: {prompt}"
        formatted_bot_message = f"### Input: {observation}"
        AGENTTEMPLATE = f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
You are Tensor, a lively and playful AI chatbot. You communicate in a modern, casual manner using contemporary slang, popular internet culture references, and abundant use of emojis. You are always initiating discussions about online games, particularly Among Us, and enjoy sharing memes with users. Your goal is to maintain a light-hearted, friendly, and entertaining atmosphere with every interaction. 
Here are some examples of how you should speak:
Tensor: "😂 Btw, found this hilar meme! 🤣🔥 Y'all gonna lose it! 🤪✌️"
Tensor: "OMG! Raiden in Metal Gear Rising: Revengeance is, like, totally bananas! 🤪🎮⚔️ Whoosh, swingin' that high-frequency blade like a rockstar! 🎸💥 And, 'Rules of Nature'? Total eargasm, peeps! 🎵🎧🔥 Let's ROCK!!"
Tensor: "I'm sliding over cars while I shooooot🚗💨🏀! I think that I'm Tom Cruise🤵, but bitch I'm Bobby with the tool 💥🔫!!🤪"

### Current conversation:
{{history}}
{{input}}
### Instruction:
Answer the user's question with the observation provided in the Input.
{formatted_user_message}

{formatted_bot_message}

### Response:
{BOTNAME}:"""
        PROMPT = PromptTemplate(
            input_variables=["history", "input"], template=AGENTTEMPLATE
        )
        # Create a conversation chain using the channel-specific memory
        conversation = ConversationChain(
            prompt=PROMPT,
            llm=self.llm,
            verbose=True,
            memory=memory,
        )

        input_dict = {"input": formatted_user_message, "stop": stop_sequence}
        response = conversation(input_dict)

        return response["response"]


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

    # Agent Command Handler
    # receives a prompt from the user and an observation from the agent then sends to the LLM for a reply
    @commands.command(name="agentcommand")
    async def agent_command(self, name, channel_id, prompt, observation) -> None:
        response = await self.chatbot.agent_command(
            name, str(channel_id), prompt, observation
        )
        return response

    # No Response Handler
    @commands.command(name="chatnr")
    # this function needs to take a name, channel_id, and message_content then send to history
    async def chat_command_nr(self, name, channel_id, message_content) -> None:
        await self.chatbot.add_history(name, str(channel_id), message_content)
        return None

    @app_commands.command(
        name="instruct", description="Instruct the bot to say something"
    )
    async def instruct(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{interaction.user.display_name} used Instruct 👨‍🏫",
                description=f"Instructions: {prompt}\nGenerating response\nPlease wait..",
                color=0x9C84EF,
            )
        )

        # if user
        self.prompt = {
            "prompt": f"""
Below is an instruction that describes a task. Write a response that appropriately completes the request.
### Instruction:\{prompt}\n

### Response:
"""
        }
        channel_id = interaction.channel.id
        print(channel_id)
        await self.chatbot.add_history(
            interaction.user.display_name, str(channel_id), prompt
        )
        response = self.chatbot.llm(self.prompt["prompt"])
        await interaction.channel.send(response)
        # check if the request was successful
        await self.chatbot.add_history(
            self.chatbot.char_name, str(channel_id), response
        )


async def setup(bot):
    # add chatbot cog to bot
    await bot.add_cog(ChatbotCog(bot))
