"""System detection for the setup wizard."""

import platform
import subprocess
import socket
import os
import sys
from typing import Dict, List, Any, Optional


def get_python_version() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def get_os_info() -> Dict[str, str]:
    return {
        "name": platform.system(),
        "version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
    }


def get_available_port(start_port: int = 8080, max_port: int = 9000) -> int:
    for port in range(start_port, max_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return start_port


def check_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("0.0.0.0", port))
            return False
        except OSError:
            return True


def check_ollama_installed() -> Dict[str, Any]:
    result = {"installed": False, "url": "http://localhost:11434", "version": "", "error": ""}

    try:
        resp = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if resp.returncode == 0:
            result["installed"] = True
            result["version"] = resp.stdout.strip()
    except FileNotFoundError:
        result["installed"] = False
        result["error"] = "Ollama not found in PATH"
    except Exception as e:
        result["error"] = str(e)

    return result


def check_ollama_running() -> Dict[str, Any]:
    result = {"running": False, "models": [], "error": ""}

    try:
        import urllib.request
        import json

        url = "http://localhost:11434/api/tags"
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


def check_gpu() -> Dict[str, Any]:
    result = {"available": False, "type": "", "memory": "", "error": ""}

    os_name = platform.system()

    if os_name == "Linux":
        try:
            resp = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if resp.returncode == 0:
                result["available"] = True
                result["type"] = "NVIDIA"
                result["memory"] = resp.stdout.strip()
        except FileNotFoundError:
            pass
        except Exception as e:
            result["error"] = str(e)

    elif os_name == "Darwin":
        try:
            resp = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if resp.returncode == 0 and "Apple" in resp.stdout:
                result["available"] = True
                result["type"] = "Apple Silicon"
                result["memory"] = "Unified Memory"
        except Exception as e:
            result["error"] = str(e)

    return result


def check_dependencies() -> Dict[str, Any]:
    missing = []
    installed = []

    deps = [
        "fastapi", "uvicorn", "pydantic", "yaml", "aiohttp",
        "chromadb", "sentence_transformers", "pdfplumber",
        "beautifulsoup4", "lxml", "bcrypt", "ollama",
        "litellm",
    ]

    for dep in deps:
        try:
            __import__(dep.replace("-", "_"))
            installed.append(dep)
        except ImportError:
            missing.append(dep)

    return {
        "installed": installed,
        "missing": missing,
    }


def get_system_info() -> Dict[str, Any]:
    python_version = get_python_version()
    os_info = get_os_info()
    ollama_status = check_ollama_installed()
    ollama_running = check_ollama_running()
    gpu_info = check_gpu()
    deps_info = check_dependencies()
    default_port = get_available_port()
    port_8000_in_use = check_port_in_use(8000)
    port_8080_in_use = check_port_in_use(8080)

    return {
        "python_version": python_version,
        "os": os_info,
        "ollama": ollama_status,
        "ollama_running": ollama_running,
        "gpu": gpu_info,
        "dependencies": deps_info,
        "default_port": default_port,
        "ports": {
            "8000_in_use": port_8000_in_use,
            "8080_in_use": port_8080_in_use,
        },
    }
