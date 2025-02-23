import aiohttp
from typing import Dict, Any, Optional, AsyncGenerator
from ..base import BaseModel, ModelProvider, ModelParameters, ModelResponse

class OllamaModel(BaseModel):
    def __init__(self, model_name: str = "llama2", base_url: str = "http://localhost:11434"):
        super().__init__(model_name, ModelProvider.OLLAMA)
        self.base_url = base_url

    async def generate(self, prompt: str, params: Optional[ModelParameters] = None) -> ModelResponse:
        params = params or ModelParameters()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "temperature": params.temperature,
                    "top_p": params.top_p,
                    "stop": params.stop
                }
            ) as response:
                result = await response.json()
                
                return ModelResponse(
                    text=result["response"],
                    usage={
                        "prompt_tokens": result.get("prompt_eval_count", 0),
                        "completion_tokens": result.get("eval_count", 0),
                        "total_tokens": result.get("total_eval_count", 0)
                    },
                    model_name=self.model_name,
                    provider=self.provider,
                    metadata=params.metadata
                )

    async def generate_stream(self, prompt: str, params: Optional[ModelParameters] = None) -> AsyncGenerator[str, None]:
        params = params or ModelParameters()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "temperature": params.temperature,
                    "top_p": params.top_p,
                    "stream": True
                }
            ) as response:
                async for line in response.content:
                    if line:
                        chunk = line.decode().strip()
                        if chunk:
                            yield chunk

    def validate_credentials(self) -> bool:
        # Ollama doesn't require credentials, just needs to be running
        return True

    @property
    def model_info(self) -> Dict[str, Any]:
        return {
            "name": self.model_name,
            "provider": self.provider,
            "requires_api_key": False,
            "supports_streaming": True
        }
