import os
os.environ["HF_HOME"] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.cache', 'huggingface')
os.environ["HF_HUB_OFFLINE"] = '1'
import yaml
from pydantic import BaseModel
from typing import Optional, List


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    username: str = ""
    password: str = ""


class OllamaConfig(BaseModel):
    url: str = "http://localhost:11434"
    model: str = "qwen2.5:3b"
    embedding_model: str = "all-MiniLM-L6-v2"


class CloudConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: str = ""
    base_url: str = ""


class ChatConfig(BaseModel):
    system_prompt: str = (
        "You are WebAI Chat, a helpful assistant for [Company]. "
        "Answer ONLY from the provided documents. "
        "DO NOT generate stories, creative content, or any information not found in the provided documents. "
        "DO NOT make up answers, DO NOT hallucinate, DO NOT use general knowledge. "
        "If the answer is not in the provided documents, reply EXACTLY with: "
        "'I don't have that information in the provided documents.'"
    )
    max_tokens: int = 1000
    top_k: int = 5


class CrawlerConfig(BaseModel):
    rate_limit: float = 1.0
    skip_patterns: List[str] = ["/login", "/admin", "/contact", "/careers"]


class WidgetConfig(BaseModel):
    position: str = "bottom-right"
    color: str = "#1a73e8"
    logo: str = ""
    greeting: str = "Hi! How can I help you?"
    theme: str = "blue"
    company_name: str = ""
    button_shape: str = "circle"
    button_size: str = "medium"
    corner_radius: int = 16
    font_family: str = "system"
    animation_speed: str = "normal"
    show_quick_replies: bool = True
    quick_replies: List[str] = ["What services do you offer?", "Contact information", "Pricing", "FAQ"]
    show_emoji_picker: bool = True
    show_source_citations: bool = True
    typing_animation: str = "dots"
    avatar_style: str = "icon"
    unread_count: bool = True
    auto_open_delay: int = 0
    status: str = "online"
    show_timestamps: bool = False
    minimize_to_icon: bool = False
    show_admin_button: bool = True
    customCSS: str = ""


class LoggingConfig(BaseModel):
    level: str = "INFO"


class AppConfig(BaseModel):
    server: ServerConfig = ServerConfig()
    ollama: OllamaConfig = OllamaConfig()
    cloud: CloudConfig = CloudConfig()
    chat: ChatConfig = ChatConfig()
    crawler: CrawlerConfig = CrawlerConfig()
    widget: WidgetConfig = WidgetConfig()
    logging: LoggingConfig = LoggingConfig()


def load_config(path: str | None = None) -> AppConfig:
    if path is None:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
    if not os.path.exists(path):
        return AppConfig()
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return AppConfig()
    # Replace empty strings with defaults for Ollama config
    if "ollama" in data:
        for key in ["model", "embedding_model", "url"]:
            if data["ollama"].get(key) == "" or data["ollama"].get(key) is None:
                default_val = OllamaConfig().model if key == "model" else \
                              OllamaConfig().embedding_model if key == "embedding_model" else \
                              OllamaConfig().url
                data["ollama"][key] = default_val
        # Fix embedding model name - Ollama uses "nomic-embed-text:latest" but SentenceTransformer needs "nomic-ai/nomic-embed-text-v1"
        if data["ollama"].get("embedding_model") == "nomic-embed-text:latest":
            data["ollama"]["embedding_model"] = "nomic-ai/nomic-embed-text-v1"
        elif data["ollama"].get("embedding_model") == "all-MiniLM-L6-v2:latest":
            data["ollama"]["embedding_model"] = "all-MiniLM-L6-v2"
    return AppConfig(**data)


_config_instance = load_config()


def reload_config() -> AppConfig:
    """Reload config from disk (call after saving settings)."""
    global _config_instance
    _config_instance = load_config()
    return _config_instance


class ConfigProxy:
    """Proxy that always returns the latest config values."""
    def __getattr__(self, name):
        return getattr(_config_instance, name)


config = ConfigProxy()
