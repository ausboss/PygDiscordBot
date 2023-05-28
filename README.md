# Make sure to show some love to ausboss, all I did was tweak their work!

# Discord Tavern Style Chatbot for KoboldCpp with Pygmalion-style chat models
This is a discord bot that connects to a KoboldAI endpoint and uses the Pygmalion style chat prompt system to communicate back and forth. It supports TavernAI cards and jsons.

I have made the following changes from the original repo by ausboss:

> Changed the variables to be submitted in the prompt post request. It appears that this is the preferred way for KoboldCpp to work
> Tweaked the variables to be LLaMA model compatible.
> Improved support for models not strictly trained on the Pyg dataset by detecting and trimming cases where the model starts hallucinating what users say to it without making new lines.
> Some code tweaks to reduce repetition
> A few new slash commands for my convenience when testing

I've done most of my testing and development with Manticore-13B. I have tried Pygmalion-13B with good results too.



# Instructions: 
>1. Clone the repo.

>2. Change the variables in the sample.env file and save it as .env in the same folder

>3. Run the setup.bat file

>4. Run the run.bat file

>5. Choose the character

Go to the original repo for more instructions.


# Slash Commands: 

| Command Name   | Slash Command    | More Info                                                                               |
| ---            | ---              | ---                                                                                     |
| Sync Commands  | `/sync`          | Needed to make the commands appear right away.                                         |
| Reload Cog     | `/reload <name>` | Lets you reload a specific cog instead of needing to restart everything.               |
|Regenerate Last Message| `/regenerate`| Removes the last message and will generate another one                |
| Follow up      | `/followup`      | Tell the bot to generate another message on top of the last one it sent  |
| Reset Conversation    | `/reset_conversation`      | Erases the current conversation and returns the context window to a clean slate. |
