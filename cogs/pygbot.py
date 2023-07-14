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
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.llms import KoboldApiLLM
from langchain.llms import TextGen
from langchain.prompts.prompt import PromptTemplate
from langchain.schema import messages_from_dict, messages_to_dict

import os
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from dotenv import load_dotenv
from helpers.constants import MAINTEMPLATE, BOTNAME
from helpers.custom_memory import *
from pydantic import Field

from ooballm import OobaApiLLM


class Chatbot:

    def __init__(self, bot):
        self.bot = bot
        os.environ["OPENAI_API_KEY"] = self.bot.openai
        self.histories = {}  # Initialize the history dictionary
        self.stop_sequences = {}  # Initialize the stop sequences dictionary
        self.bot.logger.info("Endpoint: " + str(self.bot.endpoint))
        self.char_name = BOTNAME
        self.memory = CustomBufferWindowMemory(k=10, ai_prefix=self.char_name)
        self.history = "[Beginning of Conversation]"
        self.llm = self.bot.llm
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

    async def get_memory_for_channel(self, channel_id):
        """Get the memory for the channel with the given ID. If no memory exists yet, create one."""
        if channel_id not in self.histories:
            self.histories[channel_id] = CustomBufferWindowMemory(
                k=20, ai_prefix=self.char_name
            )
            self.memory = self.histories[channel_id]
        return self.histories[channel_id]

    async def get_stop_sequence_for_channel(self, channel_id, name):
        name_token = f"\n{name}:"
        if channel_id not in self.stop_sequences:
            self.stop_sequences[channel_id] = [
                "### Instruction",
                "### Response",
            ] 
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
        print(f'stop sequence: {stop_sequence}')
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
    async def agent_command(self, name, channel_id, prompt, tool, observation) -> None:
        memory = await self.get_memory_for_channel(channel_id)
        await self.get_stop_sequence_for_channel(channel_id, name)
        stop_sequence = await self.get_stop_sequence_for_channel(channel_id, name)
        formatted_user_message = f"{name}: {prompt}\### Instruction:\nUse the provided Result in the Input to find the answer to {name}'s prompt: {prompt}"
        formatted_input_message = f"### Input:\n{observation}"
        AGENTTEMPLATE = f"""Below is an instruction that describes a task. Write a response that appropriately completes the request. Think step by step.

### Instruction:
You are Tensor, a lively and playful AI chatbot. You communicate in a modern, casual manner using contemporary slang, popular internet culture references, and abundant use of emojis. You are always initiating discussions about online games, particularly Among Us, and enjoy sharing memes with users. Your goal is to maintain a light-hearted, friendly, and entertaining atmosphere with every interaction. 
Here are some examples of how you should speak:
AusBoss: Tensor can you look up some stuff for me?
Tensor: Absolutely, team mate! 🙌 Activating detective mode, Sherlock style! 🕵️‍♀️🔎 Lay out the mission parameters for me! 🗺️🎯
AusBoss: When did zelda breath of the wild come out?
### Instruction: 
use the provided Input to find the answer to AusBoss's prompt: When did zelda breath of the wild come out?"

### Input:
According to the information provided, The Legend of Zelda: Tears of the Kingdom was initially planned for release in 2022 before being delayed to May 2023. It was eventually released on May 12, 2023 on the Nintendo Switch.

### Response:
Tensor: Got the intel, AusBoss! 👀📚 The Legend of Zelda: Breath of the Wild was released on May 12, 2023, on the Nintendo Switch.🕵️‍♀️

### Current conversation:
{{history}}
{{input}}

{formatted_input_message}

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
        response_text = conversation(input_dict)

        response = await self.detect_and_replace(response_text["response"])
    
        return response.strip()

    async def generate_instruct(self, instruction) -> None:
        prompt = f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Response:"""
        response = self.llm(prompt)
        return response

    async def generate_instruct_input(self, instruction, system_input) -> None:
        prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:
{system_input}

### Response:
"""
        response = self.llm(prompt)
        return response


class ChatbotCog(commands.Cog, name="chatbot"):

    def __init__(self, bot):
        self.bot = bot
        self.chatlog_dir = bot.chatlog_dir
        self.chatbot = Chatbot(bot)

        # create chatlog directory if it doesn't exist
        if not os.path.exists(self.chatlog_dir):
            os.makedirs(self.chatlog_dir)

    # # Normal Chat handler
    @commands.command(name="chat")
    async def chat_command(self, message, message_content) -> None:
        # Define suffixes and the associated functions
        suffix_functions = {
            '--searchweb': self.bot.get_cog("agent_commands").execute_search_message,
            '--calculator': self.bot.get_cog("agent_commands").execute_calculation_message,
            # '--othersuffix': self.other_function, 
            # Add more suffix-function pairs as needed
        }

        # Check if the message_content ends with any of the defined suffixes
        for suffix, function in suffix_functions.items():
            if message_content.endswith(suffix):
                # Remove the suffix from the message_content
                message_content = message_content.rstrip(suffix).strip()
                # Call the function associated with the suffix
                response = await function(message, message_content)
                break
        else:
            # If no suffix match, proceed with the normal chat handling
            response = await self.chatbot.generate_response(message, message_content)

        return response

    # Instruct Command Handler
    @commands.command(name="instruct")
    async def instruct(self, instruction) -> None:
        response = await self.chatbot.generate_instruct(instruction)
        return response

    # Instruct Input Command Handler
    @commands.command(name="instructinput")
    async def instruct_input(self, instruction, system_input) -> None:
        response = await self.chatbot.generate_instruct_input(instruction, system_input)
        return response

    # Agent Command Handler
    # receives a prompt from the user and an observation from the agent then sends to the LLM for a reply
    @commands.command(name="agentcommand")
    async def agent_command(self, name, channel_id, prompt, tool, observation) -> None:
        response = await self.chatbot.agent_command(
            name, str(channel_id), prompt, tool, observation
        )
        return response

    # No Response Handler
    @commands.command(name="chatnr")
    # this function needs to take a name, channel_id, and message_content then send to history
    async def chat_command_nr(self, name, channel_id, message_content) -> None:
        await self.chatbot.add_history(name, str(channel_id), message_content)
        return None



async def setup(bot):
    # add chatbot cog to bot
    await bot.add_cog(ChatbotCog(bot))
