# update
apparently people still use this. I appreciate that so I will start improving the main repo again. I added a few changes. 

- added max tokens to env, for kobold the max is 512, so dont go over that or you will get an error

- There is now stop token support. Update your .envs based on the new sample env. just list words that you dont want to see the bot say divided by , 

- bot will now say your display name and not your username

- i modified the endpoint and conversation history to use langchain and soon i will add oobabooga support. i just need to add a line to detect what api you put as the endpoint. (ADDED)

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
- ENDPOINT: I recommend using this

https://github.com/oobabooga/text-generation-webui#one-click-installers

after you install it you will want to run with the --api parameter, or select it in the webui. Then you can set the .env endpoint as http://127.0.0.1:5000/ assuming that you are running it locally.

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
