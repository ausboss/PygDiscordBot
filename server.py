# quart server  that instantiates a Chatbot object from cogs/pygobot.py and allows the user to interact with it
# via a web interface
import quart
import asyncio
import langchain
# import wrapper
from langchain.llms import TextGen
from langchain.memory import ConversationBufferMemory
from langchain import PromptTemplate
from langchain.chains import (
    ConversationChain
)
from quart_cors import cors
# create instance with your endpoint
llm = TextGen(model_url="http://127.0.0.1:5000")

app = quart.Quart(__name__)
app = cors(app)
template = """You are a chatbot having a conversation with a human.

{history}
Human: {input}
Chatbot:"""

memory = ConversationBufferMemory(input_key="history")

prompt = PromptTemplate(
    input_variables=["history","input"], template=template
)
  # Create a conversation chain using the channel-specific memory
conversation = ConversationChain(
      prompt=prompt,
      llm=llm,
      verbose=True,
      memory=memory,
  )

@app.route('/chatbot', methods=['POST'])
async def chatbot():
    # get the message from the request
    print("got request")
    data = await quart.request.get_json()
    message = data['message']
    name, message_content = message.split(":", 1)
    print(f"{name}: {message_content}")
    response = conversation.predict(input=f"{message_content}", stop=[f"\n{name}:"])
    print(response)
    # return the response
    return quart.jsonify({"response": response})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5003, debug=True)