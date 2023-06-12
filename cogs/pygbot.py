import re
import json
import requests
import asyncio
from typing import Any, List, Mapping, Optional

from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import commands
from discord.ext.commands import Bot
from typing import Any, List, Mapping, Optional
import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings
import uuid
import langchain
from langchain.docstore.document import Document
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory, ChatMessageHistory, ConversationBufferWindowMemory
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.llms.base import LLM
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
import os
from langchain.prompts import PromptTemplate, ChatPromptTemplate

history = ChatMessageHistory()


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
            "http://127.0.0.1:5000/api/v1/generate",
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
        global endpoint
        self.prompt = None
        self.endpoint = bot.endpoint
        endpoint = self.endpoint
        # read character data from JSON file
        with open(char_filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.char_name = data["char_name"]
            self.char_persona = data["char_persona"]
            self.char_greeting = data["char_greeting"]
            self.world_scenario = data["world_scenario"]
            self.example_dialogue = data["example_dialogue"]

        # initialize conversation history and character information
        self.collection = self.create_collection(self.create_chromadb_client(), "chat-messages")
        self.model = embedding_functions.DefaultEmbeddingFunction()
        self.convo_filename = None
        self.llm = KoboldApiLLM()
        self.ai_prefix = self.char_name
        self.human_prefix = ""
        self.num_lines_to_keep = 20
        self.extra_input = "No Extra Input"
        self.memory = ConversationBufferWindowMemory(
            k=self.num_lines_to_keep, ai_prefix=self.char_name)

    async def set_convo_filename(self, convo_filename):
        # set the conversation filename and load conversation history from file
        self.convo_filename = convo_filename
        if not os.path.isfile(convo_filename):
            # create a new file if it does not exist
            with open(convo_filename, "w", encoding="utf-8") as f:
                f.write("<START>\n")
        with open(convo_filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
            num_lines = min(len(lines), self.num_lines_to_keep)
            self.conversation_history = "<START>\n" + "".join(lines[-num_lines:])

    conversation_with_summary = ConversationChain(

    # We set a low k=2, to only keep the last 2 interactions in memory
    memory=ConversationBufferWindowMemory(k=2), 
    verbose=True)
    conversation_with_summary.predict(input="Hi, what's up?")

    def create_chromadb_client(self) -> chromadb.Client:
        return chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="./chroma_db"
        ))

    def create_collection(self, client: chromadb.Client, name: str):
        return client.get_or_create_collection(name)

    def add_docs_to_collection(self, collection, docs: List[Document], embeddings: List[List[float]]):
        for doc, embedding in zip(docs, embeddings):
            doc_id = str(uuid.uuid4())
            collection.add(documents=[doc.page_content], embeddings=[embedding], ids=[doc_id])
    
    def save_db(self, client: chromadb.Client):
        client.persist()

    def text_to_docs(self, text: List[str]) -> List[Document]:
        doc_chunks = []
        for i, message in enumerate(text):
            doc = Document(
                page_content=message,
                metadata={
                    "message_number": i,
                    "source": f"m{i}",
                },
            )
            doc_chunks.append(doc)
        return doc_chunks

    async def save_conversation(self, message, message_content) -> None:
        name = message.author.name
        user_message = message_content

        new_document = self.text_to_docs([message])[0]
        # Generate the embedding for the new message
        new_embedding = self.model.encode([message])[0].tolist()

        # Add the document and embedding to the collection
        self.add_docs_to_collection(self.collection, [new_document], [new_embedding])

        # Query the collection with the new message
        query_embedding = self.model.encode([message])[0]
        results = self.collection.query(query_texts=[message], n_results=1)
        
        if results:  # If a relevant message was found in the database
            # Retrieve the most relevant message
            most_relevant_message = results[0].documents[0].text

            # Use it as extra input
            self.extra_input = most_relevant_message
  
        self.template = f"""### Instruction:
        The following is a chat transcript between {self.char_name} and her friends. You are {self.char_name}.\nContinue the message conversation.\n### Input:\n{self.extra_input}\n{self.char_name}'s Persona: {self.char_persona} also a little racist and dislikes the gay community and is unapologetic about it.
        {self.example_dialogue}
        {{history}}
        {{input}}
        ### Response:
        {self.char_name}:"""

        self.PROMPT = PromptTemplate(
            input_variables=["history", "input"], template=self.template)
        self.conversation = ConversationChain(
            prompt=self.PROMPT, llm=self.llm, verbose=True, memory=self.memory)
        # the input should be the name of the user and the message content {Name: message}
        formatted_input = f"{name}: {user_message}"
        response = self.conversation.run(input=formatted_input).strip()
        with open(self.convo_filename, "a", encoding="utf-8") as f:
            f.write(f'{message.author.name}: {message_content}\n')
            f.write(f'{self.char_name}: {response}\n')  # add a separator between

        return response


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
        if message.guild:
            server_name = message.channel.name
        else:
            server_name = message.author.name
        chatlog_filename = os.path.join(self.chatlog_dir, f"{self.chatbot.char_name}_{server_name}_chatlog.log")
        if message.guild and self.chatbot.convo_filename != chatlog_filename or \
                not message.guild and self.chatbot.convo_filename != chatlog_filename:
            await self.chatbot.set_convo_filename(chatlog_filename)
            response = await self.chatbot.save_conversation(message, message_content)
            return response
    
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
        await interaction.response.send_message(embed=await self.wait_embedder(interaction.user.name), delete_after=7)
        
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
