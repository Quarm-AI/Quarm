from typing import Dict, Optional, AsyncGenerator
import asyncio
from groq import AsyncGroq
from openai import AsyncOpenAI
from config.settings import (
    GROQ_API_KEY, 
    OPENAI_API_KEY,
    HEURIST_API_KEY,
    GROQ_MODEL,
    OPENAI_MODEL,
    HEURIST_MODEL,
    OPENAI_BASE_URL,
    HEURIST_BASE_URL,
    MAX_RETRIES, 
    RETRY_DELAY,
    USE_MEMORY,
    MAX_MEMORY_ITEMS,
    MEMORY_MAX_AGE_HOURS
)
from agents.roles import AGENT_ROLES
from agents.memory import ConversationMemory

class AgentSwarm:
    def __init__(self):
        # Select provider based on available API key
        if OPENAI_API_KEY:
            self.client = AsyncOpenAI(
                api_key=OPENAI_API_KEY,
                base_url=OPENAI_BASE_URL
            )
            self.model = OPENAI_MODEL
            self.provider = "openai"
        elif GROQ_API_KEY:
            self.client = AsyncGroq(api_key=GROQ_API_KEY)
            self.model = GROQ_MODEL
            self.provider = "groq"
        elif HEURIST_API_KEY:
            self.client = AsyncOpenAI(
                api_key=HEURIST_API_KEY,
                base_url=HEURIST_BASE_URL
            )
            self.model = HEURIST_MODEL
            self.provider = "heurist"
        else:
            raise ValueError("No API keys configured. Please add one in settings.py")
        self.memory = ConversationMemory(
            max_history=MAX_MEMORY_ITEMS,
            max_age_hours=MEMORY_MAX_AGE_HOURS
        ) if USE_MEMORY else None

    async def handle_streaming_response(self, stream) -> str:
        """Handle streaming response from Heurist"""
        full_response = []
        async for chunk in stream:
            if hasattr(chunk.choices[0].delta, "content"):
                content = chunk.choices[0].delta.content
                if content is not None:
                    full_response.append(content)
        return "".join(full_response)

    async def query_agent(self, role: Dict, context: str, parameters: Optional[Dict] = None) -> str:
        """Query a single agent with retry logic and custom parameters"""
        for attempt in range(MAX_RETRIES):
            try:
                # Get role parameters
                role_params = {}
                if parameters and role["name"].lower().replace(" ", "_") in parameters:
                    role_params = parameters[role["name"].lower().replace(" ", "_")]
                
                # Modify system prompt based on parameters
                system_prompt = role["system"]
                if role_params:
                    param_context = "\nParameters:\n"
                    for param, value in role_params.items():
                        param_context += f"- {param}: {value}%\n"
                    system_prompt = f"{system_prompt}\n{param_context}"

                messages = [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ]
                
                # Handle provider-specific parameters
                params = {
                    "messages": messages,
                    "model": self.model,
                }
                
                if self.provider == "openai":
                    params["temperature"] = 0.7
                elif self.provider == "heurist":
                    params["temperature"] = 0.7
                    params["max_tokens"] = 64
                    params["stream"] = True
                
                completion = await self.client.chat.completions.create(**params)
                
                # Handle streaming response for Heurist
                if self.provider == "heurist":
                    return await self.handle_streaming_response(completion)
                
                # Handle regular response for other providers
                return completion.choices[0].message.content
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    raise e
                await asyncio.sleep(RETRY_DELAY)

    async def handle_simple_query(self, triage_response: str) -> str:
        """Extract and format the response from the triage agent"""
        # Remove the "SIMPLE: " prefix and any extra whitespace
        return triage_response.replace("SIMPLE:", "").strip()

    async def process_query(self, user_query: str, telegram_mode: bool = False, user_id: str = "default") -> str:
        """Process a user query through the agent swarm"""
        print(f"\n🤔 Processing query: '{user_query}'\n")

        # Get conversation context if memory is enabled
        context_info = ""
        if self.memory:
            context = self.memory.get_context(user_id)
            if context:
                context_info = f"\nPrevious conversation:\n{context}"

        # Step 0: Triage the query
        triage_response = await self.query_agent(
            AGENT_ROLES["triage"],
            f"Evaluate this query: '{user_query}'{context_info}"
        )
        print(f"🔄 {AGENT_ROLES['triage']['name']}:")
        print(triage_response + "\n")

        # If it's a simple query, handle and store response
        if triage_response.startswith("SIMPLE:"):
            response = await self.handle_simple_query(triage_response)
            if self.memory:
                self.memory.add_exchange(user_id, user_query, response)
            return response

        # For complex queries, proceed with full swarm analysis
        print("⚡ Activating full agent swarm for complex query...\n")

        # Update interpreter prompt to include context
        interpreter_response = await self.query_agent(
            AGENT_ROLES["interpreter"],
            f"Analyze this query considering the conversation context:\n{context_info}\nQuery: '{user_query}'"
        )
        print(f"🔍 {AGENT_ROLES['interpreter']['name']}:")
        print(interpreter_response + "\n")

        # Step 2: Research Planning
        researcher_response = await self.query_agent(
            AGENT_ROLES["researcher"],
            f"Based on this interpretation:\n{interpreter_response}\nWhat specific aspects need investigation?"
        )
        print(f"📚 {AGENT_ROLES['researcher']['name']}:")
        print(researcher_response + "\n")

        # Step 3: Critical Analysis
        critic_response = await self.query_agent(
            AGENT_ROLES["critic"],
            f"Critically analyze these research points:\n{researcher_response}"
        )
        print(f"⚖️ {AGENT_ROLES['critic']['name']}:")
        print(critic_response + "\n")

        # Step 4: Creative Exploration
        creative_response = await self.query_agent(
            AGENT_ROLES["creative"],
            f"Given this analysis:\n{critic_response}\nExplore creative perspectives and alternatives."
        )
        print(f"💡 {AGENT_ROLES['creative']['name']}:")
        print(creative_response + "\n")

        # Step 5: Final Synthesis
        synthesis_context = f"""
        Original Query: {user_query}
        
        Interpretation: {interpreter_response}
        
        Research Points: {researcher_response}
        
        Critical Analysis: {critic_response}
        
        Creative Perspectives: {creative_response}
        
        Please synthesize all this information into a comprehensive response.
        """
        
        final_response = await self.query_agent(
            AGENT_ROLES["synthesizer"],
            synthesis_context
        )
        print(f"🎯 {AGENT_ROLES['synthesizer']['name']} - Final Response:")
        print(final_response + "\n")
        
        # Store the final response if memory is enabled
        if self.memory:
            self.memory.add_exchange(user_id, user_query, final_response)
        return final_response 

    async def process_query_with_details(self, user_query: str, user_id: str = "default") -> dict:
        """Process a query and return all agent responses"""
        print(f"\n🤔 Processing query: '{user_query}'\n")

        # Get conversation context if memory is enabled
        context_info = ""
        if self.memory:
            context = self.memory.get_context(user_id)
            if context:
                context_info = f"\nPrevious conversation:\n{context}"

        # Initialize response structure
        response = {
            "is_simple_query": False,
            "synthesizer": {"name": "Information Synthesizer", "response": ""}
        }

        # Step 0: Triage the query
        triage_response = await self.query_agent(
            AGENT_ROLES["triage"],
            f"Evaluate this query: '{user_query}'{context_info}"
        )
        print(f"🔄 {AGENT_ROLES['triage']['name']}:")
        print(triage_response + "\n")
        
        response["triage"] = {"name": "Query Triage", "response": triage_response}

        # If it's a simple query, handle and return
        if triage_response.startswith("SIMPLE:"):
            simple_response = await self.handle_simple_query(triage_response)
            if self.memory:
                self.memory.add_exchange(user_id, user_query, simple_response)
            response["is_simple_query"] = True
            response["synthesizer"]["response"] = simple_response
            return response

        # For complex queries, proceed with full swarm analysis
        print("⚡ Activating full agent swarm for complex query...\n")

        # Step 1: Interpretation
        interpreter_response = await self.query_agent(
            AGENT_ROLES["interpreter"],
            f"Analyze this query considering the conversation context:\n{context_info}\nQuery: '{user_query}'"
        )
        print(f"🔍 {AGENT_ROLES['interpreter']['name']}:")
        print(interpreter_response + "\n")
        response["interpreter"] = {"name": "Query Interpreter", "response": interpreter_response}

        # Step 2: Research
        researcher_response = await self.query_agent(
            AGENT_ROLES["researcher"],
            f"Based on this interpretation:\n{interpreter_response}\nWhat specific aspects need investigation?"
        )
        print(f"📚 {AGENT_ROLES['researcher']['name']}:")
        print(researcher_response + "\n")
        response["researcher"] = {"name": "Research Specialist", "response": researcher_response}

        # Step 3: Critical Analysis
        critic_response = await self.query_agent(
            AGENT_ROLES["critic"],
            f"Critically analyze these research points:\n{researcher_response}"
        )
        print(f"⚖️ {AGENT_ROLES['critic']['name']}:")
        print(critic_response + "\n")
        response["critic"] = {"name": "Critical Analyzer", "response": critic_response}

        # Step 4: Creative Exploration
        creative_response = await self.query_agent(
            AGENT_ROLES["creative"],
            f"Given this analysis:\n{critic_response}\nExplore creative perspectives and alternatives."
        )
        print(f"💡 {AGENT_ROLES['creative']['name']}:")
        print(creative_response + "\n")
        response["creative"] = {"name": "Creative Explorer", "response": creative_response}

        # Step 5: Final Synthesis
        synthesis_context = f"""
        Original Query: {user_query}
        
        Interpretation: {interpreter_response}
        
        Research Points: {researcher_response}
        
        Critical Analysis: {critic_response}
        
        Creative Perspectives: {creative_response}
        
        Please synthesize all this information into a comprehensive response.
        """
        
        final_response = await self.query_agent(
            AGENT_ROLES["synthesizer"],
            synthesis_context
        )
        print(f"🎯 {AGENT_ROLES['synthesizer']['name']} - Final Response:")
        print(final_response + "\n")
        
        response["synthesizer"]["response"] = final_response

        # Store the final response if memory is enabled
        if self.memory:
            self.memory.add_exchange(user_id, user_query, final_response)

        return response 

    async def process_query_streaming(self, user_query: str, user_id: str = "default", parameters: Optional[Dict] = None) -> AsyncGenerator[Dict, None]:
        """Process a query and stream the response in real-time"""
        print(f"\n🤔 Processing query: '{user_query}'\n")

        # Get conversation context if memory is enabled
        context_info = ""
        if self.memory:
            context = self.memory.get_context(user_id)
            if context:
                context_info = f"\nPrevious conversation:\n{context}"

        # Step 0: Triage
        print(f"🔄 {AGENT_ROLES['triage']['name']}:")
        triage_text = ""
        async for chunk in self.query_agent_stream(
            AGENT_ROLES["triage"],
            f"Evaluate this query: '{user_query}'{context_info}"
        ):
            triage_text += chunk
            yield {
                "role": "triage",
                "name": AGENT_ROLES["triage"]["name"],
                "content": chunk
            }
        print("\n")

        # If simple query, stream direct response
        if triage_text.startswith("SIMPLE:"):
            simple_response = triage_text.replace("SIMPLE:", "").strip()
            if self.memory:
                self.memory.add_exchange(user_id, user_query, simple_response)
            yield {
                "role": "synthesizer",
                "name": "Simple Response",
                "content": simple_response
            }
            return

        # For complex queries, proceed with full swarm analysis
        print("⚡ Activating full agent swarm for complex query...\n")

        # Step 1: Interpretation
        print(f"🔍 {AGENT_ROLES['interpreter']['name']}:")
        interpreter_text = ""
        async for chunk in self.query_agent_stream(
            AGENT_ROLES["interpreter"],
            f"Analyze this query considering the conversation context:\n{context_info}\nQuery: '{user_query}'",
            parameters
        ):
            interpreter_text += chunk
            yield {
                "role": "interpreter",
                "name": AGENT_ROLES["interpreter"]["name"],
                "content": chunk
            }
        print("\n")

        # Step 2: Research
        print(f"📚 {AGENT_ROLES['researcher']['name']}:")
        researcher_text = ""
        async for chunk in self.query_agent_stream(
            AGENT_ROLES["researcher"],
            f"Based on this interpretation:\n{interpreter_text}\nWhat specific aspects need investigation?",
            parameters
        ):
            researcher_text += chunk
            yield {
                "role": "researcher",
                "name": AGENT_ROLES["researcher"]["name"],
                "content": chunk
            }
        print("\n")

        # Step 3: Critical Analysis
        print(f"⚖️ {AGENT_ROLES['critic']['name']}:")
        critic_text = ""
        async for chunk in self.query_agent_stream(
            AGENT_ROLES["critic"],
            f"Critically analyze these research points:\n{researcher_text}",
            parameters
        ):
            critic_text += chunk
            yield {
                "role": "critic",
                "name": AGENT_ROLES["critic"]["name"],
                "content": chunk
            }
        print("\n")

        # Step 4: Creative Exploration
        print(f"💡 {AGENT_ROLES['creative']['name']}:")
        creative_text = ""
        async for chunk in self.query_agent_stream(
            AGENT_ROLES["creative"],
            f"Given this analysis:\n{critic_text}\nExplore creative perspectives and alternatives.",
            parameters
        ):
            creative_text += chunk
            yield {
                "role": "creative",
                "name": AGENT_ROLES["creative"]["name"],
                "content": chunk
            }
        print("\n")

        # Step 5: Final Synthesis
        synthesis_context = f"""
        Original Query: {user_query}
        
        Interpretation: {interpreter_text}
        
        Research Points: {researcher_text}
        
        Critical Analysis: {critic_text}
        
        Creative Perspectives: {creative_text}
        
        Please synthesize all this information into a comprehensive response.
        """
        
        print(f"🎯 {AGENT_ROLES['synthesizer']['name']} - Final Response:")
        final_response = ""
        async for chunk in self.query_agent_stream(
            AGENT_ROLES["synthesizer"],
            synthesis_context,
            parameters
        ):
            final_response += chunk
            yield {
                "role": "synthesizer",
                "name": AGENT_ROLES["synthesizer"]["name"],
                "content": chunk
            }
        print("\n")

        # Store the final response if memory is enabled
        if self.memory:
            self.memory.add_exchange(user_id, user_query, final_response)

    async def query_agent_stream(self, role: Dict, context: str, parameters: Optional[Dict] = None) -> AsyncGenerator[str, None]:
        """Query a single agent with streaming"""
        try:
            # Get role parameters
            role_params = {}
            if parameters and role["name"].lower().replace(" ", "_") in parameters:
                role_params = parameters[role["name"].lower().replace(" ", "_")]
            
            # Modify system prompt based on parameters
            system_prompt = role["system"]
            if role_params:
                param_context = "\nParameters:\n"
                for param, value in role_params.items():
                    param_context += f"- {param}: {value}%\n"
                system_prompt = f"{system_prompt}\n{param_context}"

            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": context
                }
            ]
            
            params = {
                "messages": messages,
                "model": self.model,
                "stream": True
            }
            
            if self.provider == "openai":
                params["temperature"] = 0.7
            elif self.provider == "heurist":
                params["temperature"] = 0.7
                params["max_tokens"] = 64
            
            stream = await self.client.chat.completions.create(**params)
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            print(f"Streaming error: {str(e)}")
            # Fallback to non-streaming if streaming fails
            response = await self.query_agent(role, context, parameters)
            yield response 