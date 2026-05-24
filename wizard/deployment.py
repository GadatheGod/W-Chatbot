"""Deployment file generator for the setup wizard."""

import os
from typing import Dict, Any


def generate_docker_files(config: Dict[str, Any], project_dir: str) -> Dict[str, str]:
    server_port = config.get("server", {}).get("port", 8000)
    ollama_url = config.get("ollama", {}).get("url", "http://localhost:11434")

    dockerfile = f"""FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \\
    pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Install the package
RUN pip install -e .

# Create data directories
RUN mkdir -p /app/data/chroma /app/data/crawled /app/data/docs /app/data/conversations /app/data/logs

# Expose port
EXPOSE {server_port}

# Start the server
CMD ["python", "-m", "webaichat", "serve"]
"""

    docker_compose = f"""version: "3.8"

services:
  webaichat:
    build: .
    ports:
      - "{server_port}:{server_port}"
    volumes:
      - ./config.yaml:/app/config.yaml
      - ./data:/app/data
    environment:
      - OLLAMA_HOST={ollama_url.replace("http://", "").replace(":11434", "")}
    restart: unless-stopped

  # Uncomment below if you want Ollama running in Docker
  # ollama:
  #   image: ollama/ollama
  #   ports:
  #     - "11434:11434"
  #   volumes:
  #     - ollama_data:/root/.ollama
  #   restart: unless-stopped

volumes:
  ollama_data:
"""

    env_example = f"""# WebAI Chat Environment Variables
OLLAMA_HOST={ollama_url.replace("http://", "").replace(":11434", "")}
OLLAMA_PORT=11434
WEBAI_CHAT_PORT={server_port}
"""

    docker_gitignore = """# Python
__pycache__/
*.py[cod]
*.egg-info/
venv/
.env

# Data
data/chroma/
data/conversations/
data/logs/

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db
"""

    return {
        "Dockerfile": dockerfile,
        "docker-compose.yml": docker_compose,
        ".env.example": env_example,
        ".dockerignore": docker_gitignore,
    }


def generate_systemd_service(config: Dict[str, Any], service_name: str = "webaichat") -> Dict[str, str]:
    server_port = config.get("server", {}).get("port", 8000)

    service_file = f"""[Unit]
Description=WebAI Chat Server
After=network.target

[Service]
Type=simple
User={os.environ.get('USER', 'www-data')}
WorkingDirectory=/opt/WebAI-Chat
ExecStart=/opt/WebAI-Chat/venv/bin/python -m webaichat serve --port {server_port}
Restart=always
RestartSec=5
Environment="PATH=/opt/WebAI-Chat/venv/bin:/usr/bin"

[Install]
WantedBy=multi-user.target
"""

    nginx_config = f"""server {{
    listen 80;
    server_name _;

    location / {{
        proxy_pass http://127.0.0.1:{server_port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }}
}}
"""

    install_script = f"""#!/bin/bash
# WebAI Chat Systemd Installation Script

echo "Installing WebAI Chat as a systemd service..."

# Copy service file
sudo cp webaichat.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable {service_name}

# Start the service
sudo systemctl start {service_name}

echo "Service installed and started!"
echo "Access WebAI Chat at: http://localhost:{server_port}"
echo "Check status: sudo systemctl status {service_name}"
echo "View logs: sudo journalctl -u {service_name} -f"
"""

    return {
        f"{service_name}.service": service_file,
        "nginx.conf": nginx_config,
        "install-service.sh": install_script,
    }


def generate_windows_startup(config: Dict[str, Any]) -> Dict[str, str]:
    server_port = config.get("server", {}).get("port", 8000)

    batch_file = f"""@echo off
REM WebAI Chat Startup Script
cd /d "%~dp0"
call venv\\Scripts\\activate
python -m webaichat serve --port {server_port}
pause
"""

    schtasks_script = f"""@echo off
REM Install WebAI Chat as a Windows Scheduled Task (runs at login)
schtasks /Create /TN "WebAI Chat" /TR "{os.getcwd()}\\start-webaichat.bat" /RU %USERNAME% /SC ONLOGON /F
echo Scheduled task created. WebAI Chat will start on login.
"""

    return {
        "start-webaichat.bat": batch_file,
        "install-schtasks.bat": schtasks_script,
    }


def generate_heroku_config(config: Dict[str, Any]) -> Dict[str, str]:
    server_port = config.get("server", {}).get("port", 8000)

    procfile = f"""web: gunicorn webaichat.main:app --bind 0.0.0.0:{server_port} --timeout 86400
"""

    runtime_txt = "python-3.11.0\n"

    return {
        "Procfile": procfile,
        "runtime.txt": runtime_txt,
    }


def generate_railway_config(config: Dict[str, Any]) -> Dict[str, str]:
    railway_toml = f"""[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python -m webaichat serve"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
"""

    return {
        "railway.toml": railway_toml,
    }


def generate_render_config(config: Dict[str, Any]) -> Dict[str, str]:
    server_port = config.get("server", {}).get("port", 8000)

    render_yaml = f"""services:
  - type: web
    name: webaichat
    env: python
    buildCommand: pip install -e .
    startCommand: python -m webaichat serve --port {server_port}
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
"""

    return {
        "render.yaml": render_yaml,
    }


def generate_all_deployments(config: Dict[str, Any], project_dir: str) -> Dict[str, Dict[str, str]]:
    return {
        "docker": generate_docker_files(config, project_dir),
        "systemd": generate_systemd_service(config),
        "windows": generate_windows_startup(config),
        "heroku": generate_heroku_config(config),
        "railway": generate_railway_config(config),
        "render": generate_render_config(config),
    }
