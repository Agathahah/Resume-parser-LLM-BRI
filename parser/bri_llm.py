import requests
from typing import List, Dict, Any, Optional
from aiohttp import ClientSession

class BRILargeLanguageModel:
    """
    A client class for interacting with the BRI Large Language Model (LLM) API, allowing both synchronous and asynchronous
    requests to generate responses from the model.

    Attributes:
        api_endpoint (str): The base URL of the BRI LLM API.
        api_key (str): An API key for authenticating requests to the BRI LLM API.
    """
    def __init__(
        self,
        api_endpoint: str,
        api_key: str
    ) -> None:
        """
        Initializes the LLMClient with the specified API URL.

        Args:
            api_endpoint (str): The base URL of the BRI LLM API.
            api_key (str): An API key for authenticating requests to the BRI LLM API.
        """
        self.api_endpoint = api_endpoint
        self.api_key = api_key
    

    def create_response(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        sampling_params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Sends a synchronous request to the LLM API to generate a response based on the provided messages,
        optional functions, and sampling parameters.

        Args:
            messages (List[Dict[str, str]]): A list of message dictionaries containing the conversation history.
            functions (Optional[List[Dict[str, Any]]], optional): A list of optional functions the LLM can call.
            sampling_params (Optional[Dict[str, Any]], optional): Optional parameters for response generation, such as temperature or max tokens.

        Returns:
            chat_completion (Optional[Dict[str, Any]]): The response from the LLM API if successful, otherwise raises an exception.

        Raises:
            Exception: If the API returns an error or the request fails.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": self.api_key
        }

        request_body = {
            "messages": messages,
            "functions": functions,
            "sampling_params": sampling_params,
        }

        response = requests.post(self.api_endpoint, json=request_body, headers=headers)
        response_json = response.json()
        chat_completion = response_json["data"]

        if response.status_code == 200:
            return chat_completion
        else:
            raise Exception(
                f"Error occurred when calling API ({self.api_endpoint}): {response_json['error_message']}"
            )
    

    async def a_create_response(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        sampling_params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Sends an asynchronous request to the LLM API to generate a response based on the provided messages,
        optional functions, and sampling parameters.

        Args:
            messages (List[Dict[str, str]]): A list of message dictionaries containing the conversation history.
            functions (Optional[List[Dict[str, Any]]], optional): A list of optional functions the LLM can call.
            sampling_params (Optional[Dict[str, Any]], optional): Optional parameters for response generation, such as temperature or max tokens.

        Returns:
            chat_completion (Optional[Dict[str, Any]]): The response from the LLM API if successful, otherwise raises an exception.

        Raises:
            Exception: If the API returns an error or the request fails.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": self.api_key
        }

        request_body = {
            "messages": messages,
            "functions": functions,
            "sampling_params": sampling_params,
        }
        
        async with ClientSession() as session:
            async with session.post(self.api_endpoint, json=request_body, headers=headers) as response:
                response_json = await response.json()
                chat_completion = response_json["data"]

                if response.status == 200:
                    return chat_completion
                else:
                    raise Exception(
                        f"Error occurred when calling API ({self.api_endpoint}): {response_json['error_message']}"
                    )