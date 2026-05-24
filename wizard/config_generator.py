"""Configuration file generator for the setup wizard."""

import os
import yaml
from typing import Dict, Any, Optional


def generate_config(
    mode: str = "local",
    server_host: str = "0.0.0.0",
    server_port: int = 8000,
    server_username: str = "",
    server_password: str = "",
    ollama_url: str = "http://localhost:11434",
    ollama_model: str = "qwen2.5:3b",
    embedding_model: str = "all-MiniLM-L6-v2",
    cloud_provider: str = "openai",
    cloud_model: str = "gpt-4o-mini",
    cloud_api_key: str = "",
    cloud_base_url: str = "",
    system_prompt: str = "",
    max_tokens: int = 1000,
    top_k: int = 5,
    crawler_rate_limit: float = 1.0,
    crawler_skip_patterns: list = None,
    widget_position: str = "bottom-right",
    widget_color: str = "#1a73e8",
    widget_logo: str = "",
    widget_greeting: str = "Hi! How can I help you?",
    widget_theme: str = "blue",
    widget_company_name: str = "",
    widget_button_shape: str = "circle",
    widget_button_size: str = "medium",
    widget_corner_radius: int = 16,
    widget_font_family: str = "system",
    widget_animation_speed: str = "normal",
    widget_show_quick_replies: bool = True,
    widget_quick_replies: list = None,
    widget_show_emoji_picker: bool = True,
    widget_show_source_citations: bool = True,
    widget_typing_animation: str = "dots",
    widget_avatar_style: str = "icon",
    widget_unread_count: bool = True,
    widget_auto_open_delay: int = 0,
    widget_status: str = "online",
    widget_show_timestamps: bool = False,
    widget_minimize_to_icon: bool = False,
    widget_show_admin_button: bool = True,
    widget_custom_css: str = "",
    log_level: str = "INFO",
) -> Dict[str, Any]:
    if crawler_skip_patterns is None:
        crawler_skip_patterns = ["/login", "/admin", "/contact", "/careers"]
    if widget_quick_replies is None:
        widget_quick_replies = [
            "What services do you offer?",
            "Contact information",
            "Pricing",
            "FAQ",
        ]

    if not system_prompt:
        system_prompt = (
            "You are WebAI Chat, a helpful assistant for [Company]. "
            "Answer ONLY from the provided documents. "
            "DO NOT generate stories, creative content, or any information not found in the provided documents. "
            "DO NOT make up answers, DO NOT hallucinate, DO NOT use general knowledge. "
            "If the answer is not in the provided documents, reply EXACTLY with: "
            "'I don't have that information in the provided documents.'"
        )

    config = {
        "server": {
            "host": server_host,
            "port": server_port,
            "username": server_username,
            "password": server_password,
        },
        "chat": {
            "mode": mode,
            "system_prompt": system_prompt,
            "max_tokens": max_tokens,
            "top_k": top_k,
        },
        "ollama": {
            "url": ollama_url,
            "model": ollama_model,
            "embedding_model": embedding_model,
        },
        "cloud": {
            "provider": cloud_provider,
            "model": cloud_model,
            "api_key": cloud_api_key,
            "base_url": cloud_base_url,
        },
        "crawler": {
            "rate_limit": crawler_rate_limit,
            "skip_patterns": crawler_skip_patterns,
        },
        "widget": {
            "position": widget_position,
            "color": widget_color,
            "logo": widget_logo,
            "greeting": widget_greeting,
            "theme": widget_theme,
            "company_name": widget_company_name,
            "button_shape": widget_button_shape,
            "button_size": widget_button_size,
            "corner_radius": widget_corner_radius,
            "font_family": widget_font_family,
            "animation_speed": widget_animation_speed,
            "show_quick_replies": widget_show_quick_replies,
            "quick_replies": widget_quick_replies,
            "show_emoji_picker": widget_show_emoji_picker,
            "show_source_citations": widget_show_source_citations,
            "typing_animation": widget_typing_animation,
            "avatar_style": widget_avatar_style,
            "unread_count": widget_unread_count,
            "auto_open_delay": widget_auto_open_delay,
            "status": widget_status,
            "show_timestamps": widget_show_timestamps,
            "minimize_to_icon": widget_minimize_to_icon,
            "show_admin_button": widget_show_admin_button,
            "customCSS": widget_custom_css,
        },
        "logging": {
            "level": log_level,
        },
    }

    if mode == "cloud":
        config["ollama"]["model"] = ""
        config["ollama"]["embedding_model"] = embedding_model
    elif mode == "hybrid":
        pass
    else:
        config["cloud"]["provider"] = ""
        config["cloud"]["model"] = ""
        config["cloud"]["api_key"] = ""
        config["cloud"]["base_url"] = ""

    return config


def save_config(config: Dict[str, Any], output_path: str) -> bool:
    try:
        if os.path.exists(output_path):
            backup_path = output_path + ".backup"
            with open(output_path, "r", encoding="utf-8") as f:
                existing = f.read()
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(existing)

        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def load_config(config_path: str) -> Optional[Dict[str, Any]]:
    try:
        if not os.path.exists(config_path):
            return None
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if data else {}
    except Exception as e:
        print(f"Error loading config: {e}")
        return None
