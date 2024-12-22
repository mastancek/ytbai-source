from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import openai
import cohere
from huggingface_hub import InferenceClient
import requests
import json

class AIProvider(ABC):
    @abstractmethod
    def generate_query(self, prompt: str) -> str:
        pass

    @abstractmethod
    def analyze_mood(self, text: str) -> List[str]:
        pass

    @abstractmethod
    def get_status(self) -> bool:
        pass

class OpenAIProvider(AIProvider):
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get('ai_services', {}).get('openai', {}).get('api_key')
        self.model = config.get('ai_services', {}).get('openai', {}).get('model', 'gpt-3.5-turbo')
        openai.api_key = self.api_key

    def generate_query(self, prompt: str) -> str:
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a music recommendation expert."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    def analyze_mood(self, text: str) -> List[str]:
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Analyze the mood and genre of this music description."},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content.split(',')

    def get_status(self) -> bool:
        return bool(self.api_key)

class CohereProvider(AIProvider):
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get('ai_services', {}).get('cohere', {}).get('api_key')
        self.client = cohere.Client(self.api_key) if self.api_key else None

    def generate_query(self, prompt: str) -> str:
        response = self.client.generate(
            prompt=f"Generate a music search query based on: {prompt}",
            max_tokens=50
        )
        return response.generations[0].text

    def analyze_mood(self, text: str) -> List[str]:
        response = self.client.generate(
            prompt=f"Analyze the mood and genre of: {text}",
            max_tokens=50
        )
        return response.generations[0].text.split(',')

    def get_status(self) -> bool:
        return bool(self.client)

class OllamaProvider(AIProvider):
    def __init__(self, config: Dict[str, Any]):
        self.host = config.get('ai_services', {}).get('ollama', {}).get('host', 'http://localhost:11434')
        self.model = config.get('ai_services', {}).get('ollama', {}).get('model', 'llama2')

    def _query_ollama(self, prompt: str) -> str:
        response = requests.post(
            f"{self.host}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt
            }
        )
        return response.json()['response']

    def generate_query(self, prompt: str) -> str:
        return self._query_ollama(f"Generate a music search query based on: {prompt}")

    def analyze_mood(self, text: str) -> List[str]:
        response = self._query_ollama(f"Analyze the mood and genre of: {text}")
        return response.split(',')

    def get_status(self) -> bool:
        try:
            requests.get(f"{self.host}/api/version")
            return True
        except:
            return False

class HuggingFaceProvider(AIProvider):
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get('ai_services', {}).get('huggingface', {}).get('api_key')
        self.client = InferenceClient(token=self.api_key) if self.api_key else None
        self.model = config.get('ai_services', {}).get('huggingface', {}).get('model', 'gpt2')

    def generate_query(self, prompt: str) -> str:
        response = self.client.text_generation(
            prompt,
            model=self.model,
            max_new_tokens=50
        )
        return response[0]['generated_text']

    def analyze_mood(self, text: str) -> List[str]:
        response = self.client.text_generation(
            f"Analyze the mood and genre of: {text}",
            model=self.model,
            max_new_tokens=50
        )
        return response[0]['generated_text'].split(',')

    def get_status(self) -> bool:
        return bool(self.client) 