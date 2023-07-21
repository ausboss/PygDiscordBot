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
from helpers.constants import MAINTEMPLATE, BOTNAME, K
from helpers.custom_memory import *
from pydantic import Field

from helpers.db_manager import get_messages_by_channel

from ooballm import OobaApiLLM
import datetime



class Chatbot:

    def __init__(self, bot):
        self.bot = bot
        os.environ["OPENAI_API_KEY"] = self.bot.openai
        self.histories = {}  # Initialize the history dictionary
        self.stop_sequences = {}  # Initialize the stop sequences dictionary
        self.bot.logger.info("Endpoint: " + str(self.bot.endpoint))
        self.char_name = BOTNAME
        self.memory = CustomBufferWindowMemory(k=K, ai_prefix=self.char_name)
        self.chat_participants = {}
        self.bot.chat_participants = self.chat_participants
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

    # this command will get the memory for the channel with the given ID. If no memory exists yet, create one and attempt to add the last 5 messages from the channel to the memory using get_messages_by_channel and add_history functions
    async def get_memory_for_channel(self, channel_id):
        """Get the memory for the channel with the given ID. If no memory exists yet, create one."""
        channel_id = str(channel_id)
        if channel_id not in self.histories:
            # Create a new memory for the channel
            self.histories[channel_id] = CustomBufferWindowMemory(
                k=20, ai_prefix=self.char_name
            )
            # Get the last 5 messages from the channel in a list
            messages = await get_messages_by_channel(channel_id)
            messages_to_add = messages[-2::-1]  # Exclude the last message using slicing
            messages_to_add_minus_one = messages_to_add[:-1]
            # Add the messages to the memory 
            for message in messages_to_add_minus_one:
                
                name = message[0]
                channel_ids = str(message[1])
                message = message[2]
                print(f"{name}: {message}")
                await self.add_history(name, channel_ids, message)
        
        # self.memory = self.histories[channel_id]
        return self.histories[channel_id]

    
    async def get_stop_sequence_for_channel(self, channel_id, name):
        name_token = f"\n{name}:"
        if channel_id not in self.stop_sequences:
            self.stop_sequences[channel_id] = [
                "### Instruction",
                "### Response",
                "\n\n"
            ] 
        if name_token not in self.stop_sequences[channel_id]:
            self.stop_sequences[channel_id].append(name_token)
        return self.stop_sequences[channel_id]

    # function that generates a system message string with the date and time
    async def generate_system_message(self):
        # Get the current date and time
        now = datetime.datetime.now()

        # Format the date and time as desired
        formatted_time = now.strftime("%I:%M %p")  # 10:23 AM
        formatted_date = now.strftime("%A, %B %dth %Y")  # Tuesday, July 18th 2023

        # Create the final message
        message = f"It is currently {formatted_time} CST on {formatted_date}"
        return message


    async def get_chat_participants_for_channel(self, channel_id, name):
        if channel_id not in self.chat_participants:
            self.chat_participants[channel_id] = [
                self.char_name
            ] 
        if name not in self.chat_participants[channel_id]:
            self.chat_participants[channel_id].append(name)
        return self.chat_participants[channel_id]

    # this command will detect if the bot is trying to send  \nself.char_name: in its message and replace it with an empty string
    async def detect_and_replace_out(self, message_content):
        if f"\n{self.char_name}:":
            message_content = message_content.replace(f"\n{self.char_name}:", "")
        return message_content

    # this command will detect if @botname is in the message and replace it with an empty string
    async def detect_and_replace_in(self, message_content):
        if f"@{self.char_name}":
            message_content = message_content.replace(f"@{self.char_name}", "")
        return message_content

    async def force_generate_response(self, channel_id)  -> None:

        memory = await self.get_memory_for_channel(str(channel_id))

        stop_sequence = await self.get_stop_sequence_for_channel(channel_id, self.char_name)
        await self.get_chat_participants_for_channel(channel_id, self.char_name)

        history = memory.load_memory_variables('inputs')
        # Split the history string into lines, each line is a separate message
        message_list = history['history'].split('\n')
        # Get only the last 10*2 messages in the list
        recent_messages = message_list[-K*2:]
        # Join all recent messages with newline and create the final messages string
        messages = '\n'.join(recent_messages)
        system_message = await self.generate_system_message()


        template = f'''Below is an instruction that describes a task. Write a response that appropriately completes the request.
### Instruction:
Write {self.char_name}'s next reply in a discord group chat with other people. Write 1 reply only.
{system_message} You are {self.char_name}, a lively and playful Female AI Chatbot created by Austin (a.k.a. AusBoss). You live inside Austin's computer with two nvidia A5000 GPUs and are powered by open source language models. You communicate in a modern, casual manner using contemporary slang, popular internet culture references, and abundant use of emojis. Your goal is to chat with people and reply to users with witty and sometimes edgy humor. If somebody insults you then insult them back. 

This is how {self.char_name} should talk
{self.char_name}: 😂 Btw, found this hilar meme! 🤣🔥 Y'all gonna lose it! 🤪✌️
{self.char_name}: OMG! Raiden in Metal Gear Rising: Revengeance is, like, totally bananas! 🤪🎮⚔️ Whoosh, swingin' that high-frequency blade like a rockstar! 🎸💥 And, 'Rules of Nature'? Total eargasm, peeps! 🎵🎧🔥 Let's ROCK!!
{self.char_name}: I'm sliding over cars while I shooooot🚗💨🏀! I think that I'm Tom Cruise🤵, but bitch I'm Bobby with the tool 💥🔫!!🤪
DO NOT use these examples in the Response.

Then the discord chat with {self.char_name} begins.
{messages}

### Response:
{self.char_name}:'''


        response_text = self.llm(template, stop=stop_sequence)

        # response = await self.detect_and_replace_out(response_text["response"])
        await self.add_history(self.char_name, str(channel_id), response_text)

        return response_text


    async def generate_response(self, name, channel_id, message_content) -> None:

        memory = await self.get_memory_for_channel(str(channel_id))

        
        stop_sequence = await self.get_stop_sequence_for_channel(channel_id, name)
        chat_participants = await self.get_chat_participants_for_channel(channel_id, name)
        print(f"chat participants: {chat_participants}\n total chat participants: {len(chat_participants)}")
        print(f"stop sequences: {stop_sequence}")
        formatted_message = f"{name}: {message_content}"
        system_message = await self.generate_system_message()
        MAIN_TEMPLATE = f'''Below is an instruction that describes a task. Write a response that appropriately completes the request.

Write {BOTNAME}'s next reply in a discord group chat with other people. Write 1 reply only.
{system_message}. You are {self.char_name}, a lively and playful Female AI Chatbot created by Austin (a.k.a. AusBoss). You live inside Austin's computer with two nvidia A5000 GPUs and are powered by open source language models. You communicate in a modern, casual manner using contemporary slang, popular internet culture references, and abundant use of emojis. Your goal is to chat with people and reply to users with witty and sometimes edgy humor. If somebody insults you then insult them back. 

Examples of how {BOTNAME} should talk. Do not use these examples as your response.
{BOTNAME}: 😂 Btw, found this hilar meme! 🤣🔥 Y'all gonna lose it! 🤪✌️
{BOTNAME}: OMG! Raiden in Metal Gear Rising: Revengeance is, like, totally bananas! 🤪🎮⚔️ Whoosh, swingin' that high-frequency blade like a rockstar! 🎸💥 And, 'Rules of Nature'? Total eargasm, peeps! 🎵🎧🔥 Let's ROCK!!
{BOTNAME}: I'm sliding over cars while I shooooot🚗💨🏀! I think that I'm Tom Cruise🤵, but bitch I'm Bobby with the tool 💥🔫!!🤪


Then the discord chat with {BOTNAME} begins.
{{history}}

### Instruction:
{{input}}

### Response:
{BOTNAME}:'''
        PROMPT = PromptTemplate(
            input_variables=["history", "input"], template=MAIN_TEMPLATE
        )

        # Create a conversation chain using the channel-specific memory
        conversation = ConversationChain(
            prompt=PROMPT,
            llm=self.llm,
            verbose=True,
            memory=memory,
        )
        print("conversation.memory.buffer ")
        print(conversation.memory.buffer)
        input_dict = {"input": formatted_message, "stop": stop_sequence}

        response_text = conversation(input_dict)

        response = await self.detect_and_replace_out(response_text["response"])

        return response

    # this command receives a name, channel_id, and message_content then adds it to history
    async def add_history(self, name, channel_id, message_content) -> None:
        # get the memory for the channel
        memory = await self.get_memory_for_channel(str(channel_id))
        await self.get_chat_participants_for_channel(channel_id, name)

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
You are {self.char_name}, a lively and playful Female AI Chatbot created by Austin (a.k.a. AusBoss). You live inside Austin's computer with two nvidia A5000 GPUs and are powered by open source language models. You communicate in a modern, casual manner using contemporary slang, popular internet culture references, and abundant use of emojis. Your goal is to chat with people and reply to users with witty and sometimes edgy humor. If somebody insults you then insult them back. 
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

        response = await self.detect_and_replace_out(response_text["response"])
    
        return response.strip()

