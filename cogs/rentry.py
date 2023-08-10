import discord
from discord.ext import commands
from discord import app_commands

import csv

import http.cookiejar
import sys
import urllib.parse
import asyncio
import urllib.request
from http.cookies import SimpleCookie
from json import loads as json_loads
import csv
from bs4 import BeautifulSoup
import aiohttp

_headers = {"Referer": 'https://rentry.co'}


class UrllibClient:
    """Simple HTTP Session Client, keeps cookies."""

    def __init__(self):
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))
        urllib.request.install_opener(self.opener)

    def get(self, url, headers={}):
        request = urllib.request.Request(url, headers=headers)
        return self._request(request)

    def post(self, url, data=None, headers={}):
        postdata = urllib.parse.urlencode(data).encode()
        request = urllib.request.Request(url, postdata, headers)
        return self._request(request)

    def _request(self, request):
        response = self.opener.open(request)
        response.status_code = response.getcode()
        response.data = response.read().decode('utf-8')
        return response  # Return the response object directly


def edit(url, edit_code, text):
    client, cookie = UrllibClient(), SimpleCookie()

    cookie.load(vars(client.get('https://rentry.co'))['headers']['Set-Cookie'])
    csrftoken = cookie['csrftoken'].value

    payload = {
        'csrfmiddlewaretoken': csrftoken,
        'edit_code': edit_code,
        'text': text
    }

    return json_loads(client.post('https://rentry.co/api/edit/{}'.format(url), payload, headers=_headers).data)


def append(url, edit_code, text):
    client, cookie = UrllibClient(), SimpleCookie()

    cookie.load(vars(client.get('https://rentry.co'))['headers']['Set-Cookie'])
    csrftoken = cookie['csrftoken'].value

    # Retrieve existing text
    response = client.get('https://rentry.co/' + url + '/raw')
    existing_text = response.data

    # Concatenate existing text with new text
    updated_text = existing_text + '\n' + text

    payload = {
        'csrfmiddlewaretoken': csrftoken,
        'edit_code': edit_code,
        'text': updated_text
    }

    return json_loads(client.post('https://rentry.co/api/edit/{}'.format(url), payload, headers=_headers).data)


