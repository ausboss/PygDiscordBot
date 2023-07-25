import re
import json
import requests
import discord
from discord import app_commands
from discord.ext import commands
import os
<<<<<<< Updated upstream

# configuration settings for the api
model_config = {
    "use_story": False,
    "use_authors_note": False,
    "use_world_info": False,
    "use_memory": False,
    "max_context_length": 2400,
    "max_length": 120,
    "rep_pen": 1.02,
    "rep_pen_range": 1024,
    "rep_pen_slope": 0.9,
    "temperature": 1.0,
    "tfs": 0.9,
    "top_p": 0.9,
    "typical": 1,
    "sampler_order": [6, 0, 1, 2, 3, 4, 5]
}
=======
from langchain.llms import KoboldApiLLM, TextGen
from langchain.prompts.prompt import PromptTemplate
from helpers.custom_memory import *
from dotenv import load_dotenv

# load environment STOP_SEQUENCES variables and split them in to a list by comma
load_dotenv()
CHAT_HISTORY_LINE_LIMIT = int(os.getenv("CHAT_HISTORY_LINE_LIMIT"))
STOP_SEQUENCES = os.getenv("STOP_SEQUENCES")
STOP_SEQUENCES = STOP_SEQUENCES.split(",")


#import p
>>>>>>> Stashed changes

def embedder(msg):
    embed = discord.Embed(
            description=f"{msg}",
            color=0x9C84EF
        )
    return embed


<<<<<<< Updated upstream
=======

        
>>>>>>> Stashed changes
class Chatbot:
    def __init__(self, bot):
        self.bot = bot
        self.prompt = None
        self.endpoint = bot.endpoint
