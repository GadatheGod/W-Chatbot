"""Website injection snippet generator for the setup wizard."""

import json
from typing import Dict, Any, List, Optional


def generate_widget_snippet(
    api_base: str = "",
    widget_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    if widget_config is None:
        widget_config = {}

    if not api_base:
        api_base = "http://localhost:8000/"

    if not api_base.endswith("/"):
        api_base += "/"

    config_obj = {}
    if widget_config.get("position"):
        config_obj["position"] = widget_config["position"]
    if widget_config.get("color"):
        config_obj["color"] = widget_config["color"]
    if widget_config.get("logo"):
        config_obj["logo"] = widget_config["logo"]
    if widget_config.get("greeting"):
        config_obj["greeting"] = widget_config["greeting"]
    if widget_config.get("company_name"):
        config_obj["company_name"] = widget_config["company_name"]
    if widget_config.get("button_shape"):
        config_obj["button_shape"] = widget_config["button_shape"]
    if widget_config.get("button_size"):
        config_obj["button_size"] = widget_config["button_size"]
    if widget_config.get("show_quick_replies") is not None:
        config_obj["show_quick_replies"] = widget_config["show_quick_replies"]
    if widget_config.get("quick_replies"):
        config_obj["quick_replies"] = widget_config["quick_replies"]
    if widget_config.get("show_emoji_picker") is not None:
        config_obj["show_emoji_picker"] = widget_config["show_emoji_picker"]
    if widget_config.get("show_source_citations") is not None:
        config_obj["show_source_citations"] = widget_config["show_source_citations"]
    if widget_config.get("typing_animation"):
        config_obj["typing_animation"] = widget_config["typing_animation"]
    if widget_config.get("auto_open_delay"):
        config_obj["auto_open_delay"] = widget_config["auto_open_delay"]
    if widget_config.get("show_timestamps") is not None:
        config_obj["show_timestamps"] = widget_config["show_timestamps"]
    if widget_config.get("minimize_to_icon") is not None:
        config_obj["minimize_to_icon"] = widget_config["minimize_to_icon"]
    if widget_config.get("customCSS"):
        config_obj["customCSS"] = widget_config["customCSS"]

    config_json = ""
    if config_obj:
        import json
        config_json = json.dumps(config_obj, indent=2)

    snippet = f"""<!-- WebAI Chat Widget -->
<script>
  window.WEBAI_CHAT_CONFIG = {config_json if config_obj else '{}'};
  window.WEBAI_CHAT_CONFIG.apiBase = "{api_base}";
</script>
<script src="{api_base}static/widget.js"></script>"""

    return {
        "plain_html": snippet,
        "head_tag": f"""<head>
    <!-- WebAI Chat Widget -->
    <script>
      window.WEBAI_CHAT_CONFIG = {config_json if config_obj else '{}'};
      window.WEBAI_CHAT_CONFIG.apiBase = "{api_base}";
    </script>
    <script src="{api_base}static/widget.js"></script>
</head>""",
    }


def generate_wordpress_snippet(
    api_base: str = "",
    widget_config: Optional[Dict[str, Any]] = None,
) -> str:
    snippets = generate_widget_snippet(api_base, widget_config)
    plain = snippets["plain_html"]

    php_code = f"""<?php
/**
 * WebAI Chat Widget - WordPress Integration
 * 
 * Add this to your theme's functions.php file,
 * OR use a plugin like "Insert Headers and Footers"
 * to add the script to your site footer.
 */

function webaichat_enqueue_widget() {{
    ?>
{plain}
    <?php
}}
add_action('wp_footer', 'webaichat_enqueue_widget');
"""

    return php_code


def generate_react_snippet(
    api_base: str = "",
    widget_config: Optional[Dict[str, Any]] = None,
) -> str:
    snippets = generate_widget_snippet(api_base, widget_config)

    react_code = f"""import React, {{" useEffect "}} from "react";

export function WebAIChatWidget() {{
  useEffect(() => {{
    const config = {{" apiBase: '{api_base}' """
    if widget_config:
        import json
        for key, value in widget_config.items():
            if key in ("position", "color", "logo", "greeting", "company_name", "button_shape", "button_size", "show_quick_replies", "quick_replies", "show_emoji_picker", "show_source_citations", "typing_animation", "auto_open_delay", "show_timestamps", "minimize_to_icon"):
                react_code += f", {key}: {json.dumps(value)}"
    react_code += """ }};
    
    window.WEBAI_CHAT_CONFIG = config;
    
    const script = document.createElement('script');
    script.src = '{api_base}static/widget.js';
    script.async = true;
    document.body.appendChild(script);
    
    return () => {{
      document.body.removeChild(script);
    }};
  }}, []);
  
  return null;
}}

// Usage in your App:
// import { WebAIChatWidget } from './WebAIChatWidget';
// <WebAIChatWidget />"""

    return react_code


def generate_vue_snippet(
    api_base: str = "",
    widget_config: Optional[Dict[str, Any]] = None,
) -> str:
    snippets = generate_widget_snippet(api_base, widget_config)
    
    extra_config = ""
    if widget_config:
        extra_parts = []
        for key, value in widget_config.items():
            if key in ("position", "color", "logo", "greeting", "company_name", "button_shape", "button_size", "show_quick_replies", "quick_replies", "show_emoji_picker", "show_source_citations", "typing_animation", "auto_open_delay", "show_timestamps", "minimize_to_icon"):
                extra_parts.append(f"    {key}: {json.dumps(value)}")
        if extra_parts:
            extra_config = ",\n" + ",\n".join(extra_parts)
    
    base_code = f"""<script setup>
import {{ onMounted, onUnmounted }} from 'vue'

const scriptEl = {{ ref(null) }}

onMounted(() => {{
  window.WEBAI_CHAT_CONFIG = {{
    apiBase: '{api_base}'{extra_config}
  }}
  
  const script = document.createElement('script')
  script.src = '{api_base}static/widget.js'
  script.async = true
  scriptEl.value = script
  document.body.appendChild(script)
}})

onUnmounted(() => {{
  if (scriptEl.value) {{
    document.body.removeChild(scriptEl.value)
  }}
}}
</script>

<template>
  <!-- Widget renders automatically -->
</template>"""
    
    return base_code


def generate_custom_html_snippet(
    page_title: str = "My Website",
    api_base: str = "",
    widget_config: Optional[Dict[str, Any]] = None,
) -> str:
    snippets = generate_widget_snippet(api_base, widget_config)
    config_json = "{}"
    if widget_config:
        import json
        config_dict = {}
        for key, value in widget_config.items():
            if key in ("position", "color", "logo", "greeting", "company_name"):
                config_dict[key] = value
        config_json = json.dumps(config_dict)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        .hero {{ text-align: center; padding: 100px 20px; }}
        .hero h1 {{ font-size: 48px; margin-bottom: 16px; color: #333; }}
        .hero p {{ font-size: 20px; color: #666; }}
    </style>
</head>
<body>
    <div class="hero">
        <h1>{page_title}</h1>
        <p>Welcome to our website. Click the chat button to ask us anything!</p>
    </div>

    <!-- WebAI Chat Widget -->
    <script>
      window.WEBAI_CHAT_CONFIG = {config_json};
      window.WEBAI_CHAT_CONFIG.apiBase = "{api_base}";
    </script>
    <script src="{api_base}static/widget.js"></script>
</body>
</html>"""


def generate_all_snippets(
    api_base: str = "",
    widget_config: Optional[Dict[str, Any]] = None,
    page_title: str = "My Website",
) -> Dict[str, str]:
    snippets = generate_widget_snippet(api_base, widget_config)
    
    return {
        "widget": snippets["plain_html"],
        "wordpress": generate_wordpress_snippet(api_base, widget_config),
        "react": generate_react_snippet(api_base, widget_config),
        "vue": generate_vue_snippet(api_base, widget_config),
        "custom_html": generate_custom_html_snippet(page_title, api_base, widget_config),
    }
