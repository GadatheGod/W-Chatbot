"""WebAI Chat Setup Wizard - FastAPI server."""

import os
import sys
import json
import subprocess
import threading
import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yaml

from .system_check import get_system_info, check_ollama_running
from .config_generator import generate_config, save_config, load_config
from .deployment import generate_all_deployments
from .snippets import generate_all_snippets

BASE_DIR = Path(__file__).parent
app = FastAPI(title="WebAI Chat Setup Wizard", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Pydantic Models ──────────────────────────────────────────────────

class SystemInfoRequest(BaseModel):
    pass


class OllamaCheckRequest(BaseModel):
    ollama_url: str = "http://localhost:11434"


class ConfigSaveRequest(BaseModel):
    config: Dict[str, Any]


class DeployRequest(BaseModel):
    target: str = "docker"
    config: Dict[str, Any]


class SnippetRequest(BaseModel):
    api_base: str = "http://localhost:8000/"
    widget_config: Optional[Dict[str, Any]] = None
    page_title: str = "My Website"


class InstallRequest(BaseModel):
    config: Dict[str, Any]
    project_dir: str = ""
    start_server: bool = False


# ── Routes ───────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def wizard_page():
    return FileResponse(str(TEMPLATES_DIR / "wizard.html"))


@app.get("/api/system-info")
def api_system_info():
    return get_system_info()


@app.get("/api/ollama/models")
def api_ollama_models(ollama_url: str = "http://localhost:11434"):
    result = {"models": [], "error": "", "running": False}
    try:
        import urllib.request
        import urllib.error
        url = f"{ollama_url}/api/tags"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            result["running"] = True
            models = data.get("models", [])
            result["models"] = [
                {
                    "name": m.get("name", ""),
                    "size": m.get("size", 0),
                    "digest": m.get("digest", ""),
                }
                for m in models
            ]
    except Exception as e:
        result["error"] = str(e)
    return result


@app.post("/api/config/generate")
def api_config_generate(data: ConfigSaveRequest):
    cfg = data.config
    config = generate_config(
        mode=cfg.get("mode", "local"),
        server_host=cfg.get("server", {}).get("host", "0.0.0.0"),
        server_port=cfg.get("server", {}).get("port", 8000),
        server_username=cfg.get("server", {}).get("username", ""),
        server_password=cfg.get("server", {}).get("password", ""),
        ollama_url=cfg.get("ollama", {}).get("url", "http://localhost:11434"),
        ollama_model=cfg.get("ollama", {}).get("model", "qwen2.5:3b"),
        embedding_model=cfg.get("ollama", {}).get("embedding_model", "all-MiniLM-L6-v2"),
        cloud_provider=cfg.get("cloud", {}).get("provider", "openai"),
        cloud_model=cfg.get("cloud", {}).get("model", "gpt-4o-mini"),
        cloud_api_key=cfg.get("cloud", {}).get("api_key", ""),
        cloud_base_url=cfg.get("cloud", {}).get("base_url", ""),
        system_prompt=cfg.get("chat", {}).get("system_prompt", ""),
        max_tokens=cfg.get("chat", {}).get("max_tokens", 1000),
        top_k=cfg.get("chat", {}).get("top_k", 5),
        crawler_rate_limit=cfg.get("crawler", {}).get("rate_limit", 1.0),
        crawler_skip_patterns=cfg.get("crawler", {}).get("skip_patterns", ["/login", "/admin", "/contact", "/careers"]),
        widget_position=cfg.get("widget", {}).get("position", "bottom-right"),
        widget_color=cfg.get("widget", {}).get("color", "#1a73e8"),
        widget_logo=cfg.get("widget", {}).get("logo", ""),
        widget_greeting=cfg.get("widget", {}).get("greeting", "Hi! How can I help you?"),
        widget_theme=cfg.get("widget", {}).get("theme", "blue"),
        widget_company_name=cfg.get("widget", {}).get("company_name", ""),
        widget_button_shape=cfg.get("widget", {}).get("button_shape", "circle"),
        widget_button_size=cfg.get("widget", {}).get("button_size", "medium"),
        widget_corner_radius=cfg.get("widget", {}).get("corner_radius", 16),
        widget_font_family=cfg.get("widget", {}).get("font_family", "system"),
        widget_animation_speed=cfg.get("widget", {}).get("animation_speed", "normal"),
        widget_show_quick_replies=cfg.get("widget", {}).get("show_quick_replies", True),
        widget_quick_replies=cfg.get("widget", {}).get("quick_replies", ["What services do you offer?", "Contact information", "Pricing", "FAQ"]),
        widget_show_emoji_picker=cfg.get("widget", {}).get("show_emoji_picker", True),
        widget_show_source_citations=cfg.get("widget", {}).get("show_source_citations", True),
        widget_typing_animation=cfg.get("widget", {}).get("typing_animation", "dots"),
        widget_avatar_style=cfg.get("widget", {}).get("avatar_style", "icon"),
        widget_unread_count=cfg.get("widget", {}).get("unread_count", True),
        widget_auto_open_delay=cfg.get("widget", {}).get("auto_open_delay", 0),
        widget_status=cfg.get("widget", {}).get("status", "online"),
        widget_show_timestamps=cfg.get("widget", {}).get("show_timestamps", False),
        widget_minimize_to_icon=cfg.get("widget", {}).get("minimize_to_icon", False),
        widget_show_admin_button=cfg.get("widget", {}).get("show_admin_button", True),
        widget_custom_css=cfg.get("widget", {}).get("customCSS", ""),
        log_level=cfg.get("logging", {}).get("level", "INFO"),
    )
    return JSONResponse(content={"config": config, "yaml": yaml.dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True)})


