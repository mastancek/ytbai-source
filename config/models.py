from dataclasses import dataclass
from typing import Dict, List, Optional
import requests
import cohere
from openai import OpenAI
import os

@dataclass
class AIModel:
    """Informace o AI modelu"""
    id: str
    name: str
    provider: str
    max_tokens: int
    price_per_1k_tokens: float
    supports_streaming: bool
    description: str
    endpoint: str = ""

class AIModelManager:
    """Správce AI modelů a jejich konfigurace"""
    
    def __init__(self):
        self.models: Dict[str, AIModel] = {}
        self._load_models()
    
    def _load_models(self):
        """Načte dostupné modely od všech poskytovatelů"""
        self._load_openai_models()
        self._load_cohere_models()
        self._load_perplexity_models()
        self._load_replicate_models()
        self._load_huggingface_models()
    
    def _load_openai_models(self):
        """Načte dostupné OpenAI modely"""
        try:
            if os.getenv('OPENAI_API_KEY'):
                client = OpenAI()
                models = client.models.list()
                for model in models.data:
                    if any(name in model.id for name in ['gpt-3.5', 'gpt-4']):
                        self.models[model.id] = AIModel(
                            id=model.id,
                            name=model.id,
                            provider="OpenAI",
                            max_tokens=4096 if 'gpt-3.5' in model.id else 8192,
                            price_per_1k_tokens=0.002 if 'gpt-3.5' in model.id else 0.06,
                            supports_streaming=True,
                            description="GPT model pro generování textu"
                        )
        except Exception as e:
            print(f"Chyba při načítání OpenAI modelů: {e}")
    
    def _load_cohere_models(self):
        """Načte dostupné Cohere modely"""
        try:
            if os.getenv('COHERE_API_KEY'):
                client = cohere.Client(os.getenv('COHERE_API_KEY'))
                models = {
                    'command': AIModel(
                        id='command',
                        name='Command',
                        provider="Cohere",
                        max_tokens=4096,
                        price_per_1k_tokens=0.002,
                        supports_streaming=True,
                        description="Výkonný model pro generování textu"
                    ),
                    'command-light': AIModel(
                        id='command-light',
                        name='Command Light',
                        provider="Cohere",
                        max_tokens=4096,
                        price_per_1k_tokens=0.001,
                        supports_streaming=True,
                        description="Lehčí verze Command modelu"
                    )
                }
                self.models.update(models)
        except Exception as e:
            print(f"Chyba při načítání Cohere modelů: {e}")
    
    def _load_perplexity_models(self):
        """Načte dostupné Perplexity modely"""
        models = {
            'mixtral-8x7b-instruct': AIModel(
                id='mixtral-8x7b-instruct',
                name='Mixtral 8x7B Instruct',
                provider="Perplexity",
                max_tokens=4096,
                price_per_1k_tokens=0.0007,
                supports_streaming=True,
                description="Open source model optimalizovaný pro instrukce"
            ),
            'codellama-34b-instruct': AIModel(
                id='codellama-34b-instruct',
                name='CodeLlama 34B Instruct',
                provider="Perplexity",
                max_tokens=4096,
                price_per_1k_tokens=0.0007,
                supports_streaming=True,
                description="Model specializovaný na kód"
            )
        }
        self.models.update(models)
    
    def _load_replicate_models(self):
        """Načte dostupné Replicate modely"""
        try:
            if os.getenv('REPLICATE_API_TOKEN'):
                # Replicate API nemá endpoint pro výpis modelů
                # Přidáme ručně známé modely
                models = {
                    'llama-2-70b-chat': AIModel(
                        id='llama-2-70b-chat',
                        name='Llama 2 70B Chat',
                        provider="Replicate",
                        max_tokens=4096,
                        price_per_1k_tokens=0.0007,
                        supports_streaming=True,
                        description="Největší veřejně dostupný chatovací model"
                    )
                }
                self.models.update(models)
        except Exception as e:
            print(f"Chyba při načítání Replicate modelů: {e}")
    
    def _load_huggingface_models(self):
        """Načte dostupné Hugging Face modely"""
        try:
            if os.getenv('HUGGINGFACE_API_KEY'):
                # Můžeme použít HF API pro získání modelů
                headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY')}"}
                response = requests.get(
                    "https://huggingface.co/api/models",
                    headers=headers,
                    params={"filter": "text-generation", "sort": "downloads", "limit": 5}
                )
                if response.status_code == 200:
                    for model in response.json():
                        self.models[model['id']] = AIModel(
                            id=model['id'],
                            name=model['id'],
                            provider="Hugging Face",
                            max_tokens=2048,  # Defaultní hodnota
                            price_per_1k_tokens=0.0,  # HF Inference API je zdarma
                            supports_streaming=False,
                            description=model.get('description', '')
                        )
        except Exception as e:
            print(f"Chyba při načítání Hugging Face modelů: {e}")
    
    def get_available_models(self, provider: Optional[str] = None) -> List[AIModel]:
        """Vrátí seznam dostupných modelů"""
        if provider:
            return [m for m in self.models.values() if m.provider.lower() == provider.lower()]
        return list(self.models.values())
    
    def get_model(self, model_id: str) -> Optional[AIModel]:
        """Vrátí informace o konkrétním modelu"""
        return self.models.get(model_id) 