def read_csv():
    # if FileNotFoundError make the file with url, edit_code at the top
    try:
        with open('notebook_links.csv', 'r') as file:
            reader = csv.reader(file)
            next(reader)  # skip header row
            entries = list(reader)
    except FileNotFoundError:
        with open('notebook_links.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['url', 'edit_code'])
        entries = []
    
    return entries


def view(url):
    client = UrllibClient()
    response = client.get(url + '/raw').data
    soup = BeautifulSoup(response, 'html.parser')
    # print(soup.prettify())
    contents = soup.get_text()
    return contents


class RentryCog(commands.Cog, name="rentry_cog"):

    def __init__(self, bot):
        self.bot = bot
        self.rentry_links = read_csv()
        # create a temp dictionary to store the rentry url as the key and the value is a list of the edit_code and the contents of the rentry
        self.rentry_dict = {}
        for item in self.rentry_links:
            print(item)

    def cog_unload(self):  # Add this method to close the AiohttpClient session
        asyncio.create_task(self.client.close())

    # this function takes a rentry url, edit_code, and text and adds them to the self.rentry_dict. the rentry url as the key and the value is a list of the edit_code and the contents of the rentry
    async def add_rentry_dict(self, url, edit_code, text):
        if url not in self.rentry_dict:
            self.rentry_dict[url] = [edit_code, text]
        else:
            self.rentry_dict[url][1] = text
            self.rentry_dict[url][0] = edit_code
        return self.rentry_dict

    # this function takes a rentry url and gets the edit code 
    async def get_edit_code(self, url):
        full_url = f"https://rentry.co/{url}"
        with open('notebook_links.csv', 'r') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                if row[0] == full_url:
                    edit_code = row[1]
                    break
        return edit_code
    
    # Create a select menu for the rentry links
    class RentrySelect(discord.ui.Select):

        def __init__(self, parent, bot):
            self.parent = parent
            self.RentryCog = RentryCog(self.parent.bot)  # Add this line
            self.bot = bot  # Add this line

            options = [
                discord.SelectOption(label=f"url: {rentry[0].split('https://rentry.co/')[1]}", description=f"{rentry[2]}") 
                for rentry in self.parent.rentry_links
            ]
            super().__init__(
                placeholder="Select a rentry",
                options=options
            )
        
        async def callback(self, interaction: discord.Interaction):
            url_part = self.values[0].split(' ')[1]
            full_url = f"https://rentry.co/{url_part}"

            contents = view(full_url)
            message = contents
            edit_code = await self.RentryCog.get_edit_code(url_part)
            rentry_dict = await self.RentryCog.add_rentry_dict(url_part, edit_code, message)

            contents_txt = rentry_dict[url_part][1]
            await interaction.response.send_message(
                f'```Rentry: {url_part}\n\n{str(contents_txt)}```',
                ephemeral=False
            )
            # await channel.send(f"Rentry: https://rentry.co/{url_part}\n```{view(full_url)}```")

    # Create a view for the rentry links
    class RentryView(discord.ui.View):

        def __init__(self, parent):
            self.parent = parent
            super().__init__()
           
            self.add_item(RentryCog.RentrySelect(parent, parent.bot))  # Pass the bot object here

    # shows a menu of rentry links and then displays the selected rentry contents
    @app_commands.command(name="viewrentry", description="View a rentry")
    async def view_rentry(self, interaction: discord.Interaction):
        view = self.RentryView(self)  
        await interaction.response.send_message(
        'Select a rentry',
        view=view)

    # takes the ending url of a rentry and a string then appends the string to the rentry
    @app_commands.command(name="appendrentry", description="append to a rentry")
    async def append_rentry(self, interaction: discord.Interaction, url: str, string: str):
        await interaction.response.defer()
        name = interaction.user.display_name
        full_url = f"https://rentry.co/{url}"
        contents = view(full_url)
        message = contents
        edit_code = await self.get_edit_code(url)
        rentry_dict = await self.add_rentry_dict(url, edit_code, message)
        await interaction.followup.send(f'{name} used `Append Rentry`\n```Rentry: {url}\n\n{rentry_dict[url][1]}\n{string}```')
        append(url, edit_code, string)
        channel_id = self.bot.get_channel(interaction.channel_id)
        # fake_system_message = f"{name} asked you to add `{string}` to rentry: {url}\nResult: Success\n```Rentry: {url}\n\n{rentry_dict[url][1]}\n{string}```"
        fake_system_message = f"{name} asked you to add `{string}` to rentry: {url} - Result: Successfully appended to rentry"

        followup = await self.bot.get_cog("chatbot").chat_command("System", str(interaction.channel_id), fake_system_message)
        await channel_id.send(followup)

    @app_commands.command(name="createrentry", description="create a rentry")
    async def create_rentry(self, interaction: discord.Interaction, to_add: str, description: str):
        await interaction.response.defer()
        name = interaction.user.display_name

        # Initialize an UrllibClient and a SimpleCookie
        client, cookie = UrllibClient(), SimpleCookie()
        # Load the cookies from the client session
        cookie.load(vars(client.get('https://rentry.co'))['headers']['Set-Cookie'])
        csrftoken = cookie['csrftoken'].value

        # Create a payload with the CSRF token and the text
        payload = {
            'csrfmiddlewaretoken': csrftoken,
            'text': to_add
        }

        # Post the request to create a new rentry
        response = client.post('https://rentry.co/api/new', payload, headers=_headers)

        # Extract url and edit_code from the response data
        response_data = json_loads(response.data)
        url = response_data['url']
        edit_code = response_data['edit_code']

        # Save the new rentry link and edit_code to the csv file
        with open('notebook_links.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([url, edit_code, description])

        # Send a follow-up message to the user
        await interaction.followup.send(f'{name} created a new Rentry: {url} with contents:\n```{to_add}```')

        # Send a follow-up message to the chatbot
        channel_id = self.bot.get_channel(interaction.channel_id)
        fake_system_message = f"{name} created a new rentry: {url} with contents: `{to_add}` - Result: Successfully created rentry {description}"
        followup = await self.bot.get_cog("chatbot").chat_command("System", str(interaction.channel_id), fake_system_message)
        await channel_id.send(followup)


async def setup(bot):
    await bot.add_cog(RentryCog(bot))
