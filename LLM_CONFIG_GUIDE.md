# LLM Configuration Guide

## Overview

The system uses a **centralized configuration approach** with intelligent fallback support:

- **Primary**: OpenAI (`gpt-4o-mini`) on `https://api.openai.com/v1`
- **Fallback**: Ollama (`llama3.1:8b`) on `http://localhost:11434/v1` if OpenAI fails

All modules share one configuration source: `/shared/agenticaiops_shared/config.py`

## Configuration Structure

### Environment Variables (.env)

Set these in `backend/.env` or as system environment variables:

```env
# Primary: OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Fallback: Ollama Configuration (optional)
OLLAMA_API_BASE=http://localhost:11434/v1
OLLAMA_MODEL=llama3.1:8b

# Fallback Behavior
ENABLE_FALLBACK=true
MAX_RETRIES=1
```

### Python Configuration

All modules inherit from the centralized `Settings` class:

```python
from agenticaiops_shared.config import settings

# Get active LLM config (uses OpenAI if API key is set, else Ollama)
llm_config = settings.get_active_llm_config()
# Returns: {"model": "gpt-4o-mini", "api_base": "...", "api_key": "...", "is_openai": True}

# Or explicitly get primary or fallback
primary_config = settings.get_llm_config(use_primary=True)
fallback_config = settings.get_llm_config(use_primary=False)

# Access individual settings
print(settings.openai_model)  # "gpt-4o-mini"
print(settings.ollama_model)  # "llama3.1:8b"
print(settings.enable_fallback)  # True
```

## Using LLM Helper for Automatic Fallback

For automatic fallback support when LLM instantiation fails, use the LLM helper:

### CrewAI LLM with Fallback

```python
from agenticaiops_shared.llm_helper import create_llm_with_fallback
from agenticaiops_shared.config import settings

# Automatically tries OpenAI first, falls back to Ollama if it fails
llm = create_llm_with_fallback(
    api_key=settings.openai_api_key,
    api_base=settings.openai_api_base,
    model=settings.openai_model,
    fallback_api_base=settings.ollama_api_base,
    fallback_model=settings.ollama_model,
    enable_fallback=settings.enable_fallback,
    temperature=0.7,
    streaming=True
)

# Use with CrewAI Agent
from crewai import Agent, Task, Crew

agent = Agent(
    role="Analyst",
    goal="Analyze data",
    backstory="You are an expert analyst",
    llm=llm
)
```

### LlamaIndex OpenAI with Fallback

```python
from agenticaiops_shared.llm_helper import create_llamaindex_llm_with_fallback
from agenticaiops_shared.config import settings

# Automatically tries OpenAI first, falls back to Ollama if it fails
llm = create_llamaindex_llm_with_fallback(
    api_key=settings.openai_api_key,
    api_base=settings.openai_api_base,
    model=settings.openai_model,
    fallback_api_base=settings.ollama_api_base,
    fallback_model=settings.ollama_model,
    enable_fallback=settings.enable_fallback
)

# Use with LlamaIndex
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

documents = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(
    documents,
    llm=llm
)
```

## Module Configuration Architecture

### Centralized Config (Single Source of Truth)
- **File**: `shared/agenticaiops_shared/config.py`
- **Class**: `Settings`
- **Purpose**: Defines all LLM and system configurations

### Backend Config (Re-export)
- **File**: `backend/config.py`
- **Purpose**: Imports and re-exports shared config for backward compatibility

### Backend RAG Config (Enhanced)
- **File**: `backend/rag/config.py`
- **Purpose**: RAG-specific settings with LlamaIndex patches for Ollama support

### Services RAG Config (Enhanced)
- **File**: `services/agents/src/rag/config.py`
- **Purpose**: Services-specific RAG settings with fallback import handling

## Fallback Mechanism

### How It Works

1. **On startup**: Check if `OPENAI_API_KEY` is set
   - If set → Use OpenAI as primary
   - If not set → Use Ollama as primary

2. **During LLM instantiation** (when using helper):
   - Try OpenAI first
   - If connection fails → Fall back to Ollama (if `enable_fallback=True`)
   - Log all transitions for debugging

3. **For direct instantiation**: Use the primary config unless explicitly specified otherwise

### Enabling/Disabling Fallback

```python
# Enable fallback (default)
settings.enable_fallback = True

# Disable fallback (strict OpenAI only)
settings.enable_fallback = False
```

## Logging Configuration

The system logs all LLM operations:

```
✓ LlamaIndex OpenAI patches applied successfully
INFO: Creating LLM with primary config: model=gpt-4o-mini, base_url=https://api.openai.com/v1
✓ Successfully created primary LLM instance (OpenAI)
```

To see detailed logs, enable DEBUG level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Migration for Existing Code

### Old Pattern (Ollama hardcoded)
```python
from backend.config import settings
llm = LLM(model=settings.openai_model, base_url=settings.openai_api_base, api_key="ollama")
```

### New Pattern (Primary + Fallback)
```python
from agenticaiops_shared.config import settings
from agenticaiops_shared.llm_helper import create_llm_with_fallback

llm = create_llm_with_fallback(
    api_key=settings.openai_api_key,
    api_base=settings.openai_api_base,
    model=settings.openai_model,
    fallback_api_base=settings.ollama_api_base,
    fallback_model=settings.ollama_model,
    enable_fallback=settings.enable_fallback
)
```

## Troubleshooting

### Problem: "No OpenAI API key found"

**Solution**: Set `OPENAI_API_KEY` in your `.env`:
```env
OPENAI_API_KEY=sk-your-key-here
```

### Problem: Can't connect to Ollama fallback

**Solution**: Ensure Ollama is running:
```bash
# Start Ollama
ollama serve

# In another terminal, verify it's running
curl http://localhost:11434/api/tags
```

### Problem: LLM creation returns None

**Solution**: Check logs for detailed error:
```python
import logging
logging.getLogger("agenticaiops_shared.llm_helper").setLevel(logging.DEBUG)
```

## Best Practices

1. **Always use the helper** for automatic fallback support
2. **Set `OPENAI_API_KEY`** to use OpenAI as primary
3. **Keep Ollama running** locally for fallback reliability
4. **Monitor logs** for fallback transitions
5. **Test both paths** in development (with and without API key)

## File Dependencies

```
shared/agenticaiops_shared/
├── config.py           ← Centralized settings (SINGLE SOURCE OF TRUTH)
└── llm_helper.py       ← LLM instantiation helpers with fallback

backend/
├── config.py           ← Re-exports shared config
└── rag/config.py       ← RAG-specific with LlamaIndex patches

services/agents/src/
├── rag/config.py       ← Services RAG config with imports
└── main.py             ← Uses shared config
```

All backend and services modules automatically use the centralized config through their respective config imports.
