import chromadb
from chromadb import Settings
from chromadb.utils import embedding_functions
import uuid


class Memory:
    def __init__(self, name, db_directory="db"):
        self.db_directory = db_directory
        self.client = chromadb.Client(
            Settings(
                persist_directory=self.db_directory,
                chroma_db_impl="duckdb+parquet",
            )
        )
        self.collection_name = name  # Set the collection name to the provided name
        self.ensure_collection_exists()  # Ensure the collection exists
        self.ef = embedding_functions.DefaultEmbeddingFunction()

    def ensure_collection_exists(self):
        # Get or create the collection with the given name
        self.client.get_or_create_collection(name=self.collection_name)
        print(f"Collection '{self.collection_name}' is ready.")

    def query_db(self, query_text):
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

    def query_with_cutoff(self, query_text, cutoff):
        """
        
        Returns the closest result if the distance is less than the cutoff.
    
        """
        results = self.query_db(query_text)
        if not results or not results['distances']:
            return "Nothing found."

        closest_distance = results['distances'][0][0]
        if closest_distance > cutoff:
            return "Nothing found."

        closest_result = results['documents'][0][0]
        return closest_result

    def save_messages_to_db(self, messages):
        collection = self.client.get_or_create_collection(
            name=self.collection_name)

        for message in messages:
            embedding = self.ef([message])
            try:
                search = self.query_db(message)
                first_item_distance = search['distances'][0][0]
                if first_item_distance == 0:
                    print(
                        f"Message '{message}' is already in database. Skipped.")
                else:
                    self.add_message_to_collection(
                        collection, embedding, message)
            except Exception as e:
                print(
                    f"An error occurred while querying the database: {e}. Adding message '{message}' to the database.")
                self.add_message_to_collection(collection, embedding, message)

        self.client.persist()

    def add_message_to_collection(self, collection, embedding, message):
        unique_id = uuid.uuid4()
        collection.add(
            embeddings=embedding,
            documents=[message],
            ids=[f"id{unique_id}"],
        )
        print(f"Message '{message}' added to database.")

    def reset_db(self):
        self.client.reset()
