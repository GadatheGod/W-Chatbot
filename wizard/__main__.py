"""Entry point for python -m wizard."""

import sys
import webbrowser
import uvicorn

from .main import app
from .system_check import get_available_port


def main():
    port = get_available_port(start_port=9000)
    url = f"http://localhost:{port}"
    print(f"Starting WebAI Chat Setup Wizard...")
    print(f"Opening browser at {url}")
    webbrowser.open(url)
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
