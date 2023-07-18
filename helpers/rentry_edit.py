import http.cookiejar
import sys
import urllib.parse
import urllib.request
from http.cookies import SimpleCookie
from json import loads as json_loads
import csv
from bs4 import BeautifulSoup

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



def new(url, edit_code, text):
    client, cookie = UrllibClient(), SimpleCookie()

    cookie.load(vars(client.get('https://rentry.co'))['headers']['Set-Cookie'])
    csrftoken = cookie['csrftoken'].value

    payload = {
        'csrfmiddlewaretoken': csrftoken,
        'url': url,
        'edit_code': edit_code,
        'text': text
    }

    return json_loads(client.post('https://rentry.co/api/new', payload, headers=_headers).data)




def get_rentry_link(text):
    url, edit_code = '', ''
    response = new(url, edit_code, text)
    if response['status'] != '200':
        print('error: {}'.format(response['content']))
        try:
            for i in response['errors'].split('.'):
                i and print(i)
            sys.exit(1)
        except:
            sys.exit(1)
    else:
        pastebin_link = response['url']
        print('Url:        {}\nEdit code:  {}'.format(response['url'], response['edit_code']))

        # write the url and edit code to a csv file
        with open('notebook_links.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([response['url'], response['edit_code']])

        return pastebin_link

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



class AiohttpClient:
    """Simple HTTP Session Client, keeps cookies."""

    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def get(self, url, headers={}):
        async with self.session.get(url, headers=headers) as response:
            response.status_code = response.status
            response.data = await response.text()
            return response

    async def post(self, url, data=None, headers={}):
        async with self.session.post(url, data=data, headers=headers) as response:
            response.status_code = response.status
            response.data = await response.text()
            return response

    async def close(self):
        await self.session.close()


async def new(url, edit_code, text):
    client = AiohttpClient()

    response = await client.get('https://rentry.co')
    csrftoken = response.headers.get('Set-Cookie', '').split(';')[0].split('=')[1]

    payload = {
        'csrfmiddlewaretoken': csrftoken,
        'url': url,
        'edit_code': edit_code,
        'text': text
    }

    result = await client.post('https://rentry.co/api/new', payload, headers=_headers)
    await client.close()
    return json_loads(result.data)


async def get_rentry_link(text):
    url, edit_code = '', ''
    response = await new(url, edit_code, text)
    if response['status'] != '200':
        print('error: {}'.format(response['content']))
        try:
            for i in response['errors'].split('.'):
                i and print(i)
            sys.exit(1)
        except:
            sys.exit(1)
    else:
        pastebin_link = response['url']
        print('Url:        {}\nEdit code:  {}'.format(response['url'], response['edit_code']))

        # write the url and edit code to a csv file
        with open('notebook_links.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([response['url'], response['edit_code']])

        return pastebin_link


async def edit(url, edit_code, text):
    client, cookie = AiohttpClient(), SimpleCookie()

    cookie.load(vars(await client.get('https://rentry.co'))['headers']['Set-Cookie'])
    csrftoken = cookie['csrftoken'].value

    payload = {
        'csrfmiddlewaretoken': csrftoken,
        'edit_code': edit_code,
        'text': text
    }

    return json_loads(await client.post('https://rentry.co/api/edit/{}'.format(url), payload, headers=_headers).data)



async def append(url, edit_code, text):
    client, cookie = AiohttpClient(), SimpleCookie()

    cookie.load(vars(await client.get('https://rentry.co'))['headers']['Set-Cookie'])
    csrftoken = cookie['csrftoken'].value

    # Retrieve existing text
    response = await client.get('https://rentry.co/' + url + '/raw')
    existing_text = response.data

    # Concatenate existing text with new text
    updated_text = existing_text + '\n' + text

    payload = {
        'csrfmiddlewaretoken': csrftoken,
        'edit_code': edit_code,
        'text': updated_text
    }

    return json_loads(await client.post('https://rentry.co/api/edit/{}'.format(url), payload, headers=_headers).data)


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


async def view(url):
    client = AiohttpClient()
    response = (await client.get(url + '/raw')).data
    soup = BeautifulSoup(response, 'html.parser')
    # print(soup.prettify())
    contents = soup.get_text()
    return contents

async def main():
    client = AiohttpClient()  # Create an instance of AiohttpClient

    while True:
        user_input = input('''1. new\n2. existing\nq. quit\nDo you want to create a new notebook or edit an existing one? ''')

        if user_input.lower() == '1':
            text_input = input('Enter the text to add to the notebook: ')
            await get_rentry_link(text_input)

        elif user_input.lower() == '2':
            entries = read_csv()
            for i, entry in enumerate(entries, start=1):
                print(f'{i}. Url: {entry[0]}, Edit Code: {entry[1]}')
            
            entry_num = int(input('Select the entry number to edit: ')) - 1
            url, edit_code = entries[entry_num]

            action = input('Do you want to view or append to the notebook? (view/append): ')
            if action.lower() == 'view':
                view(url)
            elif action.lower() == 'append':
                url = url.split('https://rentry.co/')[1]
                new_text = input('Enter the text to append: ')
                response = append(url, edit_code, new_text + '\n')
                if response['status'] != '200':
                    print('edit error: {}'.format(response['content']))
                else:
                    print('Notebook edited successfully.')
            
        elif user_input.lower() == 'q':
            break

    await client.close()  # Close the AiohttpClient session

if __name__ == '__main__':
    asyncio.run(main())  # Run the async function using asyncio.run()