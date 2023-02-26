# Cog Branch

## New Features
> Text Logs

> Tenor Gif to Text

> Better cog support

> Faster Boot Options

> Lauch Arguments

This branch tests out image detection and the usage of cogs for easily adding in your own commands
There is two versions of on_message handlers that do the same thing but to keep things simple I have commented out the one with more complex logic. The point of the bigger version is so that the bot responds more like a real person rather than a bot that responds to every single message.

# Blip Image detection added
![image](https://i.imgur.com/VPzquLol.png)

# Discord Tavern Style Pygmalion Chatbot
This is a discord bot that uses Pygmalion-6B and a KoboldAI url. The bot now supports json files and tavern cards and will change its name and image automatically. I plan on adding more features like group chat support, random messages, and the ability to comment on images you share.

![Preview](https://i.imgur.com/XcIDQ3V.png)


# Instructions: 
>1. Clone the repo.

>2. Change the variables in the sample.env file and save it as .env in the same folder

>3. Run the bat file

>4. Choose the character

![Choose](https://i.imgur.com/qY6ZpB8.png)

Discord only allows bots to be renamed twice per hour.

[Get more Characters](https://booru.plus/+pygmalion)
# More Info: 

DISORD_BOT_TOKEN: You can get this from the discord developers portal. [Guide for setting that up](https://rentry.org/discordbotguide)

ENDPOINT: Set the endpoint variable with the KoboldAI url you get from this [google collab](https://colab.research.google.com/drive/1ZvYq4GmjfsyIkcTQcrBhSFXs8vQLLMAS).

Look for this url in the google collab output:

![url example](https://raytracing-benchmarks.are-really.cool/5utGhMj.png)


