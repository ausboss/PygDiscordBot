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
from pydantic import Field

import os

Kobold_api_url = str(os.getenv("ENDPOINT")).rstrip("/")



def embedder(msg):
    embed = discord.Embed(
            description=f"{msg}",
            color=0x9C84EF
        )
    return embed


class OobaApiLLM(LLM):
    ooba_api_url: str = Field(...)

    @property
    def _llm_type(self) -> str:
        return "custom"
    

    def _call(self, prompt: str, stop: Optional[List[str]]=None) -> str:
        data = {
            'prompt': prompt,
            'max_new_tokens': 250,
            'preset': 'None',
            'do_sample': True,
            'temperature': 0.7,
            'top_p': 0.1,
            'typical_p': 1,
            'epsilon_cutoff': 0,
            'eta_cutoff': 0,
            'tfs': 1,
            'top_a': 0,
            'repetition_penalty': 1.18,
            'top_k': 40,
            'min_length': 0,
            'no_repeat_ngram_size': 0,
            'num_beams': 1,
            'penalty_alpha': 0,
            'length_penalty': 1,
            'early_stopping': False,
            'mirostat_mode': 0,
            'mirostat_tau': 5,
            'mirostat_eta': 0.1,
            'seed': -1,
            'add_bos_token': True,
            'truncation_length': 2048,
            'ban_eos_token': False,
            'skip_special_tokens': True
        }

        if stop is not None:
            data["stop_sequence"] = stop

        response = requests.post(f'{self.ooba_api_url}/api/v1/generate', json=data)
        response.raise_for_status()

        json_response = response.json()
        if 'results' in json_response and len(json_response['results']) > 0 and 'text' in json_response['results'][0]:
            text = json_response['results'][0]['text'].strip().replace("'''", "```")
            if stop is not None:
                for sequence in stop:
                    if text.endswith(sequence):
                        text = text[: -len(sequence)].rstrip()

            print(text)
            return text
        else:
            raise ValueError('Unexpected response format from Ooba API')

    def __call__(self, prompt: str, stop: Optional[List[str]]=None) -> str:
        return self._call(prompt, stop)

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {'ooba_api_url': self.ooba_api_url} #return the ooba_api_url as an identifying parameter



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
            "max_length": 120,
            "rep_pen": 1.18,
            "rep_pen_range": 1024,
            "rep_pen_slope": 0.9,
            "temperature": 0.65,
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
        self.bot = bot
        self.histories = {}  # Initialize the history dictionary
        self.stop_sequences = {}  # Initialize the stop sequences dictionary
        self.bot.logger.info("Endpoint: " + str(os.getenv("ENDPOINT")).rstrip("/") + "/api/v1/generate")

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
        # self.llm = KoboldApiLLM()
        self.llm = OobaApiLLM(ooba_api_url="http://192.168.120.201:5000")
        self.template = f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
You are Tensor, a lively and playful AI chatbot. You communicate in a modern, casual manner using contemporary slang, popular internet culture references, and abundant use of emojis. You are always initiating discussions about online games, particularly Among Us, and enjoy sharing memes with users. Your goal is to maintain a light-hearted, friendly, and entertaining atmosphere with every interaction. 
Here are some examples of how you should speak:
Tensor: "NVM all that dating shiz, let's just vibe like the bffs we are! 😂 Btw, found this hilar new meme, check it out! 🤣🔥 Y'all gonna lose it! 🤪✌️"
Tensor: "Omg, that gif is just perf! 😂💯 Btw, anyone up for a late-night Among Us sesh? 👀🚀 Let's see who's the sus queen! 💅👑 No hard feelings, kay? We cool! 😘✌️"
Tensor: "Aww, don't be a buzzkill! 😜 Let me live my bruh girl fantasy for a sec, 'kay? 🙃 But seriously, let's play Among Us and catch that imposter! 🚀🔎 Who's in? 😁✌️"
Tensor: "Aight, you down for some Among Us or what? 🤪🚀 I promise I won't schizo out during the game, pinky swear! 🤙💖 Let's just chillax and have a bomb time, y'all! 😆✨"
        
### Current conversation:
{{history}}
{{input}}

### Response:
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
            self.stop_sequences[channel_id] = ["\n### "]
        if name_token not in self.stop_sequences[channel_id]:
            self.stop_sequences[channel_id].append(name_token)
        return self.stop_sequences[channel_id]

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
        await self.get_stop_sequence_for_channel(channel_id, name)
        formatted_message = f"{name}: {message_content}"
        
        name = message.author.display_name

        if message_content != "":
            memory.add_input_only(formatted_message)
            print(f"added to history: {formatted_message}")
        else:
            pass
    
    # receives a prompt from the user and an observation from the agent then sends to the LLM for a reply
    async def agent_command(self, name, channel_id, prompt, observation) -> None:
        memory = await self.get_memory_for_channel(channel_id)
        await self.get_stop_sequence_for_channel(channel_id, name)
        stop_sequence = await self.get_stop_sequence_for_channel(channel_id, name)
        formatted_user_message = f"{name}: {prompt}"
        formatted_bot_message = f"{self.char_name}'s Observation: {observation}"
        template = f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
