import requests
import json

# put the KoboldAI url you get from https://colab.research.google.com/drive/1ZvYq4GmjfsyIkcTQcrBhSFXs8vQLLMAS
endpoint = "https://bridges-uncle-cage-police.trycloudflare.com/"

# change to True if you want to enable the print statement to see the json data being sent to the api
debug = False

# Initialize the conversation history to the starting prompt. This is what Tavern uses to make the personality.
conversation_history = "Chat Bot's Persona: A chat bot. Very cool personality and likes to talk.\n" + \
                       '<START>\n' + \
                       "Chat Bot: Lets Chat. Whats new with you?\n"

print("\nStarting Chat. 'q' to quit\n")

# Starts main loop that you can break with 'q'
while True:
    print("Chat Bot: Lets Chat. Whats new with you?")
    try:
        user_input = input("You: ")
        if user_input != "q":
            # Add the user input to the conversation history
            conversation_history += f'You: {user_input}\n'
            # Define the prompt
            prompt = {
                "prompt": conversation_history + 'Chat Bot:',
                'use_story': False,
                'use_memory': False,
                'use_authors_note': False,
                'use_world_info': False,
                'max_context_length': 1818,
                'max_length': 50,
                'rep_pen': 1.03,
                'rep_pen_range': 1024,
                'rep_pen_slope': 0.9,
                'temperature': 0.98,
                'tfs': 0.9,
                'top_a': 0,
                'top_k': 0,
                'top_p': 0.9,
                'typical': 1,
                'sampler_order': [
                    6, 0, 1, 2,
                    3, 4, 5
                ]
            }
            if debug:
                print(json.dumps(prompt, indent=4))
            # Send a post request to the API endpoint
            response = requests.post(f"{endpoint}/api/v1/generate", json=prompt)
            # Check if the request was successful
            if response.status_code == 200:
                # Get the results from the response
                results = response.json()['results']
                # Print the results for debug

                for result in results:
                    if "\n" in result['text']:
                        response_text = result['text'].split("\n")[0]
                        print(f'Chat Bot:{response_text}')
                        conversation_history = conversation_history + 'Chat Bot:' + response_text + '\n'
            else:
                break
        else:
            print("\n\nChat Ended\n\n")
            break
    except requests.exceptions.ConnectionError:
            print("Error: there was a problem with the endpoint.")
            break
