import asyncio
import threading
from agents.swarm import AgentSwarm
from agents.telegram_bot import TelegramBot
from agents.api_server import APIServer
from config.settings import (
    TELEGRAM_BOT_TOKEN,
    USE_MEMORY,
    USE_API,
    API_HOST,
    API_PORT
)

async def cli_mode():
    """Run in CLI mode"""
    swarm = AgentSwarm()
    if USE_MEMORY:
        swarm.memory.start_cleanup()
    
    print("Welcome to the AI Agent Swarm!")
    print("Please enter your query (or 'quit' to exit):")
    
    while True:
        try:
            user_query = input("\n❓ Your query: ").strip()
            if user_query.lower() == 'quit':
                break
            if not user_query:
                continue
                
            await swarm.process_query(user_query)
            print("\n-----------------------------------")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please try again or type 'quit' to exit.")

def telegram_mode():
    """Run in Telegram mode"""
    print("🤖 Starting AI Agent Swarm in Telegram mode...")
    bot = TelegramBot()
    bot.run()

def start_api_server():
    """Start the API server in a separate thread"""
    server = APIServer(host=API_HOST, port=API_PORT)
    server.run()

if __name__ == "__main__":
    # Start API server if enabled
    if USE_API:
        print(f"🚀 Starting API server on {API_HOST}:{API_PORT}")
        api_thread = threading.Thread(target=start_api_server, daemon=True)
        api_thread.start()
    
    # Run main interface (CLI or Telegram)
    if TELEGRAM_BOT_TOKEN:
        telegram_mode()
    else:
        print("ℹ️ No Telegram token found in settings.py, running in CLI mode...")
        asyncio.run(cli_mode())