# Used LLM configuration, provide an API key for the LLM you want to use, leave others empty
OPENAI_API_KEY = ""
OPENAI_MODEL = "gpt-4-turbo-preview"  # or "gpt-3.5-turbo" for a cheaper option
OPENAI_BASE_URL = "https://api.openai.com/v1"  # Default OpenAI URL

GROQ_API_KEY = ""
GROQ_MODEL = "llama3-8b-8192"

HEURIST_API_KEY = ""
HEURIST_MODEL = "mistralai/mixtral-8x7b-instruct"  # Example Heurist model
HEURIST_BASE_URL = "https://llm-gateway.heurist.xyz"

# Memory configuration
USE_MEMORY = False  # Set to False to disable conversation memory
MAX_MEMORY_ITEMS = 3  # Number of previous exchanges to remember
MEMORY_MAX_AGE_HOURS = 24  # How long to keep conversations in memory

# Telegram configuration
TELEGRAM_BOT_TOKEN = ""  # Your Telegram bot token from @BotFather

# API configuration
USE_API = False  # Set to True to enable API server
API_HOST = "127.0.0.1"  # Use "0.0.0.0" to allow external connections
API_PORT = 8000
SEND_FULL_SWARM_RESPONSE = True  # Set to True to send all agent responses via API
USE_STREAMING = True  # Set to True to enable streaming responses

# Swarm configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# SSL configuration
SSL_ENABLED = False  # SSL will be handled by Nginx instead 