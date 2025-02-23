from valthera.models.providers.openai import OpenAIModel
from valthera.models.providers.ollama import OllamaModel

# Use OpenAI
model = OpenAIModel(model_name="gpt-4")
response = await model.generate("Hello, how are you?")

# Use Ollama locally
model = OllamaModel(model_name="llama2")
response = await model.generate("Hello, how are you?")

# Streaming example
async for chunk in model.generate_stream("Tell me a story"):
    print(chunk, end="", flush=True)