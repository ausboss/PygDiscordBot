# Discord Tavern Style Pygmalion Chatbot
This is a discord bot that uses Pygmalion-6B and a KoboldAI url. The bot now supports json files and tavern cards and will change its name and image automatically. I plan on adding more features like group chat support, random messages, and the ability to comment on images you share.

![Preview](https://i.imgur.com/XcIDQ3V.png)


# Instructions: 
>1. Clone the repo.

>2. Change the variables in the sample.env file and save it as .env in the same folder

>3. Run the bat file

>4. Choose the character

>5. Choose the settings

![Choose](https://i.imgur.com/qY6ZpB8.png)

Discord only allows bots to be renamed twice per hour.

[Get more Characters](https://booru.plus/+pygmalion)
# More Info: 

DISORD_BOT_TOKEN: You can get this from the discord developers portal. [Guide for setting that up](https://rentry.org/discordbotguide)

ENDPOINT: Set the endpoint variable with the KoboldAI url you get from this [google collab](https://colab.research.google.com/drive/1ZvYq4GmjfsyIkcTQcrBhSFXs8vQLLMAS).

Look for this url in the google collab output:
![url example](https://raytracing-benchmarks.are-really.cool/5utGhMj.png)

SAVE_CHATS: Saves the conversations to a plain text file. To be used to collect data from user conversations. Softprompts, Data for a dataset, etc.

SEND_GREETING: Sends the character's greeting. Which is basically just the beginning text in a roleplay scenario.
