import discord
from discord import app_commands
from discord.ext import commands

message_list = []

# join message list by \n
message_list = "\n".join(message_list)



class ExtraLogic(commands.Cog, name="extra_logic"):

    def __init__(self, bot):
        self.bot = bot
        self.llm = self.bot.llm

    @commands.command(name="myturn")
    async def my_turn(self, message_list):

        # create a prompt that will be used to generate a response
        prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request. Think step by step.

### Instruction:
True or False? It is Tensor's turn to reply. 

### Input:
Austin: hi tensor
Tensor: Hey there, Austin! 👋😄 What's up?
Austin: nothing much. whats up with you?
Stompy: tensor if you were a kingdom hearts character who would you be?
Austin:  [Austin posts a picture of a screenshot of a text message with the text'''']
Tensor: Oh hey Stompy! If I was a Kingdom Hearts character, I'd be a mischievous and playful Keyblade Master like Vexen from Kingdom Hearts II! 😁🔥👊 We could have so much fun with our wacky adventures and witty banter! 💪🎉
Stompy:  [Stompy posts a picture of a man in a black coat and a black coat]
Stompy: you do look just like him

### Response:
True. The last message was directed at Tensor.

Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request. Think step by step.

### Instruction:
True or False? It is Tensor's turn to reply. 

### Input:
Austin: Hi Stompy
Stompy: Yo whats up?
Austin: Not much. Whats up with you?
Stompy: Nothing much. How are you Tensor?

### Response:
True. Because Stompy asked Tensor a question.

Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request. Think step by step.

### Instruction:
True or False? The last message was directed at Tensor.

### Input:
Austin: Hello Tensor
Tensor: Hey there, Austin! How's it going? 👋🙃
Austin: Pretty good. How's it going with you?

### Response:
True. Austin asked Tensor. "How's it going with you?".

Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request. Think step by step.

### Instruction:
True or False? The last message was directed at Tensor.

### Input:
Austin: Hello Stompy.
Stompy: Yo whats up?
Austin: Not much. Whats up with you? 

### Response:
False. The last message was not directed at Tensor.

Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request. Think step by step.

### Instruction:
True or False? The last message was directed at Tensor. 

### Input:
Austin: Hi Tensor
Tensor: Hey there, Austin! How's life treating you? 👋🙂
Austin: good. How about you?

### Response:
True. The last message was directed at Tensor.

Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request. Think step by step.

### Instruction:
True or False? The last message was directed at Tensor.
 
### Input:
Austin: Hello Tensor
Tensor: Hey there, Austin! How's it going? 👋🙃
Austin: Pretty good. Yo Stompy! Are you up?

### Response:
False. The last message was not directed at Tensor. Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request. Think step by step.

Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request. Think step by step.

### Instruction:
True or False? The last message was directed at Tensor.
 
### Input: 
{message_list}

### Response:
"""

        response = self.llm(prompt, temperature=0.5)
        # remove blank spaces before and after the response
        response = response.strip()
        print(response)
        # check if the response starts with True or False
        if response.startswith("True"):
            print("True")
            return True
        elif response.startswith("False"):
            print("False")
            return False
        else:
            print("Error")
            return False


async def setup(bot):
    await bot.add_cog(ExtraLogic(bot))
