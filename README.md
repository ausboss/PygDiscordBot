# Discord Tavern Style Pygmalion Chatbot
This is a discord bot that uses Pygmalion-6B and a KoboldAI url. The bot now supports json files and tavern cards and will change its name and image automatically.

# Official Discord Server
https://discord.gg/uvZtCRjYKr

# Blip Image detection added
![image](https://i.imgur.com/VPzquLol.png)


# Instructions: 
>1. Clone the repo.

>2. Change the variables in the sample.env file and save it as .env in the same folder

>3. Run the setup.bat file

>4. Run the run.bat file

>5. Choose the character

![Choose](https://i.imgur.com/qY6ZpB8.png)

Discord only allows bots to be renamed twice per hour.

[Get more Characters](https://booru.plus/+pygmalion)
# More Info: 

DISORD_BOT_TOKEN: You can get this from the discord developers portal. [Guide for setting that up](https://rentry.org/discordbotguide)

ENDPOINT: Set the endpoint variable with the KoboldAI url you get from this [google collab](https://colab.research.google.com/drive/1ZvYq4GmjfsyIkcTQcrBhSFXs8vQLLMAS). Or if you have a beefy gpu you can run kobold locally. https://github.com/KoboldAI/KoboldAI-Client

Look for this url in the google collab output:

![url example](https://raytracing-benchmarks.are-really.cool/5utGhMj.png)

# Slash Commands: 
Right now these commands are mostly helpful for developers. Use /sync to force the slash commands to show up if you don't see them.
| Command Name   | Slash Command    | More Info                                                                               |
| ---            | ---              | ---                                                                                     |
| Sync Commands  | `/sync`          | Needed to make the commands appear right away.                                         |
| Reload Cog     | `/reload <name>` | Lets you reload a specific cog instead of needing to restart everything.               |

