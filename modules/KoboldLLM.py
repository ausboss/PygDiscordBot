from typing import Any, List, Mapping, Optional
import langchain
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory, ChatMessageHistory
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.llms.base import LLM
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    PromptTemplate,
)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
import requests




def kobold_api_call(url, prompt: str) -> str:
    url = "https://piece-gzip-basename-confidential.trycloudflare.com/api/v1/generate"
    data = {"prompt": prompt}
    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()["results"]

class KoboldLLM(LLM):
    
    @property
    def _llm_type(self) -> str:
        return "kobold"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> str:
        if stop is not None:
            raise ValueError("stop kwargs are not permitted.")
        
        # Call the Kobold API here and get the results
        results = kobold_api_call(prompt)

        # Get the first result
        result = results[0]["text"]
        
        # Split the result into lines
        bot_lines = result.split("\n")[0]
        # print(f"Kobold: {result} bot_lines: {bot_lines}")
        
        return bot_lines
    
    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {}



