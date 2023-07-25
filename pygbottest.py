import json

class Chatbot:
    def __init__(self, char_filename):
        self.prompt = None
        # self.endpoint = bot.endpoint
        self.histories = {}  # Initialize the history dictionary
        self.stop_sequences = {}  # Initialize the stop sequences dictionary
        # self.llm = KoboldApiLLM(endpoint=self.endpoint)

        with open(char_filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.char_name = data.get("char_name", "")
            self.char_persona = data.get("char_persona", "")
            self.world_scenario = data.get("world_scenario", "")
            self.example_dialogue = data.get("example_dialogue", "")

        # initialize conversation history and character information
        self.convo_filename = None
        self.conversation_history = ""
        self.character_info = self.format_character_info()
        
    def format_character_info(self):
        """
        This helper function formats the character_info string, including the optional parts only if they exist.
        """
        info_str = f"Character: {self.char_name}\n{self.char_name}'s Persona: {self.char_persona}\n"

        if self.world_scenario:  # Check if world_scenario exists
            info_str += f"Scenario: {self.world_scenario}\n"
        
        if self.example_dialogue:  # Check if example_dialogue exists
            info_str += f"Example Dialogue:\n{self.example_dialogue}\n"
            
        return info_str
    
    
chatbot = Chatbot("chardata.json")

print(chatbot.format_character_info())
