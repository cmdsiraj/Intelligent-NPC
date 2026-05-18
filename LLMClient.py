import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os
import re
import json

class LLMMaxRetriesExceededError(Exception):
    """Exception raised when the LLM fails to provide a valid response after max retries."""
    def __init__(self, message, raw_response=None):
        super().__init__(message)
        self.raw_response = raw_response

class LLM:
    
    def __init__(self, max_retries=3, max_tokens=100, temperature=0.5):
        load_dotenv()
        self.MODEL_ARN = os.environ["AWS_MODEL_ARN"]
        
        self.client = boto3.client("bedrock-runtime")
        self.max_retries = max_retries
        self.max_tokens = max_tokens
        self.temperature = temperature
        
    def extract_json(self, response: str) -> dict[str, any] | None:
        
        if not response:
            return None
        
        pattern = r"```json\s*(.*?)\s*```"
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        
        if match:
            json_content = match.group(1).strip()
            try:
                return json.loads(json_content)
            except json.JSONDecodeError as e:
                raise e
        return None
    
    
    def run(self, message: str) -> dict[str, any]:
        messages = [
            {
                "role": "user",
                "content": [{"text": message}]
            }
        ]
        
        last_raw_text = None
        
        for retry in range(self.max_retries):
            try:
                response = self.client.converse(
                    modelId=self.MODEL_ARN,
                    messages=messages,
                    inferenceConfig={"maxTokens": self.max_tokens, "temperature":self.temperature}
                )
                
                response_text = response["output"]["message"]["content"][0]["text"]
                last_raw_text = response_text
                
                response_json = self.extract_json(response=response_text)
                
                if response_json is not None:
                    return response_json
                else:
                    raise json.JSONDecodeError("No ```json ``` block found in text output.", response_text, 0)
                
            except json.JSONDecodeError as e:
                messages.append({
                        "role": "assistant",
                        "content": [{"text": response_text}]
                    })
                messages.append({
                    "role": "user",
                    "content": [{"text": f"Your response was invalid. Return a valid JSON block. Error: {e}"}]
                })
            except ClientError as e:
                print(f"Error calling model: {e}")  
        
        raise LLMMaxRetriesExceededError(
            f"Failed to obtain a valid JSON response from Bedrock after {self.max_retries} attempts.",
            raw_response=last_raw_text
        )   
        