import json
import os
from typing import List, Generator
import ollama
from .vector_store import VectorStore
from .conversation import add_message, log_query
from . import config as _config
from .utils import logger


def _get_active_provider_display() -> str:
    mode = get_mode()
    if mode == "cloud":
        return f"{_config.config.cloud.provider} ({_config.config.cloud.model})"
    elif mode == "hybrid":
        return f"{_config.config.ollama.model} (fallback to {_config.config.cloud.provider})"
    else:
        return f"Ollama ({_config.config.ollama.model})"


def get_mode() -> str:
    env_mode = os.environ.get("WEBAI_CHAT_MODE", "")
    if env_mode:
        return env_mode
    cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            import yaml
            data = yaml.safe_load(f)
            if data and "chat" in data and "mode" in data["chat"]:
                return data["chat"]["mode"]
    return "local"


def _get_system_prompt() -> str:
    custom_prompt = _config.config.chat.system_prompt
    default_prompt = (
        "You are WebAI Chat, a helpful assistant for [Company]. "
        "Answer ONLY from the provided documents. "
        "DO NOT generate stories, creative content, or any information not found in the provided documents. "
        "DO NOT make up answers, DO NOT hallucinate, DO NOT use general knowledge. "
        "If the answer is not in the provided documents, reply EXACTLY with: "
        "'I don't have that information in the provided documents.'"
    )
    if custom_prompt and custom_prompt != default_prompt:
        return custom_prompt
    mode = get_mode()
    provider = _get_active_provider_display()
    return (
        f"You are WebAI Chat, a helpful assistant for [Company]. "
        f"You are powered by {provider}. "
        "Answer ONLY from the provided documents. "
        "DO NOT generate stories, creative content, or any information not found in the provided documents. "
        "DO NOT make up answers, DO NOT hallucinate, DO NOT use general knowledge. "
        "If the answer is not in the provided documents, reply EXACTLY with: "
        "'I don't have that information in the provided documents.'"
    )


class ChatEngine:
    def __init__(self):
        self.vector_store = VectorStore()

    def _stream_ollama(self, prompt: str) -> Generator[str, None, None]:
        response = ollama.chat(
            model=_config.config.ollama.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            options={"num_predict": _config.config.chat.max_tokens},
        )
        for chunk in response:
            content = chunk["message"]["content"]
            if content:
                yield content

    def _stream_cloud(self, prompt: str) -> Generator[str, None, None]:
        try:
            import litellm
        except ImportError:
            logger.error("litellm not installed. Install with: pip install litellm")
            yield "Cloud mode is not available. Please install litellm."
            return

        provider = _config.config.cloud.provider
        if provider == "google":
            provider = "gemini"
        model_name = f"{provider}/{_config.config.cloud.model}"
        kwargs = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": _config.config.chat.max_tokens,
            "stream": True,
        }
        if _config.config.cloud.api_key:
            kwargs["api_key"] = _config.config.cloud.api_key
        if _config.config.cloud.base_url:
            kwargs["base_url"] = _config.config.cloud.base_url

        try:
            response = litellm.completion(**kwargs)
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Cloud streaming failed: {e}")
            yield "I'm sorry, I'm having trouble processing your request."

    def chat(self, session_id: str, message: str) -> str:
        add_message(session_id, "user", message)
        logger.info(f"Query from session {session_id}: {message}")
        chunks = self.vector_store.search(message, top_k=_config.config.chat.top_k)
        if not chunks:
            response = "I don't have any documents indexed. Please crawl a website or upload documents first."
            add_message(session_id, "assistant", response)
            log_query(session_id, message, response, json.dumps([]))
            return response
        context = "\n\n".join([c["content"] for c in chunks])
        prompt = f"{_config.config.chat.system_prompt}\n\nRelevant information:\n{context}\n\nUser question: {message}"
        mode = get_mode()
        logger.info(f"Using mode: {mode}")
        answer = None
        if mode == "cloud":
            try:
                answer = "".join(self._stream_cloud(prompt))
            except Exception as e:
                logger.error(f"Cloud failed: {e}")
                answer = "I'm sorry, I'm having trouble processing your request. Please check your cloud API configuration."
        elif mode == "hybrid":
            try:
                answer = "".join(self._stream_ollama(prompt))
            except Exception as e:
                logger.warning(f"Ollama failed: {e}, falling back to cloud")
                try:
                    answer = "".join(self._stream_cloud(prompt))
                except Exception as e2:
                    logger.error(f"Cloud also failed: {e2}")
                    answer = "I'm sorry, I'm having trouble processing your request. Please check your configuration."
        else:
            try:
                answer = "".join(self._stream_ollama(prompt))
            except Exception as e:
                logger.error(f"Ollama failed: {e}")
                answer = "I'm sorry, I'm having trouble processing your request. Please check that Ollama is running and the model is loaded."
        add_message(session_id, "assistant", answer)
        source_info = [{"source": c["metadata"].get("source", ""), "chunk": c["content"][:200]} for c in chunks]
        log_query(session_id, message, answer, json.dumps(source_info))
        logger.info(f"Response for session {session_id}: {answer[:100]}...")
        return answer

    def stream_chat(self, session_id: str, message: str) -> Generator[str, None, None]:
        add_message(session_id, "user", message)
        logger.info(f"Query from session {session_id}: {message}")
        chunks = self.vector_store.search(message, top_k=_config.config.chat.top_k)
        if not chunks:
            response = "I don't have any documents indexed. Please crawl a website or upload documents first."
            add_message(session_id, "assistant", response)
            log_query(session_id, message, response, json.dumps([]))
            yield response
            return
        context = "\n\n".join([c["content"] for c in chunks])
        prompt = f"{_config.config.chat.system_prompt}\n\nRelevant information:\n{context}\n\nUser question: {message}"
        mode = get_mode()
        logger.info(f"Using mode: {mode}")
        answer = ""
        if mode == "cloud":
            try:
                for token in self._stream_cloud(prompt):
                    answer += token
                    yield token
            except Exception as e:
                logger.error(f"Cloud failed: {e}")
                error_msg = "I'm sorry, I'm having trouble processing your request."
                yield error_msg
                answer = error_msg
        elif mode == "hybrid":
            try:
                for token in self._stream_ollama(prompt):
                    answer += token
                    yield token
            except Exception as e:
                logger.warning(f"Ollama failed: {e}, falling back to cloud")
                answer = ""
                try:
                    for token in self._stream_cloud(prompt):
                        answer += token
                        yield token
                except Exception as e2:
                    logger.error(f"Cloud also failed: {e2}")
                    error_msg = "I'm sorry, I'm having trouble processing your request."
                    yield error_msg
                    answer = error_msg
        else:
            try:
                for token in self._stream_ollama(prompt):
                    answer += token
                    yield token
            except Exception as e:
                logger.error(f"Ollama failed: {e}")
                error_msg = "I'm sorry, I'm having trouble processing your request. Please check that Ollama is running and the model is loaded."
                yield error_msg
                answer = error_msg
        add_message(session_id, "assistant", answer)
        source_info = [{"source": c["metadata"].get("source", ""), "chunk": c["content"][:200]} for c in chunks]
        log_query(session_id, message, answer, json.dumps(source_info))
        logger.info(f"Response for session {session_id}: {answer[:100]}...")