<<<<<<< Updated upstream
        # Send a PUT request to modify the settings
        requests.put(f"{self.endpoint}/config", json=model_config)
        # read character data from JSON file
        with open(char_filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.char_name = data["char_name"]
            self.char_persona = data["char_persona"]
            self.char_greeting = data["char_greeting"]
=======
        self.histories = {}  # Initialize the history dictionary
        self.stop_sequences = {}  # Initialize the stop sequences dictionary
        # select KoboldApiLLM or TextGen based on endpoint
        
        self.llm = KoboldApiLLM(endpoint=self.endpoint)

             

        with open("chardata.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.char_name = data["char_name"]
            self.char_persona = data["char_persona"]
>>>>>>> Stashed changes
            self.world_scenario = data["world_scenario"]
            self.example_dialogue = data["example_dialogue"]

        # initialize conversation history and character information
        self.convo_filename = None
        self.conversation_history = ""
<<<<<<< Updated upstream
        self.character_info = f"{self.char_name}'s Persona: {self.char_persona}\nScenario: {self.world_scenario}\n{self.example_dialogue}\n"

        self.num_lines_to_keep = 20
=======
        self.top_character_info = self.format_top_character_info()
        self.bottom_character_info = self.format_bottom_character_info()
        """
        
        the format I want:
        Persona : top character info
        Scenario : top character info
        Example of Dialogues : top character info
        Chat history
        Author's Note aka bottom character info
        User message : name: message_content
        Bot Name:
        """
    
    def format_bottom_character_info(self):
        """
        This helper function formats the character_info string, including the optional parts only if they exist.
        """
        info_str = f"\n{self.char_name}'s Persona: {self.char_persona}\n"
            
        return info_str

        
    def format_top_character_info(self):
        """
        This helper function formats the character_info string, including the optional parts only if they exist.
        """
        info_str = f"Character: {self.char_name}\n{self.char_name}'s Persona: {self.char_persona}\n"

        if self.world_scenario:  # Check if world_scenario exists
            info_str += f"Scenario: {self.world_scenario}\n"
        
        if self.example_dialogue:  # Check if example_dialogue exists
            info_str += f"Example Dialogue:\n{self.example_dialogue}\n"
            
        return info_str
    
    # if message starts with . or / then it is a command and should not be appended to the conversation history. do not use flatten use append
    async def get_messages_by_channel(self, channel_id):
        channel = self.bot.get_channel(int(channel_id))
        messages = []

        async for message in channel.history(limit=None):
            # Skip messages that start with '.' or '/'
            if message.content.startswith('.') or message.content.startswith('/'):
                continue

            messages.append((message.author.display_name, message.channel.id, message.clean_content.replace("\n", " ")))

            # Break the loop once we have at least 5 non-skipped messages
            if len(messages) >= CHAT_HISTORY_LINE_LIMIT:
                break

        return messages[:CHAT_HISTORY_LINE_LIMIT]  # Return the first 5 non-skipped messages

        
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
        
    
    
    async def get_memory_for_channel(self, channel_id):
        """Get the memory for the channel with the given ID. If no memory exists yet, create one."""
        channel_id = str(channel_id)
        if channel_id not in self.histories:
            # Create a new memory for the channel
            
            self.histories[channel_id] = CustomBufferWindowMemory(
                k=CHAT_HISTORY_LINE_LIMIT, ai_prefix=self.char_name
            )
            # Get the last 5 messages from the channel in a list
            messages = await self.get_messages_by_channel(channel_id)
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
            self.stop_sequences[channel_id] = STOP_SEQUENCES
            
        if name_token not in self.stop_sequences[channel_id]:
            self.stop_sequences[channel_id].append(name_token)
        
        return self.stop_sequences[channel_id]
>>>>>>> Stashed changes

    async def set_convo_filename(self, convo_filename):
        # set the conversation filename and load conversation history from file
        self.convo_filename = convo_filename
        if not os.path.isfile(convo_filename):
            # create a new file if it does not exist
            with open(convo_filename, "w", encoding="utf-8") as f:
                f.write("<START>\n")
        with open(convo_filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
            num_lines = min(len(lines), self.bot.num_lines_to_keep)
            self.conversation_history = "<START>\n" + "".join(lines[-num_lines:])

<<<<<<< Updated upstream
    async def save_conversation(self, message, message_content):
        self.conversation_history += f'{message.author.name}: {message_content}\n'
        # define the prompt
        self.prompt = {
            "prompt": self.character_info + '\n'.join(
                self.conversation_history.split('\n')[-self.num_lines_to_keep:]) + f'{self.char_name}:',
        }
        # send a post request to the API endpoint
        response = requests.post(f"{self.endpoint}/api/v1/generate", json=self.prompt)
        # check if the request was successful
        if response.status_code == 200:
            # Get the results from the response
            results = response.json()['results']
            response_list = [line for line in results[0]['text'][1:].split("\n")]
            result = [response_list[0]]
            for item in response_list[1:]:
                if self.char_name in item:
                    result.append(item)
                else:
                    break
            new_list = [item.replace(self.char_name + ": ", '\n') for item in result]
            response_text = ''.join(new_list)
            # add bot response to conversation history
            self.conversation_history = self.conversation_history + f'{self.char_name}: {response_text}\n'
            with open(self.convo_filename, "a", encoding="utf-8") as f:
                f.write(f'{message.author.name}: {message_content}\n')
                f.write(f'{self.char_name}: {response_text}\n')  # add a separator between

            return response_text

    async def follow_up(self):
        self.conversation_history = self.conversation_history
        self.prompt = {
            "prompt": self.character_info + '\n'.join(
                self.conversation_history.split('\n')[-self.num_lines_to_keep:]) + f"{self.char_name}:",
        }
        print(self.prompt)
        response = requests.post(f"{self.endpoint}/api/v1/generate", json=self.prompt)
        print(response.json()['results'])
        # check if the request was successful
        if response.status_code == 200:
            # Get the results from the response
            results = response.json()['results']
            response_list = [line for line in results[0]['text'][1:].split("\n")]
            result = [response_list[0]]
            for item in response_list[1:]:
                if self.char_name in item:
                    result.append(item)
                else:
                    break
            new_list = [item.replace(self.char_name + ": ", '\n') for item in result]
            response_text = ''.join(new_list)
            self.conversation_history = self.conversation_history + f'{self.char_name}: {response_text}\n'
            with open(self.convo_filename, "a", encoding="utf-8") as f:
                f.write(f'{self.char_name}: {response_text}\n')  # add a separator between
            return response_text


=======
    async def generate_response(self, message, message_content) -> None:
        channel_id = str(message.channel.id)
        name = message.author.display_name
        memory = await self.get_memory_for_channel(str(channel_id))
        stop_sequence = await self.get_stop_sequence_for_channel(channel_id, name)
        print(f"stoop sequence: {stop_sequence}")
        print(f"stop sequences: {stop_sequence}")
        formatted_message = f"{name}: {message_content}"
        MAIN_TEMPLATE = f'''
{self.top_character_info}
{{history}}
{{input}}
{self.char_name}:'''
        
        PROMPT = PromptTemplate(
            input_variables=["history", "input"], 
            template=MAIN_TEMPLATE
        )
                
        # Create a conversation chain using the channel-specific memory
        conversation = ConversationChain(
            prompt=PROMPT,
            llm=self.llm,
            verbose=True,
            memory=memory,
        )
        input_dict = {"input": formatted_message, "stop": stop_sequence}
        response_text = conversation(input_dict)
        response = await self.detect_and_replace_out(response_text["response"])
        with open(self.convo_filename, "a", encoding="utf-8") as f:
            f.write(f'{message.author.display_name}: {message_content}\n')
            f.write(f'{self.char_name}: {response_text}\n')  # add a separator between

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
            
>>>>>>> Stashed changes

class ChatbotCog(commands.Cog, name="chatbot"):
    def __init__(self, bot):
        self.bot = bot
        self.chatlog_dir = bot.chatlog_dir
        self.chatbot = Chatbot(bot)

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
        response = await self.chatbot.generate_response(message, message_content)
        return response



async def setup(bot):
    # add chatbot cog to bot
    await bot.add_cog(ChatbotCog(bot))