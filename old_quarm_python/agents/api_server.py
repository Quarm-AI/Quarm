from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, AsyncGenerator
from agents.swarm import AgentSwarm
from config.settings import (
    SSL_ENABLED, 
    SEND_FULL_SWARM_RESPONSE, 
    USE_STREAMING
)
import json
import uvicorn

class AgentParameters(BaseModel):
    interpreter: Optional[Dict[str, int]] = None
    researcher: Optional[Dict[str, int]] = None
    critic: Optional[Dict[str, int]] = None
    creative: Optional[Dict[str, int]] = None
    synthesizer: Optional[Dict[str, int]] = None

class Query(BaseModel):
    text: str
    user_id: Optional[str] = "default"
    parameters: Optional[AgentParameters] = None

class APIServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.app = FastAPI(
            title="AI Agent Swarm API",
            description="API interface for the AI Agent Swarm",
            version="1.0.0"
        )
        self.host = host
        self.port = port
        self.swarm = AgentSwarm()
        
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["https://quarm.io"],
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
            expose_headers=["Content-Type", "Authorization"],
            max_age=3600
        )
        
        self.setup_routes()

    async def stream_to_sse(self, generator: AsyncGenerator) -> AsyncGenerator[str, None]:
        """Convert generator output to SSE format"""
        try:
            async for chunk in generator:
                if chunk:
                    # Format as SSE data
                    yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            error_msg = f"data: {json.dumps({'error': str(e)})}\n\n"
            yield error_msg
    
    def setup_routes(self):
        @self.app.get("/agent-parameters")
        async def get_agent_parameters():
            """Get available agent parameters and their defaults"""
            from agents.roles import AGENT_ROLES
            parameters = {}
            for role, config in AGENT_ROLES.items():
                if "parameters" in config:
                    parameters[role] = config["parameters"]
            return parameters

        @self.app.post("/query")
        async def process_query(query: Query):
            try:
                if USE_STREAMING:
                    generator = self.swarm.process_query_streaming(
                        query.text,
                        user_id=query.user_id,
                        parameters=query.parameters.dict() if query.parameters else None
                    )
                    return StreamingResponse(
                        self.stream_to_sse(generator),
                        media_type='text/event-stream'
                    )
                else:
                    if SEND_FULL_SWARM_RESPONSE:
                        responses = await self.swarm.process_query_with_details(
                            query.text,
                            user_id=query.user_id,
                            parameters=query.parameters.dict() if query.parameters else None
                        )
                        return responses
                    else:
                        response = await self.swarm.process_query(
                            query.text,
                            user_id=query.user_id,
                            parameters=query.parameters.dict() if query.parameters else None
                        )
                        return {"response": response}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy"}
    
    def run(self):
        """Start the API server"""
        print(f"🚀 Starting AI Agent Swarm API server on port {self.port}...")
        uvicorn.run(self.app, host=self.host, port=self.port) 