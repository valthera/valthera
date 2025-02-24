import os
from typing import Dict, Any, Optional, AsyncGenerator
from openai import AsyncOpenAI
from ..base import BaseModel, ModelProvider, ModelParameters, ModelResponse


class OpenAIModel(BaseModel):
    def __init__(self, model_name: str = "gpt-4"):
        super().__init__(model_name, ModelProvider.OPENAI)
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def generate(
            self, 
            prompt: str, 
            params: Optional[ModelParameters] = None
            ) -> ModelResponse:
        params = params or ModelParameters()
        
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=params.temperature,
            max_tokens=params.max_tokens,
            top_p=params.top_p,
            frequency_penalty=params.frequency_penalty,
            presence_penalty=params.presence_penalty,
            stop=params.stop
        )

        return ModelResponse(
            text=response.choices[0].message.content,
            usage=response.usage.model_dump(),
            model_name=self.model_name,
            provider=self.provider,
            metadata=params.metadata
        )

    async def generate_stream(
            self, 
            prompt: str, 
            params: Optional[ModelParameters] = None
         ) -> AsyncGenerator[str, None]:
        params = params or ModelParameters()

        stream = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=params.temperature,
            max_tokens=params.max_tokens,
            stream=True
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    def validate_credentials(self) -> bool:
        return bool(os.getenv("OPENAI_API_KEY"))

    @property
    def model_info(self) -> Dict[str, Any]:
        return {
            "name": self.model_name,
            "provider": self.provider,
            "requires_api_key": True,
            "supports_streaming": True
        }
