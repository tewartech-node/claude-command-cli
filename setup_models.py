#!/usr/bin/env python3
"""
Easy setup for LLM models - run this to get started
"""

import sys
import os
from agent.models import ModelManager


def main():
    mm = ModelManager()

    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║          🧠 The Brain - Model Setup Wizard 🧠                ║
║                                                               ║
║            Download LLM models for your network               ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    # Show current status
    print("\n📊 Current Status:\n")
    mm.print_status()

    print("\n" + "="*60)
    print("Available Providers:")
    print("="*60)
    print("""
1️⃣  Ollama (Recommended - Unlimited Free, Local)
    Install once, use everywhere. No API key needed.

2️⃣  Groq (Free Tier - 30 req/min)
    Fast cloud inference, perfect for fallback.

3️⃣  Together AI (Free Tier)
    Alternative cloud provider.

4️⃣  HuggingFace (Free Tier)
    Alternative cloud provider.

5️⃣  View All Models

6️⃣  Exit
    """)

    choice = input("Select option (1-6): ").strip()

    if choice == "1":
        setup_ollama(mm)
    elif choice == "2":
        setup_groq(mm)
    elif choice == "3":
        setup_together(mm)
    elif choice == "4":
        setup_huggingface(mm)
    elif choice == "5":
        mm.print_catalog()
    elif choice == "6":
        print("Goodbye! 🚀")
        return
    else:
        print("Invalid option")
        return

    print("\n✅ Setup complete! Your Brain is ready to think.\n")


def setup_ollama(mm):
    """Setup Ollama"""
    print("\n" + "="*60)
    print("Setting up Ollama")
    print("="*60)

    setup_cmds = mm.get_setup_commands("ollama")

    print(f"""
📥 Installation:
   {setup_cmds['install']}

Once installed:
   1️⃣  Start Ollama:     {setup_cmds['start']}
   2️⃣  Download model:   {setup_cmds['download']}
   3️⃣  Test it:         {setup_cmds['test']}

Then The Brain will auto-detect and use it!
    """)

    # Try auto-setup if Ollama is installed
    try:
        import subprocess
        subprocess.run(["ollama", "--version"], capture_output=True, timeout=2)
        print("\n✅ Ollama is installed!\n")

        auto = input("Auto-download recommended model? (y/n): ").strip().lower()
        if auto == "y":
            print("\nDownloading Mistral 7B (4.1GB)...")
            print("(This may take 5-10 minutes on first run)\n")

            if mm.download_ollama_models(["mistral"]):
                print("\n✅ Mistral downloaded successfully!")
                print("\nNext: Run 'ollama serve' in a terminal")
                print("Then: python -m agent.core.agent")
            else:
                print("❌ Download failed")
    except:
        print("Ollama not yet installed. Download and install first, then re-run this script.")


def setup_groq(mm):
    """Setup Groq"""
    print("\n" + "="*60)
    print("Setting up Groq (30 requests/minute free)")
    print("="*60)

    setup_cmds = mm.get_setup_commands("groq")

    print(f"""
📝 Setup Steps:

1️⃣  Get free API key:
    Visit: {setup_cmds['api_key']}

2️⃣  Set environment variable:

    Linux/Mac/Termux:
    echo 'export GROQ_API_KEY="gsk_..."' >> ~/.bashrc
    source ~/.bashrc

    Windows (PowerShell):
    [System.Environment]::SetEnvironmentVariable("GROQ_API_KEY", "gsk_...", "User")
    # Restart terminal

3️⃣  Test setup:
    python -c "from agent.executor.free_connectors import FreeAIConnectors; print('Ready!')"

4️⃣  Start The Brain:
    python -m agent.core.agent

Done! Your Brain will use Groq for fast inference.
    """)

    key = input("\n📌 Have you set GROQ_API_KEY? (y/n): ").strip().lower()
    if key == "y":
        print("✅ Groq is ready!")
    else:
        print("⏳ Come back after setting the environment variable")


def setup_together(mm):
    """Setup Together AI"""
    print("\n" + "="*60)
    print("Setting up Together AI")
    print("="*60)

    setup_cmds = mm.get_setup_commands("together")

    print(f"""
📝 Setup Steps:

1️⃣  Get free API key:
    Visit: {setup_cmds['api_key']}

2️⃣  Set environment variable:
    export TOGETHER_API_KEY="..."

3️⃣  Test and run The Brain
    python -m agent.core.agent

Done!
    """)


def setup_huggingface(mm):
    """Setup HuggingFace"""
    print("\n" + "="*60)
    print("Setting up HuggingFace")
    print("="*60)

    setup_cmds = mm.get_setup_commands("huggingface")

    print(f"""
📝 Setup Steps:

1️⃣  Get free API token:
    Visit: {setup_cmds['api_key']}

2️⃣  Set environment variable:
    export HF_API_KEY="hf_..."

3️⃣  Test and run The Brain
    python -m agent.core.agent

Done!
    """)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled. Goodbye! 🚀")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
