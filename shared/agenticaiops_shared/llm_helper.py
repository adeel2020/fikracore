"""LLM Helper - Unified LLM instantiation with fallback support."""
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

try:
    from crewai import LLM
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False

try:
    from llama_index.llms.openai import OpenAI as LlamaOpenAI
    HAS_LLAMAINDEX = True
except ImportError:
    HAS_LLAMAINDEX = False


def create_llm_with_fallback(
    api_key: Optional[str] = None,
    api_base: str = "https://api.openai.com/v1",
    model: str = "gpt-4o-mini",
    fallback_api_base: str = "http://localhost:11434/v1",
    fallback_model: str = "llama3.1:8b",
    enable_fallback: bool = True,
    temperature: float = 0.7,
    max_retries: int = 1,
    streaming: bool = False,
    **kwargs
) -> Optional[Any]:
    """
    Create an LLM instance with fallback support.
    
    Tries to create an LLM with OpenAI first. If it fails and fallback is enabled,
    falls back to Ollama model.
    
    Args:
        api_key: OpenAI API key
        api_base: OpenAI API base URL
        model: OpenAI model name
        fallback_api_base: Fallback API base URL (Ollama)
        fallback_model: Fallback model name
        enable_fallback: Enable fallback to Ollama on failure
        temperature: Temperature for generation
        max_retries: Number of retries before falling back
        streaming: Enable streaming
        **kwargs: Additional arguments to pass to LLM
        
    Returns:
        LLM instance or None if instantiation fails
    """
    
    if not HAS_CREWAI:
        logger.warning("CrewAI not installed; LLM creation may fail")
        return None
    
    # Try primary (OpenAI)
    try:
        logger.info(f"Creating LLM with primary config: model={model}, base_url={api_base}")
        llm = LLM(
            model=model,
            base_url=api_base,
            api_key=api_key or "sk-placeholder",
            temperature=temperature,
            stream=streaming,
            **kwargs
        )
        logger.info("✓ Successfully created primary LLM instance (OpenAI)")
        return llm
    except Exception as e:
        logger.warning(f"Failed to create primary LLM: {str(e)}")
        
        # Try fallback (Ollama) if enabled
        if enable_fallback:
            try:
                logger.info(
                    f"Attempting fallback to Ollama: model={fallback_model}, "
                    f"base_url={fallback_api_base}"
                )
                llm = LLM(
                    model=fallback_model,
                    base_url=fallback_api_base,
                    api_key="ollama",
                    temperature=temperature,
                    stream=streaming,
                    **kwargs
                )
                logger.info("✓ Successfully created fallback LLM instance (Ollama)")
                return llm
            except Exception as fallback_err:
                logger.error(f"Failed to create fallback LLM: {str(fallback_err)}")
                return None
        else:
            return None


def create_llamaindex_llm_with_fallback(
    api_key: Optional[str] = None,
    api_base: str = "https://api.openai.com/v1",
    model: str = "gpt-4o-mini",
    fallback_api_base: str = "http://localhost:11434/v1",
    fallback_model: str = "llama3.1:8b",
    enable_fallback: bool = True,
    temperature: float = 0.7,
    **kwargs
) -> Optional[Any]:
    """
    Create a LlamaIndex OpenAI LLM instance with fallback support.
    
    Args:
        api_key: OpenAI API key
        api_base: OpenAI API base URL
        model: OpenAI model name
        fallback_api_base: Fallback API base URL (Ollama)
        fallback_model: Fallback model name
        enable_fallback: Enable fallback to Ollama on failure
        temperature: Temperature for generation
        **kwargs: Additional arguments to pass to LLM
        
    Returns:
        LlamaIndex OpenAI LLM instance or None if instantiation fails
    """
    
    if not HAS_LLAMAINDEX:
        logger.warning("LlamaIndex not installed; LLM creation may fail")
        return None
    
    # Try primary (OpenAI)
    try:
        logger.info(f"Creating LlamaIndex LLM with primary config: model={model}, base_url={api_base}")
        llm = LlamaOpenAI(
            model=model,
            api_key=api_key or "sk-placeholder",
            api_base=api_base,
            temperature=temperature,
            **kwargs
        )
        logger.info("✓ Successfully created primary LlamaIndex LLM instance (OpenAI)")
        return llm
    except Exception as e:
        logger.warning(f"Failed to create primary LlamaIndex LLM: {str(e)}")
        
        # Try fallback (Ollama) if enabled
        if enable_fallback:
            try:
                logger.info(
                    f"Attempting fallback to Ollama: model={fallback_model}, "
                    f"base_url={fallback_api_base}"
                )
                llm = LlamaOpenAI(
                    model=fallback_model,
                    api_key="ollama",
                    api_base=fallback_api_base,
                    temperature=temperature,
                    **kwargs
                )
                logger.info("✓ Successfully created fallback LlamaIndex LLM instance (Ollama)")
                return llm
            except Exception as fallback_err:
                logger.error(f"Failed to create fallback LlamaIndex LLM: {str(fallback_err)}")
                return None
        else:
            return None
