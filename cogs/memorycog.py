import discord
from discord import app_commands
from discord.ext import commands
import chromadb
from chromadb import Settings
from chromadb.utils import embedding_functions
import uuid

async def embedder(msg):
    embed = discord.Embed(
        description=f"{msg}",
        color=0x9C84EF
    )
    return embed

print("Loading memorycog.py")

class Memory(commands.Cog, name="memory_cog"):
    def __init__(self, bot):
        self.bot = bot
        self.client = chromadb.PersistentClient(path="/db")
        self.ef = embedding_functions.DefaultEmbeddingFunction()

    async def ensure_collection_exists(self):
        # Get or create the collection with the given name
        self.client.get_or_create_collection(name=self.collection_name)
        print(f"Collection '{self.collection_name}' is ready.")

    async def query_db(self, query_text):
        try:
            collection = self.client.get_collection(self.collection_name)
        except:
            print("There was an issue loading the collection.")
            return ""

        query_embedding = self.ef([query_text])

        results = collection.query(
            query_embeddings=query_embedding,
            n_results=5
        )

        return results

    async def query_with_cutoff(self, query_text, cutoff):
        """

        Returns the closest result if the distance is less than the cutoff.

        """
        results = await self.query_db(query_text)
        if not results or not results['distances']:
            return "Nothing found."

        closest_distance = results['distances'][0][0]
        if closest_distance > cutoff:
            return "Nothing found."

        closest_result = results['documents'][0][0]
        return closest_result

    async def save_messages_to_db(self, messages):
        collection = self.client.get_or_create_collection(
            name=self.collection_name)

        for message in messages:
            embedding = self.ef([message])
            try:
                search = await self.query_db(message)
                first_item_distance = search['distances'][0][0]
                if first_item_distance == 0:
                    return f"Message '{message}' already exists in the database."
                else:
                    await self.add_message_to_collection(
                        collection, embedding, message)
                    return f"Message '{message}' added to database."
            except Exception as e:
                print(
                    f"An error occurred while querying the database: {e}. Adding message '{message}' to the database.")
                await self.add_message_to_collection(collection, embedding, message)


    async def add_message_to_collection(self, collection, embedding, message):
        unique_id = uuid.uuid4()
        collection.add(
            embeddings=embedding,
            documents=[message],
            ids=[f"id{unique_id}"],
        )
        print(f"Message '{message}' added to database.")

    async def reset_db(self):
        self.client.reset()


    @app_commands.command(name="add_memory", description="Add a memory")
    async def add_memory(self, interaction: discord.Interaction, text: str):
        # defer the response to avoid the "thinking" state
        # await interaction.response.defer()
        # Set the collection name to the user ID, converted to a string
        self.collection_name = str(interaction.user.id)
        print(f"collection_name: {self.collection_name}")
        await self.ensure_collection_exists()
        response = await self.save_messages_to_db([text])
        await interaction.response.send_message(response, ephemeral=True)
        
    #app command to query the database and print the result
    @app_commands.command(name="query_memory", description="Query a memory")
    async def query_memory(self, interaction: discord.Interaction, text: str):
        print(f"collection_name: {interaction.user.id}")

        # Set the collection name to the channel ID
        self.collection_name = str(interaction.user.id)
        await self.ensure_collection_exists()
        result = await self.query_with_cutoff(text, 0.5)
        await interaction.response.send_message(result)
        
    # takes the message and message content, it will find the db based on the collection name and use the message content as the query
    # if the query is found, it will return the result or else it will return an empty string
    @commands.command(name="query_memory")
    async def query_memory_live(self, name, channel_id, message_content, message) -> None:
        print(f"collection_name: {message.author.id}")
        self.collection_name = str(message.author.id)
        await self.ensure_collection_exists()
        query_message = f"{message_content}"
        print(self.query_db(query_message))
        result = await self.query_with_cutoff(query_message, 0.6)
        print(f'query_memory: {result}')
        if result == "Nothing found.":
            return ""
        return f"{name}: {result}"
        

async def setup(bot):
    await bot.add_cog(Memory(bot))
