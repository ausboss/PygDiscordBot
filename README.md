# update
apparently people still use this. I appreciate that so I will start improving the main repo again. I added a few changes. 

-There is now stop token support. Update your .envs based on the new sample env. just list words that you dont want to see the bot say divided by , 

-bot will now say your display name and not your username

-i modified the endpoint and conversation history to use langchain and soon i will add oobabooga support. i just need to add a line to detect what api you put as the endpoint.

-more to come soon..

# Original Info Card: Discord Tavern Style LLM Chatbot

This Discord bot utilizes LLMs and character cards for casual chatting. The bot supports JSON files and tavern cards, offering the option to automatically update the bot's image and name.

![image](https://i.imgur.com/VPzquLom.png)

# Instructions

1. Clone the repository.
2. Modify the variables in the sample.env file and save it as .env in the same folder.
3. Run the setup.bat file.
4. Run the run.bat file.
5. Choose the character.

![Choose](https://i.imgur.com/qY6ZpB8.png)

Please note that Discord only allows bots to be renamed twice per hour.

# More Information

- DISCORD_BOT_TOKEN: Obtain this token from the Discord Developer Portal. [Guide for setting that up](https://rentry.org/discordbotguide)
- ENDPOINT: Set the endpoint variable with the KoboldAI URL obtained from this [colab](https://colab.research.google.com/github/koboldai/KoboldAI-Client/blob/main/colab/GPU.ipynb). Simply press Shift + Enter to run the cells until you acquire the API URL. Alternatively, if you have a powerful GPU, you can run Kobold locally using [Kobold](https://github.com/KoboldAI/KoboldAI-Client) or its [Kobold 4bit fork](https://github.com/0cc4m/KoboldAI).
  For more information on running it locally, refer to: [Local Installation (GPU)](https://docs.alpindale.dev/local-installation-(gpu)/kobold/)

# Slash Commands

Currently, these commands are primarily useful for developers. If you don't see them, use the `/sync` command to force their appearance.

| Command Name          | Slash Command   | More Info                                                      |
|-----------------------|-----------------|----------------------------------------------------------------|
| Sync Commands         | `/sync`         | Forces the slash commands to appear immediately.               |
| Reload Cog            | `/reload <name>`| Reloads a specific cog instead of restarting everything.       |
| Regenerate Last Message| `/regenerate`   | Removes the last message and generates another one.             |

# Tip for making the .env file
## Enable file name extensions
> Windows 11:

![win11img](https://i.imgur.com/HayEcPol.png)
> Windows 10:

![win10img](https://i.imgur.com/BsmMUjo.png)
## Now you can easily rename it to .env
![envgif](https://github.com/ausboss/PygDiscordBot/blob/main/how-to-env.gif)
