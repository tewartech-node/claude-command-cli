#!/usr/bin/env python3
"""
Models CLI - Quick access to model management
"""

import sys
import json
from agent.models import ModelManager


def print_help():
    """Print help message"""
    print("""
Usage: python models_cli.py [command]

Commands:
  status      Show which providers are ready
  catalog     List all available models
  info        Show model details
  download    Download models for a provider
  setup       Run interactive setup wizard
  list        List installed models

Examples:
  python models_cli.py status
  python models_cli.py catalog
  python models_cli.py info ollama mistral
  python models_cli.py download ollama mistral
    """)


def cmd_status():
    """Show provider status"""
    mm = ModelManager()
    mm.print_status()


def cmd_catalog():
    """Show full catalog"""
    mm = ModelManager()
    mm.print_catalog()


def cmd_info(args):
    """Show model info"""
    if len(args) < 2:
        print("Usage: python models_cli.py info <provider> <model_id>")
        print("Example: python models_cli.py info ollama mistral")
        return

    provider = args[0]
    model_id = args[1]

    mm = ModelManager()
    model = mm.get_model_info(provider, model_id)

    if model:
        print(f"\n📦 {model['name']}")
        print("="*60)
        for key, value in model.items():
            if key != "id" and key != "name":
                print(f"{key.title()}: {value}")
    else:
        print(f"Model not found: {provider}/{model_id}")


def cmd_download(args):
    """Download models"""
    if len(args) < 2:
        print("Usage: python models_cli.py download <provider> <model_id>")
        print("Example: python models_cli.py download ollama mistral")
        return

    provider = args[0]
    model_id = args[1]

    mm = ModelManager()

    if provider == "ollama":
        print(f"\n📥 Downloading {model_id}...")
        if mm.download_ollama_models([model_id]):
            print(f"✅ {model_id} downloaded!")
        else:
            print(f"❌ Download failed")
    else:
        print(f"Auto-download only supported for Ollama")
        print(f"For {provider}, see: python models_cli.py info {provider} {model_id}")


def cmd_list():
    """List installed models"""
    mm = ModelManager()
    models = mm.list_ollama_models()

    if models:
        print("\n📚 Installed Ollama Models:")
        for model in models:
            print(f"  • {model['name']}")
    else:
        print("No Ollama models installed or Ollama not running")


def cmd_setup():
    """Run setup wizard"""
    import subprocess
    subprocess.run([sys.executable, "setup_models.py"])


def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "status":
        cmd_status()
    elif command == "catalog":
        cmd_catalog()
    elif command == "info":
        cmd_info(args)
    elif command == "download":
        cmd_download(args)
    elif command == "list":
        cmd_list()
    elif command == "setup":
        cmd_setup()
    elif command == "help" or command == "-h":
        print_help()
    else:
        print(f"Unknown command: {command}\n")
        print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
