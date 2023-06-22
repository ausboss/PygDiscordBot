import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import re
import requests
from getpass import getpass
from pathlib import Path
import inspect
import langchain
from langchain.chains import ConversationChain, LLMChain, LLMMathChain, TransformChain, SequentialChain
from langchain.chat_models import ChatOpenAI
from langchain.docstore import InMemoryDocstore
from langchain.llms.base import LLM, Optional, List, Mapping, Any
from langchain.embeddings.openai import OpenAIEmbeddings
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
from cogs.pygbot import KoboldApiLLM
from langchain.utilities import WikipediaAPIWrapper


def embedder(msg):
    embed = discord.Embed(
            description=f"{msg}",
            color=0x9C84EF
        )
    return embed



class AgentCommands(commands.Cog, name="agent_commands"):
    def __init__(self, bot):
        self.bot = bot
        self.llm = KoboldApiLLM()

    @app_commands.command(name="agent_test", description="Test command")
    async def agent_test(self, interaction: discord.Interaction):
        await interaction.response.send_message("Agent Test passed.", delete_after=3)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Agent Commands cog loaded.")


    async def embedder(self, msg):
        embed = discord.Embed(
                description=f"{msg}",
                color=0x9C84EF
            )
        return embed
        
    @app_commands.command(name="gorillallm", description="Query Gorilla")
    async def gorilla_call(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.send_message(embed=discord.Embed(
        title=f"{interaction.user.display_name} used GorillaLLM 🦍",
        description=f"Prompt: {prompt}",
        color=0x9C84EF
        ))
        
        response = await self.bot.get_cog("gorilla_llm").gorilla_query(prompt)
        
        await self.bot.get_cog("chatbot").agent_command(interaction, prompt, response)
        await interaction.channel.send(response)

    
    # @app_commands.command(name="wikipedia", description="Search Wikipedia")
    # async def wikipedia(self, interaction: discord.Interaction, prompt: str):
    #     await interaction.response.send_message(embed=discord.Embed(
    #     title=f"{interaction.user.display_name} used Wikipedia",
    #     description=f"Prompt: {prompt}",
    #     color=0x9C84EF
    #     ))
    #     tools = load_tools(["wikipedia"], llm=self.llm)
    #     agent = initialize_agent(tools, self.llm, agent="zero-shot-react-description", verbose=True)
    #     response = agent.run(f"Below is an instruction that describes a task. Write a response that appropriately completes the request.\n\n### Instruction:\n{prompt}\n\n### Response:\n")
    #     await self.bot.get_cog("chatbot").agent_command(interaction, prompt, response)
    #     await interaction.channel.send(response)

#     @app_commands.command(name="wikipedia", description="Search Wikipedia")
#     async def wikipedia(self, interaction: discord.Interaction, prompt: str):
#         await interaction.response.send_message(embed=discord.Embed(
#         title=f"{interaction.user.display_name} used Wikipedia",
#         description=f"Prompt: {prompt}",
#         color=0x9C84EF
#         ))
#         wikipedia = WikipediaAPIWrapper()
#         response = wikipedia.run(prompt)
#         await self.bot.get_cog("chatbot").agent_command(interaction, prompt, response)
#         await interaction.channel.send(response)
    
    
        
#     @app_commands.command(name="duckduckgo", description="Search Wikipedia")
#     async def duckduckgo_search(self, interaction: discord.Interaction, prompt: str):
#         await interaction.response.send_message(embed=discord.Embed(
#         title=f"{interaction.user.display_name} used Wikipedia",
#         description=f"Prompt: {prompt}",
#         color=0x9C84EF
#         ))
#         # Define which tools the agent can use to answer user queries
#         search = DuckDuckGoSearchRun()
#         tools = [
#             Tool(
#                 name = "Search",
#                 func=search.run,
#                 description="useful for when you need to answer questions about current events"
#             )
#         ]

#         template = """
# Please follow the steps below to answer the question using the available tools. Repeat the steps as necessary until you find a solution.

# ### Instruction:
# Answer the question: {input}
# You have access to the following tools: {tools}

# ### Steps:
# 1. Think about the question and the best tool to use.
# 2. Perform the action using the selected tool.
# 3. Observe the results of the action and provide the final answer.

# ### Response Format:
# Thought: Your thought process.
# Action: The name of the tool (one word only, from {tool_names}).
# Action Input: The input you provide to the tool.
# Observation: The results obtained from using the tool.
# Final Answer: The answer to the question based on your observation.
# """
#         prompt = CustomPromptTemplate(
#         template=template,
#         tools=tools,
#         # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
#         # This includes the `intermediate_steps` variable because that is needed
#         input_variables=["input", "intermediate_steps"]
#         )
        
#         search = DuckDuckGoSearchRun()
#         response = search.run(prompt)


#         agent = initialize_agent(tools, self.llm, agent="zero-shot-react-description", verbose=True)
#         response = agent.run(f"Below is an instruction that describes a task. Write a response that appropriately completes the request.\n\n### Instruction:\n{prompt}\n\n### Response:\n")
#         await self.bot.get_cog("chatbot").agent_command(interaction, prompt, response)
#         await interaction.channel.send(response)
    
    


async def setup(bot):
    await bot.add_cog(AgentCommands(bot))
