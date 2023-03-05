# Discord Tavern Style Pygmalion Chatbot
This is a discord bot that uses Pygmalion-6B and a KoboldAI url. The bot now supports json files and tavern cards and will change its name and image automatically. It current has groupchat, image detection, random messages, user relationship settings, and special image sending.

![Preview](https://i.imgur.com/XcIDQ3V.png)


# Instructions: 
>1. Clone the repo.

>2. Change the variables in the sample.env file and save it as .env in the same folder

>3. Run the bat file

>4. Choose the character

![Choose](https://i.imgur.com/qY6ZpB8.png)

>5. After running the bot, run the '/bothelp' command to see some details on what you can do with it.

Discord only allows bots to be renamed twice per hour.

[Get more Characters](https://booru.plus/+pygmalion)

Extra shit:

>Configure your own GIF JSON like this (located in /CharacterInfo):
name the file 'Character-Name_gif.JSON' (exampel: Aqua-Sama_gifs.json

{
    "blush": "https://tenor.com/view/aqua-gif-20916837",
    "turns red": "https://tenor.com/view/aqua-gif-20916837"
}
Which is 'keyword': 'gif.link' formatting.



# More Info: 

DISORD_BOT_TOKEN: You can get this from the discord developers portal. [Guide for setting that up](https://rentry.org/discordbotguide)

ENDPOINT: Set the endpoint variable with the KoboldAI url you get from this [google collab](https://colab.research.google.com/drive/1ZvYq4GmjfsyIkcTQcrBhSFXs8vQLLMAS).

Look for this url in the google collab output:

![url example](https://raytracing-benchmarks.are-really.cool/5utGhMj.png)


