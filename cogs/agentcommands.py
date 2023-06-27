import discord
from discord import app_commands
from discord.ext import commands

import os

from cogs.pygbot import KoboldApiLLM

from langchain import OpenAI
from langchain.tools import BaseTool, StructuredTool, Tool
from langchain.agents import initialize_agent

from langchain.utilities import WikipediaAPIWrapper
from langchain.tools import DuckDuckGoSearchRun
from langchain.utilities import PythonREPL


os.environ["OPENAI_API_KEY"] = ""

def embedder(msg):
    embed = discord.Embed(
            description=f"{msg}",
            color=0x9C84EF
        )
    return embed



class AgentCommands(commands.Cog, name="agent_commands"):
    def __init__(self, bot):
        self.bot = bot
        self.llm = ""

        # Tools
        self.wikipedia = WikipediaAPIWrapper() # Wikipedia tool
        self.search = DuckDuckGoSearchRun() # DuckDuckGo tool
        self.python_repl = PythonREPL()  # Python REPL tool
        

        self.wikipedia_tool = Tool(
            name='wikipedia',
            func= self.wikipedia.run,
            description="Useful for when you need to look up a topic, country or person on wikipedia"
        )

        self.duckduckgo_tool = Tool(
            name='DuckDuckGo Search',
            func= self.search.run,
            description="Useful for when you need to do a search on the internet to find information that another tool can't find. be specific with your input."
        )

        


    @app_commands.command(name="searchweb", description="Query Web")
    async def search_web(self, interaction: discord.Interaction, prompt: str):

        self.llm = OpenAI(temperature=0)

        name = interaction.user.display_name
        channel_id = interaction.channel.id

        await interaction.response.send_message(embed=discord.Embed(
        title=f"{interaction.user.display_name} used Search Web 🌐",
        description=f"Prompt: {prompt}",
        color=0x9C84EF
        ))

        tools = [
            Tool(
                name = "python repl",
                func=self.python_repl.run,
                description="useful for when you need to use python to answer a question. You should input python code"
            )
        ]

        tools.append(self.duckduckgo_tool)
        tools.append(self.wikipedia_tool)
        llm = OpenAI(temperature=0)

        zero_shot_agent = initialize_agent(
            agent="zero-shot-react-description",
            tools=tools,
            llm=llm,
            verbose=True,
            max_iterations=3,
        )

        observation = zero_shot_agent.run(prompt)

        response = await self.bot.get_cog("chatbot").agent_command(name, channel_id, prompt, observation)


        await interaction.channel.send(response)

    async def embedder(self, msg):
        embed = discord.Embed(
                description=f"{msg}",
                color=0x9C84EF
            )
        return embed




    @app_commands.command(name="agent_test", description="Test command")
    async def agent_test(self, interaction: discord.Interaction):
        await interaction.response.send_message("Agent Test passed.", delete_after=3)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info("Agent Commands cog loaded.")


        
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
