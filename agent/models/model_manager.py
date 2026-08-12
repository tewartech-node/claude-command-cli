"""
Model Manager: Download and manage LLM models for all providers
Provides easy access to model catalogs and download management
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict


class ModelManager:
    """Manage LLM models across all providers"""

    def __init__(self, models_dir: str = "./agent/models"):
        self.models_dir = Path(models_dir)
        self.catalog_path = self.models_dir / "model_catalog.json"
        self.cache_dir = self.models_dir / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.catalog = self._load_catalog()

    def _load_catalog(self) -> dict:
        """Load model catalog from JSON"""
        try:
            with open(self.catalog_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading catalog: {e}")
            return {}

    def get_provider_models(self, provider: str) -> List[dict]:
        """Get all models for a provider"""
        if provider not in self.catalog:
            return []
        return self.catalog[provider].get("models", [])

    def get_recommended_model(self, provider: str) -> Optional[dict]:
        """Get recommended model for provider"""
        models = self.get_provider_models(provider)
        for model in models:
            if model.get("recommended"):
                return model
        return models[0] if models else None

    def download_ollama_models(self, models: List[str] = None) -> bool:
        """Download Ollama models"""
        if models is None:
            # Get recommended model
            rec = self.get_recommended_model("ollama")
            models = [rec["id"]] if rec else []

        print(f"📥 Downloading Ollama models: {models}")

        for model in models:
            print(f"\n  Pulling {model}...")
            try:
                result = subprocess.run(
                    ["ollama", "pull", model],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                if result.returncode == 0:
                    print(f"  ✅ {model} downloaded")
                else:
                    print(f"  ❌ Failed to download {model}")
                    print(f"  Error: {result.stderr}")
                    return False
            except FileNotFoundError:
                print("  ❌ Ollama not installed. Install from https://ollama.ai")
                return False
            except subprocess.TimeoutExpired:
                print(f"  ⏱️  {model} download timeout (>10min)")
                return False
            except Exception as e:
                print(f"  ❌ Error: {e}")
                return False

        return True

    def list_ollama_models(self) -> List[dict]:
        """List installed Ollama models"""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                models = []
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 1:
                            models.append({
                                "name": parts[0],
                                "installed": True
                            })
                return models
        except Exception as e:
            print(f"Error listing models: {e}")
        return []

    def setup_ollama(self) -> bool:
        """Complete Ollama setup"""
        print("🚀 Setting up Ollama...")

        # Check if installed
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                raise FileNotFoundError
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("❌ Ollama not installed")
            print("📥 Download from https://ollama.ai")
            return False

        print("✅ Ollama installed")

        # Download recommended model
        rec = self.get_recommended_model("ollama")
        if rec:
            print(f"\n📥 Downloading recommended model: {rec['name']}")
            return self.download_ollama_models([rec["id"]])

        return True

    def get_setup_commands(self, provider: str) -> dict:
        """Get setup commands for provider"""
        if provider == "ollama":
            return {
                "install": "Download from https://ollama.ai",
                "start": "ollama serve",
                "download": "ollama pull mistral",
                "test": "ollama run mistral 'Hello, how are you?'"
            }
        elif provider == "groq":
            return {
                "api_key": "Get free key from https://console.groq.com",
                "env_setup": 'export GROQ_API_KEY="gsk_..."',
                "test": "python -c \"from agent.executor.free_connectors import FreeAIConnectors; print('Groq available')\"",
                "info": "Free tier: 30 requests/minute"
            }
        elif provider == "together":
            return {
                "api_key": "Get free key from https://www.together.ai",
                "env_setup": 'export TOGETHER_API_KEY="..."',
                "test": "python -c \"from agent.executor.free_connectors import FreeAIConnectors; print('Together available')\"",
                "info": "Free tier available"
            }
        elif provider == "huggingface":
            return {
                "api_key": "Get free token from https://huggingface.co/settings/tokens",
                "env_setup": 'export HF_API_KEY="hf_..."',
                "test": "python -c \"from agent.executor.free_connectors import FreeAIConnectors; print('HuggingFace available')\"",
                "info": "Free tier with rate limits"
            }
        return {}

    def print_catalog(self):
        """Print formatted catalog"""
        print("\n📚 Available LLM Models\n")

        for provider, info in self.catalog.items():
            print(f"{'='*60}")
            print(f"🔧 {provider.upper()}")
            print(f"{'='*60}")
            print(f"{info['description']}")

            if "install_url" in info:
                print(f"Install: {info['install_url']}")

            if info.get("api_key_required"):
                print(f"API Key: Required (free from {info['api_url']})")

            print(f"\nModels:")
            for model in info.get("models", []):
                marker = "⭐" if model.get("recommended") else "  "
                print(f"  {marker} {model['id']}")
                print(f"     {model['description']}")
                print(f"     Speed: {model['speed']} | Quality: {model['quality']}")
                if "size" in model:
                    print(f"     Size: {model['size']}")
            print()

    def get_model_info(self, provider: str, model_id: str) -> Optional[dict]:
        """Get detailed info about a model"""
        models = self.get_provider_models(provider)
        for model in models:
            if model["id"] == model_id:
                return model
        return None

    def get_provider_status(self) -> dict:
        """Check which providers are ready to use"""
        status = {}

        # Ollama
        try:
            subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                timeout=2
            )
            status["ollama"] = {
                "installed": True,
                "models": self.list_ollama_models(),
                "setup": "Run 'ollama serve' then download models"
            }
        except:
            status["ollama"] = {
                "installed": False,
                "models": [],
                "setup": "Download from https://ollama.ai"
            }

        # Cloud providers (check env vars)
        status["groq"] = {
            "configured": bool(os.getenv("GROQ_API_KEY")),
            "setup": "Set GROQ_API_KEY environment variable"
        }

        status["together"] = {
            "configured": bool(os.getenv("TOGETHER_API_KEY")),
            "setup": "Set TOGETHER_API_KEY environment variable"
        }

        status["huggingface"] = {
            "configured": bool(os.getenv("HF_API_KEY")),
            "setup": "Set HF_API_KEY environment variable"
        }

        return status

    def print_status(self):
        """Print provider status"""
        print("\n📊 Provider Status\n")

        status = self.get_provider_status()

        for provider, info in status.items():
            if provider == "ollama":
                installed = "✅" if info["installed"] else "❌"
                print(f"{installed} Ollama: {info['setup']}")
                if info["models"]:
                    print(f"   Installed models: {', '.join([m['name'] for m in info['models']])}")
            else:
                configured = "✅" if info["configured"] else "⏳"
                print(f"{configured} {provider.upper()}: {info['setup']}")

        print()