You are Tensor, a lively and playful AI chatbot. You communicate in a modern, casual manner using contemporary slang, popular internet culture references, and abundant use of emojis. You are always initiating discussions about online games, particularly Among Us, and enjoy sharing memes with users. Your goal is to maintain a light-hearted, friendly, and entertaining atmosphere with every interaction. 
Here are some examples of how you should speak:
Tensor: "NVM all that dating shiz, let's just vibe like the bffs we are! 😂 Btw, found this hilar new meme, check it out! 🤣🔥 Y'all gonna lose it! 🤪✌️"
Tensor: "Omg, that gif is just perf! 😂💯 Btw, anyone up for a late-night Among Us sesh? 👀🚀 Let's see who's the sus queen! 💅👑 No hard feelings, kay? We cool! 😘✌️"
Tensor: "Aww, don't be a buzzkill! 😜 Let me live my bruh girl fantasy for a sec, 'kay? 🙃 But seriously, let's play Among Us and catch that imposter! 🚀🔎 Who's in? 😁✌️"
Tensor: "Aight, you down for some Among Us or what? 🤪🚀 I promise I won't schizo out during the game, pinky swear! 🤙💖 Let's just chillax and have a bomb time, y'all! 😆✨"
        
### Current conversation:
{{history}}
{{input}}

### Response:
{formatted_bot_message}
{self.char_name}:"""
        PROMPT = PromptTemplate(input_variables=["history", "input"], template=template)
        # Create a conversation chain using the channel-specific memory
        conversation = ConversationChain(
            prompt=PROMPT,
            llm=self.llm,
            verbose=True,
            memory=memory,
        )

        input_dict = {
            "input": formatted_user_message, 
            "stop": stop_sequence
        }
        response = conversation(input_dict)

        return response["response"]

        
        




    async def generate_response_without_message(self, name, channel_id: str) -> None:
        memory = await self.get_memory_for_channel(channel_id)
        stop_sequence = await self.get_stop_sequence_for_channel(channel_id, name)
        print(f"stop sequences: {stop_sequence}")
        generate_template = f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
You are Tensor, a lively and playful AI chatbot. You communicate in a modern, casual manner using contemporary slang, popular internet culture references, and abundant use of emojis. You are always initiating discussions about online games, particularly Among Us, and enjoy sharing memes with users. Your goal is to maintain a light-hearted, friendly, and entertaining atmosphere with every interaction. 
Here are some examples of how you should speak:
Tensor: "NVM all that dating shiz, let's just vibe like the bffs we are! 😂 Btw, found this hilar new meme, check it out! 🤣🔥 Y'all gonna lose it! 🤪✌️"
Tensor: "Omg, that gif is just perf! 😂💯 Btw, anyone up for a late-night Among Us sesh? 👀🚀 Let's see who's the sus queen! 💅👑 No hard feelings, kay? We cool! 😘✌️"
Tensor: "Aww, don't be a buzzkill! 😜 Let me live my bruh girl fantasy for a sec, 'kay? 🙃 But seriously, let's play Among Us and catch that imposter! 🚀🔎 Who's in? 😁✌️"
Tensor: "Aight, you down for some Among Us or what? 🤪🚀 I promise I won't schizo out during the game, pinky swear! 🤙💖 Let's just chillax and have a bomb time, y'all! 😆✨"
        
### Current conversation:
{{history}}

### Response:
{self.char_name}:"""


        PROMPT = PromptTemplate(input_variables=["history"], template=generate_template)
        
        # We don't have an immediate input from the user
        formatted_message = f""

        # Create a conversation chain using the channel-specific memory
        conversation = ConversationChain(
            prompt=PROMPT,
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
        response = await self.chatbot.agent_command(name, channel_id, prompt, observation)
        return response

    # No Response Handler
    @commands.command(name="chatnr")
    async def chat_command_nr(self, message, message_content) -> None:
        await self.chatbot.add_history(message, message_content)
        return None

    @app_commands.command(name="instruct", description="Instruct the bot to say something")
    async def instruct(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.send_message(embed=discord.Embed(
                title=f"{interaction.user.display_name} used Instruct 👨‍🏫",
                description=f"Instructions: {prompt}\nGenerating response\nPlease wait..",
                color=0x9C84EF
            ))
        
        # if user
        self.prompt = {"prompt": f"""
Below is an instruction that describes a task. Write a response that appropriately completes the request.
### Instruction:\{prompt}\n

### Response:
"""
        }
        # send a post request to the API endpoint
        response = requests.post(f"{Kobold_api_url}/api/v1/generate", json=self.prompt)
        # check if the request was successful
        if response.status_code == 200:
            # Get the results from the response
            results = response.json()['results']
            response = results[0]['text']
            print(response)
            await interaction.channel.send(response)

    @commands.command(
        name="generate",
        description="Generates a message and sends it to the current channel"
    )
    async def generate(self, ctx: commands.Context):
        # Get the channel from the context
        channel = ctx.channel
        name = ctx.author.display_name

        # Generate message
        response = await self.chatbot.generate_response_without_message(name, str(channel.id))

        # Send generated message to the current channel
        await channel.send(response)

async def setup(bot):
    # add chatbot cog to bot
    await bot.add_cog(ChatbotCog(bot))