@app.post("/api/config/save")
def api_config_save(data: ConfigSaveRequest):
    cfg = data.config
    config = generate_config(
        mode=cfg.get("mode", "local"),
        server_host=cfg.get("server", {}).get("host", "0.0.0.0"),
        server_port=cfg.get("server", {}).get("port", 8000),
        server_username=cfg.get("server", {}).get("username", ""),
        server_password=cfg.get("server", {}).get("password", ""),
        ollama_url=cfg.get("ollama", {}).get("url", "http://localhost:11434"),
        ollama_model=cfg.get("ollama", {}).get("model", "qwen2.5:3b"),
        embedding_model=cfg.get("ollama", {}).get("embedding_model", "all-MiniLM-L6-v2"),
        cloud_provider=cfg.get("cloud", {}).get("provider", "openai"),
        cloud_model=cfg.get("cloud", {}).get("model", "gpt-4o-mini"),
        cloud_api_key=cfg.get("cloud", {}).get("api_key", ""),
        cloud_base_url=cfg.get("cloud", {}).get("base_url", ""),
        system_prompt=cfg.get("chat", {}).get("system_prompt", ""),
        max_tokens=cfg.get("chat", {}).get("max_tokens", 1000),
        top_k=cfg.get("chat", {}).get("top_k", 5),
        crawler_rate_limit=cfg.get("crawler", {}).get("rate_limit", 1.0),
        crawler_skip_patterns=cfg.get("crawler", {}).get("skip_patterns", ["/login", "/admin", "/contact", "/careers"]),
        widget_position=cfg.get("widget", {}).get("position", "bottom-right"),
        widget_color=cfg.get("widget", {}).get("color", "#1a73e8"),
        widget_logo=cfg.get("widget", {}).get("logo", ""),
        widget_greeting=cfg.get("widget", {}).get("greeting", "Hi! How can I help you?"),
        widget_theme=cfg.get("widget", {}).get("theme", "blue"),
        widget_company_name=cfg.get("widget", {}).get("company_name", ""),
        widget_button_shape=cfg.get("widget", {}).get("button_shape", "circle"),
        widget_button_size=cfg.get("widget", {}).get("button_size", "medium"),
        widget_corner_radius=cfg.get("widget", {}).get("corner_radius", 16),
        widget_font_family=cfg.get("widget", {}).get("font_family", "system"),
        widget_animation_speed=cfg.get("widget", {}).get("animation_speed", "normal"),
        widget_show_quick_replies=cfg.get("widget", {}).get("show_quick_replies", True),
        widget_quick_replies=cfg.get("widget", {}).get("quick_replies", ["What services do you offer?", "Contact information", "Pricing", "FAQ"]),
        widget_show_emoji_picker=cfg.get("widget", {}).get("show_emoji_picker", True),
        widget_show_source_citations=cfg.get("widget", {}).get("show_source_citations", True),
        widget_typing_animation=cfg.get("widget", {}).get("typing_animation", "dots"),
        widget_avatar_style=cfg.get("widget", {}).get("avatar_style", "icon"),
        widget_unread_count=cfg.get("widget", {}).get("unread_count", True),
        widget_auto_open_delay=cfg.get("widget", {}).get("auto_open_delay", 0),
        widget_status=cfg.get("widget", {}).get("status", "online"),
        widget_show_timestamps=cfg.get("widget", {}).get("show_timestamps", False),
        widget_minimize_to_icon=cfg.get("widget", {}).get("minimize_to_icon", False),
        widget_show_admin_button=cfg.get("widget", {}).get("show_admin_button", True),
        widget_custom_css=cfg.get("widget", {}).get("customCSS", ""),
        log_level=cfg.get("logging", {}).get("level", "INFO"),
    )
    project_dir = data.config.get("project_dir", "")
    config_path = os.path.join(project_dir, "config.yaml") if project_dir else os.path.join(os.getcwd(), "config.yaml")
    success = save_config(config, config_path)
    return JSONResponse(content={"success": success, "path": config_path})


