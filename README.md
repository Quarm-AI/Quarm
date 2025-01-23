![Quantum Swarm Banner](images/banner.jpg)

# Started migration to ElizaOS

# Stay tuned!

![ElizaOS](https://github.com/elizaOS/eliza/raw/develop/docs/static/img/eliza_banner.jpg)

# Quantum Swarm 🤖

Quantum Swarm (QUARM) is a powerful multi-agent system that processes queries through a coordinated swarm of specialized AI agents. Each agent has a unique role in analyzing and responding to user queries, providing comprehensive and well-thought-out responses.

## Features ✨

- **Multi-Agent Processing**: Complex queries are processed by multiple specialized agents:

  - Query Triage: Determines query complexity
  - Query Interpreter: Breaks down and analyzes queries
  - Research Specialist: Identifies key areas for investigation
  - Critical Analyzer: Evaluates information and identifies gaps
  - Creative Explorer: Generates novel perspectives
  - Information Synthesizer: Combines insights into coherent responses

- **Multiple Interfaces**:

  - CLI mode for direct interaction
  - Telegram bot integration
  - RESTful API with streaming support
  - Web interface support

- **Advanced Capabilities**:
  - Streaming responses in real-time
  - Conversation memory with automatic cleanup
  - Customizable agent parameters
  - Support for multiple LLM providers (OpenAI, Groq, Heurist)
  - CORS support for web integration

## Installation 🚀

1. Clone the repository:

```bash
git clone https://github.com/QuarmFW/Quarm.git
cd quarm
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure settings:
   - Copy `config/settings.py` and configure your API keys and preferences

We have also created a webpage that allows you to generate the roles file in the proper format. [Click here to generate your roles file](https://quarm.io/generator.html).

## Usage 💡

### CLI Mode

```bash
python main.py
```

### Telegram Bot

1. Get a bot token from [@BotFather](https://t.me/botfather)
2. Add the token to `config/settings.py`
3. Run:

```bash
python main.py
```

### API Server

1. Configure API settings in `config/settings.py`
2. Run:

```bash
python main.py
```

The API will be available at `http://localhost:8000` by default.

## API Endpoints 🌐

- `GET /health`: Health check endpoint
- `GET /agent-parameters`: Get available agent parameters
- `POST /query`: Process a query through the agent swarm

### Query Example

```json
{
  "text": "Your query here",
  "user_id": "optional_user_id",
  "parameters": {
    "interpreter": {
      "depth_of_analysis": 80
    },
    "researcher": {
      "technical_depth": 90
    }
  }
}
```

## Configuration ⚙️

Key settings in `config/settings.py`:

- LLM Provider Configuration:

  - `OPENAI_API_KEY`: OpenAI API key
  - `GROQ_API_KEY`: Groq API key
  - `HEURIST_API_KEY`: Heurist API key

- Interface Settings:

  - `USE_API`: Enable/disable API server
  - `USE_MEMORY`: Enable/disable conversation memory
  - `TELEGRAM_BOT_TOKEN`: Telegram bot token

- Server Configuration:
  - `API_HOST`: API server host
  - `API_PORT`: API server port
  - `SSL_ENABLED`: Enable/disable SSL

## Contributing 🤝

Contributions are welcome. Please feel free to submit a Pull Request. Please note that this project is currently in development phase, and the codebase is not yet fully stable. It's currently capable of processing queries through a set pipeline of multiple agents, and possible integrations with frameworks like ElizaOS are in the works.

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
