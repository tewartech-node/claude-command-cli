"""
Free AI Connectors: Access to free-tier AI providers
Enables The Brain to run on zero cost with multiple fallback providers
"""

import httpx
import json
import os
from typing import Optional


class FreeAIConnectors:
    """Multi-provider free AI access"""

    def __init__(self):
        self.providers = {
            "ollama": self._ollama_available(),
            "groq": bool(os.getenv("GROQ_API_KEY")),
            "together": bool(os.getenv("TOGETHER_API_KEY")),
            "huggingface": bool(os.getenv("HF_API_KEY")),
            "local": True  # Fallback to local execution
        }

    @staticmethod
    def _ollama_available() -> bool:
        """Check if Ollama is running locally"""
        try:
            with httpx.Client(timeout=2.0) as client:
                response = client.get("http://localhost:11434/api/tags")
                return response.status_code == 200
        except:
            return False

    async def query_ollama(self, prompt: str, model: str = "mistral") -> Optional[str]:
        """
        Query Ollama (100% free, fully local)
        Requires: ollama installed locally
        Models: mistral, llama2, neural-chat (all free)
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=30.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "")
        except Exception as e:
            print(f"Ollama error: {e}")
        return None

    async def query_groq(self, prompt: str, model: str = "mixtral-8x7b-32768") -> Optional[str]:
        """
        Query Groq (Free tier: 30 req/min)
        Get free API key: https://console.groq.com
        Models: mixtral-8x7b-32768, llama2-70b-4096
        """
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 500
                    },
                    timeout=15.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Groq error: {e}")
        return None

    async def query_together(self, prompt: str, model: str = "mistralai/Mistral-7B-Instruct-v0.1") -> Optional[str]:
        """
        Query Together AI (Free tier: available)
        Get free API key: https://www.together.ai
        Models: mistral-7b, llama-2-7b, many others
        """
        api_key = os.getenv("TOGETHER_API_KEY")
        if not api_key:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.together.xyz/inference",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model,
                        "prompt": prompt,
                        "max_tokens": 500,
                        "temperature": 0.7
                    },
                    timeout=15.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return data["output"]["choices"][0]["text"]
        except Exception as e:
            print(f"Together error: {e}")
        return None

    async def query_huggingface(self, prompt: str, model: str = "gpt2") -> Optional[str]:
        """
        Query HuggingFace (Free tier: limited rate)
        Get free API key: https://huggingface.co/settings/tokens
        Models: gpt2, distilbert-base-uncased, many others
        """
        api_key = os.getenv("HF_API_KEY")
        if not api_key:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api-inference.huggingface.co/models/{model}",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"inputs": prompt},
                    timeout=15.0
                )
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        return data[0].get("generated_text", "")
        except Exception as e:
            print(f"HuggingFace error: {e}")
        return None

    async def query_best_available(self, prompt: str) -> Optional[str]:
        """
        Try providers in order of preference (free tier capable)
        Fallback chain ensures The Brain always has an answer
        """
        # 1. Try local Ollama (infinite free, no API key needed)
        if self.providers["ollama"]:
            result = await self.query_ollama(prompt)
            if result:
                return result

        # 2. Try Groq (fast, free tier)
        if self.providers["groq"]:
            result = await self.query_groq(prompt)
            if result:
                return result

        # 3. Try Together AI (free tier)
        if self.providers["together"]:
            result = await self.query_together(prompt)
            if result:
                return result

        # 4. Try HuggingFace (free but limited)
        if self.providers["huggingface"]:
            result = await self.query_huggingface(prompt)
            if result:
                return result

        # 5. Fallback
        return "Cannot process request - no AI provider available"

    def get_status(self) -> dict:
        """Get available free provider status"""
        return {
            "ollama_available": self.providers["ollama"],
            "groq_available": self.providers["groq"],
            "together_available": self.providers["together"],
            "huggingface_available": self.providers["huggingface"],
            "providers_enabled": sum(self.providers.values()),
            "recommendation": self._get_recommendation()
        }

    def _get_recommendation(self) -> str:
        """Recommend best free setup"""
        if self.providers["ollama"]:
            return "Ollama (local, unlimited free)"
        elif self.providers["groq"]:
            return "Groq (30 req/min free)"
        elif self.providers["together"]:
            return "Together AI (free tier)"
        else:
            return "Install Ollama for unlimited free AI: https://ollama.ai"
