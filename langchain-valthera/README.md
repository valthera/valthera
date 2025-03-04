# langchain-valthera

This package contains the LangChain integration with Valthera

## Installation

```bash
pip install -U langchain-valthera
```

And you should configure credentials by setting the following environment variables:

* TODO: fill this out

## Chat Models

`ChatValthera` class exposes chat models from Valthera.

```python
from langchain_valthera import ChatValthera

llm = ChatValthera()
llm.invoke("Sing a ballad of LangChain.")
```

## Embeddings

`ValtheraEmbeddings` class exposes embeddings from Valthera.

```python
from langchain_valthera import ValtheraEmbeddings

embeddings = ValtheraEmbeddings()
embeddings.embed_query("What is the meaning of life?")
```

## LLMs
`ValtheraLLM` class exposes LLMs from Valthera.

```python
from langchain_valthera import ValtheraLLM

llm = ValtheraLLM()
llm.invoke("The meaning of life is")
```
