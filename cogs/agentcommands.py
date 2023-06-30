import discord
from discord import app_commands
from discord.ext import commands

import os
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.document_loaders import WikipediaLoader
from langchain.tools import BaseTool, StructuredTool, Tool
from langchain.agents import initialize_agent

from langchain.utilities import WikipediaAPIWrapper
from langchain.tools import DuckDuckGoSearchRun
from langchain.utilities import PythonREPL
from dotenv import load_dotenv

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
        self.llm = ""
        os.environ["OPENAI_API_KEY"] = self.bot.openai
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
        print(f"Observation: {observation}")

        response = await self.bot.get_cog("chatbot").agent_command(name, channel_id, prompt, observation)


        await interaction.channel.send(response)



    @app_commands.command(name="agent_test", description="Test command")
    async def agent_test(self, interaction: discord.Interaction):
        await interaction.response.send_message("Agent Test passed.", delete_after=3)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info("Agent Commands cog loaded.")


    








        
    # create a command for the wiipedia chroma code is in the wikichroma copy.ipynb that will use the agent_command from pygbot
    @app_commands.command(name="wikipedia", description="Wikipedia Search")
    async def wikipedia_search(self, interaction: discord.Interaction, topic: str, wikipedia: str, query: str):
        
        loader = WikipediaLoader(query=wikipedia, load_max_docs=100)
        documents = loader.load()
        #splitting the text into
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)

        """## create the DB"""

        # Embed and store the texts
        # Supplying a persist_directory will store the embeddings on disk
        persist_directory = 'db'

        ## here we are using OpenAI embeddings but in future we will swap out to local embeddings
        embedding = OpenAIEmbeddings()

        vectordb = Chroma.from_documents(documents=texts,
                                        embedding=embedding,
                                        persist_directory=persist_directory)

        # persiste the db to disk
        vectordb.persist()
        vectordb = None

        # Now we can load the persisted database from disk, and use it as normal.
        vectordb = Chroma(persist_directory=persist_directory,
                        embedding_function=embedding)

        """## Make a retriever"""

        retriever = vectordb.as_retriever()
        docs = retriever.get_relevant_documents(query)
        len(docs)
        retriever = vectordb.as_retriever(search_kwargs={"k": 5})
        retriever.search_type
        retriever.search_kwargs

        # create the chain to answer questions
        qa_chain = RetrievalQA.from_chain_type(llm=OpenAI(),
                                        chain_type="stuff",
                                        retriever=retriever,
                                        return_source_documents=True)
                                        
        await interaction.response.send_message(embed=discord.Embed(
        title=f"{interaction.user.display_name} used Wikipedia Search 🔍",
        description=f"Prompt: {topic}",
        color=0x9C84EF
        ), timeout=3)
        # create a conversation thread in discord that will allow the user to ask questions about the topic
        self.llm_response = qa_chain(query)
        await interaction.channel.send(self.llm_response)













async def setup(bot):
    await bot.add_cog(AgentCommands(bot))
