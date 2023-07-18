import discord
from discord import app_commands
from discord.ext import commands

import os
from langchain.tools import DuckDuckGoSearchRun
from dotenv import load_dotenv
from helpers.constants import BOTNAME
from langchain.chains import LLMMathChain
from langchain.agents import Tool
from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain import OpenAI
# Load .env file
load_dotenv()

OPENAI = os.getenv('OPENAI')


def embedder(msg):
    embed = discord.Embed(
            description=f"{msg}",
            color=0x9C84EF
        )
    return embed


class AgentCommands(commands.Cog, name="agent_commands"):

    def __init__(self, bot):
        self.bot = bot
        self.llm = self.bot.llm
        self.bot

        self.search = DuckDuckGoSearchRun()  # DuckDuckGo tool

    # calculator command that will take a message and return the result of the calculation
    async def _execute_calculation(self, display_name: str, channel_id: int, prompt: str):
        """Executes a calculation and returns a formatted response."""
        
        tool = "Calculator"
        llm = OpenAI(
            openai_api_key=OPENAI,  # platform.openai.com
            temperature=0,
            model_name="text-davinci-003"
        )

        llm_math = LLMMathChain(llm=llm)
        # initialize the math tool
        math_tool = Tool(
            name='Calculator',
            func=llm_math.run,
            description='Useful for when you need to answer questions about math.'
        )
        # when giving tools to LLM, we must pass as list of tools
        tools = [math_tool]

        zero_shot_agent = initialize_agent(
            agent="zero-shot-react-description",
            tools=tools,
            llm=llm,
            verbose=True,
            max_iterations=3
        )

        straight_response = zero_shot_agent(prompt)
        output_string = straight_response["output"]
        input_string = f"Tensor used the {tool} tool to find the answer\nResult: {output_string}"

        response = await self.bot.get_cog("chatbot").agent_command(
            display_name,
            channel_id,
            prompt,
            tool,
            input_string
        )

        return response

    @commands.command(name="calculator")
    async def execute_calculation_message(self, message, message_content) -> None:
        """This command takes a message and returns the result of the calculation."""
        
        return await self._execute_calculation(
            message.author.display_name,
            message.channel.id,
            message_content
        )

    @commands.command(name="calculatorinteraction")
    async def execute_calculation_interaction(self, interaction: discord.Interaction, prompt: str):
        """This command performs a calculation based on an interaction and prompt."""
        
        return await self._execute_calculation(
            interaction.user.display_name,
            interaction.channel.id,
            prompt
        )

    @app_commands.command(name="calculatorcommand", description="Perform Calculation")
    async def calculate(self, interaction: discord.Interaction, prompt: str):
        """This command performs a calculation and sends an embedded response message to the channel."""
        
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{interaction.user.display_name} used Calculator",
                description=f"Instructions: {prompt}\nGenerating response\nPlease wait..",
                color=0x9C84EF,
            )
        )

        response = await self._execute_calculation(interaction.user.display_name, interaction.channel.id, prompt)

        await interaction.channel.send(response)

    # websearch functions    

    async def _execute_search(self, display_name: str, channel_id: int, prompt: str):
        """Executes a web search and returns a formatted response."""
        
        tool = "Web Search"
        results = self.search(prompt)
        straight_response = await self.bot.get_cog("chatbot").instruct_input(prompt, results)



        response = await self.bot.get_cog("chatbot").agent_command(
            display_name,
            channel_id,
            prompt,
            tool,
            straight_response
        )

        return response

    @commands.command(name="searchwebmessage")
    async def execute_search_message(self, message, message_content) -> None:
        """This command takes a message and returns the result of the calculation."""
        
        return await self._execute_search(
            message.author.display_name,
            message.channel.id,
            message_content
        )

    @commands.command(name="searchwebinteraction")
    async def execute_search_interaction(self, interaction: discord.Interaction, prompt: str):
        """This command performs a web search based on an interaction and prompt."""
        
        return await self._execute_search(
            interaction.user.display_name,
            interaction.channel.id,
            prompt
        )

    @app_commands.command(name="searchwebcommand", description="Query Web")
    async def search_web(self, interaction: discord.Interaction, prompt: str):
        """This command performs a web search and sends an embedded response message to the channel."""
        
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{interaction.user.display_name} used Search Web",
                description=f"Instructions: {prompt}\nGenerating response\nPlease wait..",
                color=0x9C84EF,
            )
        )

        response = await self._execute_search(interaction.user.display_name, interaction.channel.id, prompt)

        await interaction.channel.send(response)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info("Agent Commands cog loaded.")

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

        

        async with interaction.channel.typing():
            response = await self.bot.get_cog("chatbot").instruct(prompt)

            # Check if response is not None
            if response:
                await self.bot.get_cog("chatbot").chat_command_nr(interaction.user.display_name, str(channel_id), prompt)

                # If the response is more than 2000 characters, split it
                chunks = [response[i:i + 1998] for i in range(0, len(response), 1998)]
                for chunk in chunks:
                    print(chunk)
                    response_obj = await interaction.channel.send(response)
                    await self.bot.get_cog("chatbot").chat_command_nr(BOTNAME, str(response_obj.channel.id), response_obj.clean_content)

                # check if the request was successful
            else:
                print("No response received from the chatbot")
                # You can also send a message to the channel to notify the user that there was no response from the bot.
                # await interaction.channel.send("No response received from the bot")



async def setup(bot):
    await bot.add_cog(AgentCommands(bot))