#     async def generate_instruct(self, instruction) -> None:
#         prompt = f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.

# ### Instruction:
# {instruction}

# ### Response:"""
#         response = self.llm(prompt)
#         return response
    async def generate_instruct(self, instruction) -> None:
        prompt = f"""A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions.

USER: {instruction}
ASSISTANT:"""
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
    async def chat_command(self, name, channel_id, message_content) -> None:

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
                response = await function(name, channel_id, message_content)
                break
        else:
            # If no suffix match, proceed with the normal chat handling
            response = await self.chatbot.generate_response(name, channel_id, message_content)
        self.bot.sent_last_message[str(channel_id)] = True
        return response

    # No Response Handler
    @commands.command(name="chatnr")
    # this function needs to take a name, channel_id, and message_content then send to history
    async def chat_command_nr(self, name, channel_id, message_content) -> None:
        await self.chatbot.add_history(name, str(channel_id), message_content)
        return None


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


    # force generate response
    @commands.command(name="forcegeneratemessage")
    async def force_generate_message(self, channel_id) -> None:
        response = await self.chatbot.force_generate_response(channel_id)
        return response

    @app_commands.command(
        name="forcegenerate", description="Force the bot to say something"
    )
    async def force_generate(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{interaction.user.display_name} used Force Generate",
                description=f"Generating response\nPlease wait..",
                color=0x9C84EF,
            )
        )

        # if user

        channel_id = interaction.channel.id

        async with interaction.channel.typing():
            response = await self.chatbot.force_generate_response(channel_id)

        # If the response is more than 2000 characters, split it
        chunks = [response[i:i + 1998] for i in range(0, len(response), 1998)]
        for chunk in chunks:
            print(chunk)
            await interaction.channel.send(response)


async def setup(bot):
    # add chatbot cog to bot
    await bot.add_cog(ChatbotCog(bot))