@app.post("/api/deploy/generate")
def api_deploy_generate(data: DeployRequest):
    target = data.target
    config = data.config
    project_dir = config.get("project_dir", "")
    deployments = generate_all_deployments(config, project_dir)
    files = {}
    if target == "all":
        for category, file_dict in deployments.items():
            for fname, content in file_dict.items():
                files[f"{category}/{fname}"] = content
    else:
        files = deployments.get(target, {})
    return JSONResponse(content={"files": files, "targets": list(deployments.keys())})


@app.post("/api/snippets/generate")
def api_snippets_generate(data: SnippetRequest):
    snippets = generate_all_snippets(
        api_base=data.api_base,
        widget_config=data.widget_config,
        page_title=data.page_title,
    )
    return JSONResponse(content={"snippets": snippets})


@app.post("/api/install")
def api_install(data: InstallRequest):
    config = data.config
    project_dir = data.project_dir or str(Path(__file__).parent.parent)
    start_server = data.start_server

    # Save config.yaml
    config_path = os.path.join(project_dir, "config.yaml")
    success = save_config(config, config_path)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save config.yaml")

    # Install dependencies
    requirements_path = os.path.join(project_dir, "requirements.txt")
    install_msgs: list[str] = []
    python_exe = sys.executable

    # Patch sample-site.html with correct port
    sample_site_path = os.path.join(project_dir, "static", "sample-site.html")
    if os.path.exists(sample_site_path):
        try:
            server_port = config.get("server", {}).get("port", 8000)
            with open(sample_site_path, "r", encoding="utf-8") as f:
                content = f.read()
            content = content.replace(
                'http://localhost:9000/',
                f'http://localhost:{server_port}/'
            )
            with open(sample_site_path, "w", encoding="utf-8") as f:
                f.write(content)
            install_msgs.append(f"sample-site.html patched with port {server_port}")
        except Exception as e:
            install_msgs.append(f"Warning: Failed to patch sample-site.html: {e}")

    if os.path.exists(requirements_path):
        try:
            proc = subprocess.run(
                [python_exe, "-m", "pip", "install", "-r", requirements_path, "-q"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if proc.returncode == 0:
                install_msgs.append("Dependencies installed successfully")
            else:
                install_msgs.append(f"Warning: pip install returned {proc.returncode}")
                if proc.stderr:
                    install_msgs.append(f"stderr: {proc.stderr[:500]}")
        except subprocess.TimeoutExpired:
            install_msgs.append("Warning: pip install timed out (may still be running)")
        except Exception as e:
            install_msgs.append(f"pip install error: {e}")

    # Install package
    try:
        proc = subprocess.run(
            [python_exe, "-m", "pip", "install", "-e", project_dir, "-q"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode == 0:
            install_msgs.append("WebAI Chat package installed successfully")
        else:
            install_msgs.append(f"Warning: pip install -e returned {proc.returncode}")
    except Exception as e:
        install_msgs.append(f"Package install error: {e}")

    # Generate deployment files
    deployments = generate_all_deployments(config, project_dir)
    deploy_files_saved = []
    for category, file_dict in deployments.items():
        for fname, content in file_dict.items():
            out_path = os.path.join(project_dir, fname)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            deploy_files_saved.append(f"{category}/{fname}")

    # Optionally start server
    server_started = False
    if start_server:
        try:
            server_port = config.get("server", {}).get("port", 8000)
            proc = subprocess.Popen(
                [python_exe, "-m", "webaichat", "serve", "--port", str(server_port)],
                cwd=project_dir,
            )
            server_started = True
            install_msgs.append(f"Server started on port {server_port} (PID: {proc.pid})")
        except Exception as e:
            install_msgs.append(f"Server start error: {e}")

    return JSONResponse(content={
        "success": success,
        "config_path": config_path,
        "install_messages": install_msgs,
        "deploy_files": deploy_files_saved,
        "server_started": server_started,
    })


@app.get("/api/health")
def api_health():
    return {"status": "ok", "wizard_version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    port = 8080
    print(f"Starting WebAI Chat Setup Wizard on http://localhost:{port}")
    webbrowser.open(f"http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
