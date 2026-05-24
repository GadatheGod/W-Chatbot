# WebAI Chat — Installation & Configuration Guide

A complete step-by-step guide to install, configure, and deploy WebAI Chat on your own server.

---

## Table of Contents

1. [Overview](#1-overview)
2. [System Requirements](#2-system-requirements)
3. [Prerequisites](#3-prerequisites)
4. [Installation](#4-installation)
5. [Ollama Setup](#5-ollama-setup)
6. [Configuration](#6-configuration)
7. [Running the Server](#7-running-the-server)
8. [Crawling a Website](#8-crawling-a-website)
9. [Embedding the Widget](#9-embedding-the-widget)
10. [Admin Panel](#10-admin-panel)
11. [Deployment Modes Explained](#11-deployment-modes-explained)
12. [Cloud API Configuration (OpenAI / Azure)](#12-cloud-api-configuration-openai--azure)
13. [Hybrid Mode Setup](#13-hybrid-mode-setup)
14. [Production Deployment (systemd)](#14-production-deployment-systemd)
15. [Configuration Reference](#15-configuration-reference)
16. [API Endpoints](#16-api-endpoints)
17. [Troubleshooting](#17-troubleshooting)
18. [Customization](#18-customization)

---

## 1. Overview

WebAI Chat is a full-stack AI-powered website chatbot system that:

1. **Crawls** your website and extracts all content
2. **Indexes** the content using semantic embeddings (ChromaDB vector database)
3. **Responds** to visitor questions using a local or cloud language model (RAG — Retrieval Augmented Generation)
4. **Converts** visitors into leads with an embeddable floating chat widget

All data stays on your server — no third-party data scraping.

---

## 2. System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | Dual-core | 4+ cores |
| **RAM** | 8 GB | 16 GB |
| **GPU** | None (CPU only) | 4 GB VRAM (NVIDIA) |
| **Storage** | 4 GB | 10 GB |
| **OS** | Linux / Windows / macOS | Linux (Ubuntu 22.04+) |

### GPU Options

- **No GPU**: Runs on CPU — slower but functional (~2-5 tokens/sec)
- **NVIDIA GPU**: 4 GB VRAM minimum for Qwen2.5-3B (~15-30 tokens/sec)
- **Apple Silicon**: M1/M2/M3/M4 — excellent performance with Ollama

---

## 3. Prerequisites

### 3.1 Python 3.10+

```bash
# Check installed version
python --version

# Install on Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev

# Install on CentOS/RHEL
sudo yum install python3.10 python3.10-devel

# Install on macOS (via Homebrew)
brew install python@3.10

# Install on Windows
# Download from https://www.python.org/downloads/
```

### 3.2 Ollama (for local model)

Ollama is required if you plan to run the chatbot locally with an open-source LLM.

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS:**
```bash
# Download from https://ollama.ai or via Homebrew
brew install ollama
ollama serve
```

**Windows:**
```
# Download installer from https://ollama.ai
# Run the .exe installer
# Ollama runs as a background service
```

Verify Ollama is running:
```bash
ollama --version
# Expected output: ollama version 0.5.x
```

### 3.3 Git (optional, for cloning)

```bash
# Install on Ubuntu/Debian
sudo apt install git

# Install on macOS
brew install git

# Install on Windows
# Download from https://git-scm.com/download/win
```

---

## 4. Installation

### 4.1 Clone or Download the Project

```bash
# Option A: Clone from Git repository
git clone <your-repo-url>
cd WebAI-Chat

# Option B: If you have the project files locally
cd path/to/WebAI-Chat
```

### 4.2 Create a Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate

# Verify activation — you should see (venv) prefix in your terminal
```

### 4.3 Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Install the package itself (enables CLI commands)
pip install -e .
```

### 4.4 Verify Installation

```bash
# Check that the CLI command is available
webaichat --help

# Expected output:
# Usage: webaichat [OPTIONS] COMMAND [ARGS]...
#   WebAI Chat CLI
# Options:
#   --help  Show this message and exit.
# Commands:
#   serve    Start the WebAI Chat server
#   crawl    Crawl a website
#   model    Manage models (pull/list)
```

---

## 5. Ollama Setup

### 5.1 Start Ollama

```bash
# Linux/macOS (run as a service)
ollama serve &

# Or on macOS, launch via the app
# On Windows, Ollama runs automatically as a background service
```

### 5.2 Pull the Language Model

```bash
# Recommended: Qwen2.5-3B (balanced speed/quality, fits in 4GB VRAM)
ollama pull qwen2.5:3b

# Alternative models (larger = better quality, more VRAM needed):
ollama pull qwen2.5:7b      # ~5GB VRAM, better quality
ollama pull llama3.2:3b     # ~2GB VRAM, fast
ollama pull mistral:7b      # ~5GB VRAM, good all-rounder

# Verify model is available
ollama list
```

### 5.3 Embedding Model

Embedding models are loaded via `sentence-transformers` (not Ollama). They are downloaded automatically on first use and cached in `.cache/huggingface/`.

```bash
# Default embedding model: all-MiniLM-L6-v2
# Alternative: nomic-ai/nomic-embed-text-v1

# Configure in config.yaml:
# ollama:
#   embedding_model: "nomic-ai/nomic-embed-text-v1"
```

### 5.4 Test the Model

```bash
# Quick test — ask a simple question
ollama run qwen2.5:3b "What is 2+2?"

# Expected output: "2 + 2 equals 4."
```

---

## 6. Configuration

### 6.1 Create Configuration File

```bash
# Copy the example config
cp config.yaml.example config.yaml
```

### 6.2 Edit Configuration

Open `config.yaml` in your preferred editor:

```bash
nano config.yaml          # Linux/macOS
notepad config.yaml       # Windows
```

### 6.3 Configuration Walkthrough

Here is the full `config.yaml` with explanations for each section:

```yaml
# ───────────────────────────────────────────────
# SERVER SETTINGS
# ───────────────────────────────────────────────
server:
  host: "0.0.0.0"        # Bind to all network interfaces (0.0.0.0)
                          # Use "127.0.0.1" for local-only access
  port: 9000             # Port the server listens on
  username: ""           # Admin username (leave empty to disable auth)
  password: ""           # Admin password (leave empty to disable auth)

# ───────────────────────────────────────────────
# DEPLOYMENT MODE
# ───────────────────────────────────────────────
# Options: "local", "cloud", "hybrid"
chat:
  mode: "local"          # See Section 11 for mode details
  system_prompt: >
    You are WebAI Chat, a helpful assistant.
    Answer only from the provided documents.
    If you don't know the answer, say:
    "I don't have that information in the provided documents."
  max_tokens: 1000       # Maximum tokens in a response
  top_k: 5               # Number of relevant document chunks to retrieve

# ───────────────────────────────────────────────
# OLLAMA SETTINGS (local mode)
# ───────────────────────────────────────────────
ollama:
  url: "http://localhost:11434"  # Ollama API endpoint
  model: "qwen2.5:3b"           # Language model for chat responses
  embedding_model: "all-MiniLM-L6-v2"  # Embedding model (SentenceTransformer)

# ───────────────────────────────────────────────
# CLOUD API SETTINGS (cloud/hybrid mode)
# ───────────────────────────────────────────────
cloud:
  provider: "openai"       # openai, anthropic, azure, google, together, groq
  model: "gpt-4o-mini"     # Model to use
  api_key: ""              # Your API key (required)
  base_url: ""             # Custom API endpoint (optional, for Azure/compatible APIs)

# ───────────────────────────────────────────────
# WEB CRAWLER SETTINGS
# ───────────────────────────────────────────────
crawler:
  rate_limit: 1.0          # Seconds between requests (avoid overloading target site)
  skip_patterns:           # URL patterns to skip during crawling
    - "/login"
    - "/admin"
    - "/contact"
    - "/careers"

# ───────────────────────────────────────────────
# CHAT WIDGET SETTINGS
# ───────────────────────────────────────────────
widget:
  position: "bottom-right"        # Widget position
  color: "#1a73e8"                # Primary brand color (hex)
  logo: ""                        # URL to your company logo image
  greeting: "Hi! How can I help you?"  # Greeting text
  theme: "blue"                   # Visual theme: blue, gradient, etc.
  company_name: "FlowXplore"      # Your company name shown in widget
  button_shape: "circle"          # Button shape: circle, square, rounded
  button_size: "medium"           # Button size: small, medium, large
  corner_radius: 16               # Corner radius
  font_family: "system"           # Font family
  animation_speed: "normal"       # Animation speed: fast, normal, slow
  show_quick_replies: true        # Show suggested reply buttons
  quick_replies:                  # Suggested questions for visitors
    - "What services do you offer?"
    - "Contact information"
    - "Pricing"
    - "FAQ"
  show_emoji_picker: true         # Allow emoji in messages
  show_source_citations: true     # Show source document links in responses
  typing_animation: "dots"        # Typing indicator: dots, wave
  avatar_style: "icon"            # Bot avatar style
  unread_count: true              # Show unread message count badge
  auto_open_delay: 0              # Auto-open widget after N seconds (0 = disabled)
  status: "online"                # Status indicator
  show_timestamps: false          # Show message timestamps
  minimize_to_icon: false         # Minimize to floating icon
  show_admin_button: true         # Show admin panel link in widget
  customCSS: ""                   # Custom CSS injection

# ───────────────────────────────────────────────
# LOGGING
# ───────────────────────────────────────────────
logging:
  level: "INFO"   # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### 6.4 Minimal Configuration

If you just want to get started quickly, this is the minimum config needed:

```yaml
server:
  host: "0.0.0.0"
  port: 9000

chat:
  mode: "local"
  system_prompt: "You are a helpful assistant. Answer only from provided documents."
  max_tokens: 1000
  top_k: 5

ollama:
  url: "http://localhost:11434"
  model: "qwen2.5:3b"
  embedding_model: "nomic-embed-text:latest"
```

---

## 7. Running the Server

### 7.1 Start the Server

```bash
# Activate virtual environment first (if not already active)
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# Start the server
webaichat serve

# Or specify host/port directly
webaichat serve --host 0.0.0.0 --port 9000

# Or use the Python module directly
python -m webaichat serve
```

### 7.2 Expected Output

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:9000 (Press CTRL+C to quit)
```

### 7.3 Verify Server is Running

Open your browser and navigate to:

```
http://localhost:9000/static/sample-site.html
```

You should see the sample website with the WebAI Chat widget in the bottom-right corner.

### 7.4 Stop the Server

```
Press Ctrl+C in the terminal
```

---

## 8. Crawling a Website

### 8.1 Via CLI

```bash
# Crawl a website (requires server to be running)
webaichat crawl https://example.com

# Crawl with custom skip patterns
webaichat crawl https://example.com --skip /login /admin /contact
```

### 8.2 Via API

```bash
# Start a crawl
curl -X POST http://localhost:9000/api/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Expected response:
# {
#   "url": "https://example.com",
#   "pages_crawled": 5,
#   "files": ["index.html", "about.html"],
#   "errors": [],
#   "chunks_indexed": 23,
#   "timestamp": "2026-01-15T10:30:00"
# }
```

### 8.3 Via Admin Panel

1. Open `http://localhost:9000/admin`
2. Go to the **Crawl** tab
3. Enter the URL to crawl
4. Optionally specify URLs to skip
5. Click **Start Crawl**
6. Monitor progress in real-time

### 8.4 Upload Documents Manually

```bash
# Upload a PDF, TXT, or MD file
curl -X POST http://localhost:9000/api/upload \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/document.pdf"

# Expected response:
# {
#   "chunks_indexed": 15
# }
```

Or via the Admin Panel:
1. Open `http://localhost:9000/admin`
2. Go to the **Crawl** tab
3. Scroll to the **Upload** section
4. Select a file (PDF, TXT, or MD)
5. Click **Upload**

### 8.5 Crawl Output

Crawled content is stored in:
- **Raw HTML files**: `data/crawled/` (downloaded HTML files)
- **Extracted text**: `data/docs/crawled_text.txt` (extracted text content)
- **Vector store**: In-memory ChromaDB — re-indexed from `data/docs/` on server restart
- **Uploaded documents**: `data/docs/`

---

## 9. Embedding the Widget

### 9.1 Add to Your Website

Add these two lines before the closing `</body>` tag of any HTML page:

```html
<script>
  window.WEBAI_CHAT_CONFIG = { apiBase: "http://localhost:9000/" };
</script>
<script src="http://localhost:9000/static/widget.js"></script>
```

### 9.2 For Production (Remote Server)

```html
<script>
  window.WEBAI_CHAT_CONFIG = { apiBase: "https://chat.yourcompany.com/" };
</script>
<script src="https://chat.yourcompany.com/static/widget.js"></script>
```

### 9.3 Widget Configuration Options

The widget supports extensive customization via `config.yaml` or the Admin Panel **Widget** tab:

| Setting | Default | Description |
|---------|---------|-------------|
| `position` | `bottom-right` | Widget position: `bottom-right`, `bottom-left`, `top-right`, `top-left` |
| `color` | `#1a73e8` | Primary brand color (hex) |
| `logo` | `""` | URL to your company logo image |
| `greeting` | `Assistant` | Greeting text |
| `theme` | `blue` | Visual theme |
| `company_name` | `""` | Your company name |
| `button_shape` | `circle` | Button shape: `circle`, `square`, `rounded` |
| `button_size` | `medium` | Button size: `small`, `medium`, `large` |
| `corner_radius` | `16` | Corner radius |
| `font_family` | `system` | Font family |
| `animation_speed` | `normal` | Animation speed: `fast`, `normal`, `slow` |
| `show_quick_replies` | `true` | Show suggested reply buttons |
| `quick_replies` | `["What services do you offer?", ...]` | Suggested questions |
| `show_emoji_picker` | `true` | Allow emoji in messages |
| `show_source_citations` | `true` | Show source document links |
| `typing_animation` | `dots` | Typing indicator: `dots`, `wave` |
| `avatar_style` | `icon` | Bot avatar style |
| `unread_count` | `true` | Show unread message count badge |
| `auto_open_delay` | `0` | Auto-open widget after N seconds |
| `status` | `online` | Status indicator |
| `show_timestamps` | `false` | Show message timestamps |
| `minimize_to_icon` | `false` | Minimize to floating icon |
| `show_admin_button` | `true` | Show admin panel link in widget |
| `customCSS` | `""` | Custom CSS injection |

### 9.4 Supported Platforms

The widget works on **any website**:
- Plain HTML sites
- WordPress (add via Custom HTML block or footer script)
- React / Vue / Angular SPAs
- Shopify, Wix, Squarespace (via custom code injection)
- Any platform that allows custom JavaScript

---

## 10. Admin Panel

Navigate to `http://localhost:9000/admin` to access the admin dashboard.

### 10.1 Dashboard Overview

The admin panel provides:

| Tab | Function |
|-----|----------|
| **Dashboard** | System health, crawl status, conversation stats |
| **Crawl** | Start new crawls, view crawl history |
| **Conversations** | View, search, filter, and export all conversations |
| **Upload** | Manually upload documents (PDF, TXT, MD) |
| **Settings** | Configure widget appearance, LLM settings |
| **Health** | Check Ollama, database, and system status |

### 10.2 Conversation Management

- **Grouped by session** — conversations are organized by session
- **Expandable cards** — click to view full conversation history
- **Export options** — download conversations as TXT, CSV, or JSON
- **Delete** — remove individual conversations or clear all

### 10.3 System Health

The health endpoint (`/api/admin/health`) checks:
- Ollama connectivity
- Model availability
- Database status
- Crawler status

---

## 11. Deployment Modes Explained

### 11.1 Local Mode (`mode: "local"`)

**Everything runs on your server. No internet connection needed for AI responses.**

```yaml
chat:
  mode: "local"
```

**Pros:**
- 100% data privacy — no data leaves your server
- No API costs
- Works offline
- Full control

**Cons:**
- Requires GPU for good performance (or slower CPU inference)
- Model quality limited to open-source models
- Larger hardware requirements

**Best for:**
- Data-sensitive businesses (healthcare, legal, finance)
- Organizations with strict compliance requirements
- On-premise deployments

### 11.2 Cloud Mode (`mode: "cloud"`)

**Uses cloud APIs (OpenAI, Azure, etc.) for AI responses.**

```yaml
chat:
  mode: "cloud"

cloud:
  provider: "openai"
  model: "gpt-4o-mini"
  api_key: "sk-..."
```

**Pros:**
- Best-in-class model quality (GPT-4o, Claude, etc.)
- No GPU required
- Fast responses
- Lower hardware requirements

**Cons:**
- Data sent to third-party APIs
- Per-token costs
- Requires internet connection

**Best for:**
- Teams wanting GPT-4o quality
- Low-resource servers
- Prototyping and testing

### 11.3 Hybrid Mode (`mode: "hybrid"`)

**Tries local model first, falls back to cloud if unavailable.**

```yaml
chat:
  mode: "hybrid"
```

**Pros:**
- Best of both worlds
- Cost optimization (local for simple queries)
- Fallback reliability

**Cons:**
- More complex configuration
- Requires both Ollama and API key

**Best for:**
- Cost-conscious deployments
- High-availability requirements
- Mixed workload scenarios

---

## 12. Cloud API Configuration (OpenAI / Azure)

### 12.1 OpenAI

```yaml
chat:
  mode: "cloud"

cloud:
  provider: "openai"
  model: "gpt-4o-mini"
  api_key: "sk-your-api-key-here"
```

### 12.2 Azure OpenAI

```yaml
chat:
  mode: "cloud"

cloud:
  provider: "azure"
  model: "gpt-4o-mini"
  api_key: "your-azure-api-key"
  base_url: "https://your-resource.openai.azure.com/"
```

### 12.3 Other Providers

WebAI Chat uses LiteLLM under the hood, which supports many providers:

```yaml
# Anthropic (Claude)
cloud:
  provider: "anthropic"
  model: "claude-3-haiku-20240307"
  api_key: "sk-ant-..."

# Google (Gemini)
cloud:
  provider: "google"
  model: "gemini-pro"
  api_key: "your-google-api-key"

# Groq (fast inference)
cloud:
  provider: "groq"
  model: "llama3-8b-8192"
  api_key: "gsk-..."

# Together AI
cloud:
  provider: "together"
  model: "meta-llama/Llama-3-8b-chat-hf"
  api_key: "your-together-api-key"
```

---

## 13. Hybrid Mode Setup

### 13.1 Configuration

```yaml
chat:
  mode: "hybrid"
  system_prompt: "You are WebAI Chat, a helpful assistant. Answer only from provided documents."
  max_tokens: 1000
  top_k: 5

ollama:
  url: "http://localhost:11434"
  model: "qwen2.5:3b"
  embedding_model: "nomic-embed-text:latest"

cloud:
  provider: "openai"
  model: "gpt-4o-mini"
  api_key: "sk-your-api-key"
```

### 13.2 How It Works

1. User sends a message
2. System checks if Ollama is available
3. If Ollama is available → uses local model
4. If Ollama is unavailable → falls back to cloud API
5. Response is returned to the user

---

## 14. Production Deployment (systemd)

### 14.1 Create systemd Service File

```bash
sudo tee /etc/systemd/system/webaichat.service << 'EOF'
[Unit]
Description=WebAI Chat Server
After=network.target ollama.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/WebAI-Chat
ExecStart=/opt/WebAI-Chat/venv/bin/python -m webaichat serve
Restart=always
RestartSec=5
Environment="PATH=/opt/WebAI-Chat/venv/bin:/usr/bin"

[Install]
WantedBy=multi-user.target
EOF
```

### 14.2 Enable and Start the Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable webaichat

# Start the service
sudo systemctl start webaichat

# Check status
sudo systemctl status webaichat

# View logs
sudo journalctl -u webaichat -f
```

### 14.3 Nginx Reverse Proxy (Optional)

```bash
sudo tee /etc/nginx/sites-available/webaichat << 'EOF'
server {
    listen 80;
    server_name chat.yourcompany.com;

    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/webaichat /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 15. Docker Deployment

### 15.1 Create Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Install the package
RUN pip install -e .

# Expose port
EXPOSE 9000

# Start the server
CMD ["python", "-m", "webaichat", "serve"]
```

### 15.2 Create docker-compose.yml

```yaml
version: "3.8"

services:
  webaichat:
    build: .
    ports:
      - "9000:9000"
    volumes:
      - ./config.yaml:/app/config.yaml
      - ./data:/app/data
    environment:
      - OLLAMA_HOST=host.docker.internal:11434
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  ollama_data:
```

### 15.3 Build and Run

```bash
docker-compose up -d --build

# Check logs
docker-compose logs -f webaichat
```

Note: Embedding models are loaded automatically on first use from HuggingFace.

---

## 15. Configuration Reference

### 15.1 All Configuration Options

| Section | Key | Type | Default | Description |
|---------|-----|------|---------|-------------|
| **server** | host | string | `0.0.0.0` | Bind address |
| | port | int | `9000` | Port number |
| | username | string | `""` | Admin username |
| | password | string | `""` | Admin password |
| **chat** | mode | string | `local` | `local`, `cloud`, or `hybrid` |
| | system_prompt | string | (see below) | AI assistant instructions |
| | max_tokens | int | `1000` | Max response tokens |
| | top_k | int | `5` | Chunks to retrieve for RAG |
| **ollama** | url | string | `http://localhost:11434` | Ollama API URL |
| | model | string | `qwen2.5:3b` | LLM for chat |
| | embedding_model | string | `all-MiniLM-L6-v2` | Embedding model (SentenceTransformer) |
| **cloud** | provider | string | `openai` | API provider |
| | model | string | `gpt-4o-mini` | Cloud model |
| | api_key | string | `""` | API key |
| | base_url | string | `""` | Custom endpoint |
| **crawler** | rate_limit | float | `1.0` | Seconds between requests |
| | skip_patterns | list | (see below) | URL patterns to skip |
| **widget** | position | string | `bottom-right` | Widget position |
| | color | string | `#1a73e8` | Brand color (hex) |
| | logo | string | `""` | Logo URL |
| | greeting | string | `Hi! How can I help you?` | Greeting text |
| | theme | string | `blue` | Visual theme |
| | company_name | string | `""` | Company name |
| | button_shape | string | `circle` | Button shape |
| | button_size | string | `medium` | Button size |
| | corner_radius | int | `16` | Corner radius |
| | font_family | string | `system` | Font family |
| | animation_speed | string | `normal` | Animation speed |
| | show_quick_replies | bool | `true` | Show suggested replies |
| | quick_replies | list | (see below) | Suggested questions |
| | show_emoji_picker | bool | `true` | Allow emoji |
| | show_source_citations | bool | `true` | Show source links |
| | typing_animation | string | `dots` | Typing indicator |
| | avatar_style | string | `icon` | Bot avatar |
| | unread_count | bool | `true` | Show unread badge |
| | auto_open_delay | int | `0` | Auto-open delay (seconds) |
| | status | string | `online` | Status indicator |
| | show_timestamps | bool | `false` | Show timestamps |
| | minimize_to_icon | bool | `false` | Minimize to icon |
| | show_admin_button | bool | `true` | Show admin link |
| | customCSS | string | `""` | Custom CSS |
| **logging** | level | string | `INFO` | Log level |

### 15.2 Changing Configuration at Runtime

Configuration changes take effect immediately — no server restart needed. Changes are saved to `config.yaml` automatically.

To change settings:
1. Open the Admin Panel (`http://localhost:9000/admin`)
2. Go to **Settings** tab
3. Modify any setting
4. Click **Save**

Or edit `config.yaml` directly and reload the API via `/api/admin/settings`.

---

## 16. API Endpoints

### 16.1 Chat

```
POST /api/chat
Content-Type: application/json

{
  "message": "What services do you offer?",
  "session_id": "optional-session-id"
}

Response:
{
  "response": "We offer CAD, CAE, and PLM engineering services...",
  "session_id": "abc123"
}
```

### 16.2 Streaming Chat

```
POST /api/chat/stream
Content-Type: application/json

{
  "message": "What services do you offer?",
  "session_id": "optional-session-id"
}

Response: Server-sent events (SSE) stream
```

### 16.3 Crawl

```
POST /api/crawl
Content-Type: application/json

{
  "url": "https://example.com"
}

Response:
{
  "url": "https://example.com",
  "pages_crawled": 5,
  "files": ["index.html"],
  "errors": [],
  "chunks_indexed": 23,
  "timestamp": "..."
}
```

### 16.4 Upload Document

```
POST /api/upload
Content-Type: multipart/form-data

file: [PDF/TXT/MD file]

Response:
{
  "chunks_indexed": 15
}
```

### 16.5 Conversations

```
GET  /api/admin/conversations          # List all conversations
GET  /api/admin/conversations/{id}    # Get conversation details
DELETE /api/admin/conversations/{id}  # Delete a conversation
GET  /api/admin/export?format=json    # Export conversations
GET  /api/admin/export?format=csv     # Export as CSV
```

### 16.6 Health & Stats

```
GET /api/admin/health                # System health check
GET /api/admin/stats                 # Conversation statistics
GET /api/admin/model-info            # List Ollama models
GET /api/admin/source-stats          # Chunk counts by source
GET /api/admin/mode                  # Get deployment mode
POST /api/admin/mode                 # Update deployment mode
GET /api/admin/settings              # Get settings
POST /api/admin/settings             # Update settings
POST /api/admin/settings/reset       # Reset to defaults
GET /api/admin/config/raw            # Get raw config YAML
POST /api/admin/config/raw           # Save raw config YAML
GET /api/widget/config               # Widget configuration
POST /api/widget/config              # Update widget settings
GET /api/widget/health               # Widget health check
GET /api/admin/documents             # List documents
POST /api/admin/clear-crawl          # Clear crawl and upload data
GET /api/admin/open-folder           # Open data folder
GET /api/admin/check-auth            # Check auth status
POST /api/admin/login                # Login
POST /api/admin/logout               # Logout
GET /api/sessions/{id}/messages      # Get conversation history
```

---

## 18. Troubleshooting

### 18.1 Ollama Connection Refused

**Problem:** Server can't connect to Ollama

```
ERROR: Ollama connection failed: Connection refused
```

**Solution:**
```bash
# Check if Ollama is running
ollama list

# Start Ollama if not running
ollama serve &

# Check the URL in config.yaml matches your Ollama installation
# Default: http://localhost:11434
```

### 18.2 Model Not Found

**Problem:** The specified model is not pulled

```
ERROR: model 'qwen2.5:3b' not found
```

**Solution:**
```bash
# Pull the required model
ollama pull qwen2.5:3b

# Verify it's installed
ollama list
```

### 18.3 Out of Memory

**Problem:** Server crashes with memory errors

**Solution:**
```bash
# Use a smaller model
ollama pull qwen2.5:1.5b    # Even smaller model

# Or switch to cloud mode
# Edit config.yaml: chat.mode = "cloud"

# Increase system swap space (Linux)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 18.4 Crawler Not Working

**Problem:** Website crawling fails

**Solution:**
```bash
# Check the target URL is accessible
curl -I https://example.com

# Increase rate limit if getting blocked
# Edit config.yaml: crawler.rate_limit = 2.0

# Add URL to skip_patterns if it should be excluded
# Edit config.yaml: crawler.skip_patterns
```

### 18.5 Widget Not Showing

**Problem:** Chat widget doesn't appear on the website

**Solution:**
1. Check browser console for JavaScript errors (F12 → Console)
2. Verify the script tags are placed before `</body>`
3. Check CORS — the widget domain must match the API base URL
4. Hard refresh the page (Ctrl+Shift+R / Cmd+Shift+R)
5. Verify the API server is running: `http://localhost:9000/api/admin/health`

### 18.6 Responses Include Non-Document Content

**Problem:** Bot generates answers not based on crawled content

**Solution:**
```yaml
# Strengthen the system prompt in config.yaml
chat:
  system_prompt: >
    You are WebAI Chat, a helpful assistant for [Company].
    Answer ONLY from the provided documents.
    DO NOT generate stories, creative content, or any information
    not found in the provided documents.
    DO NOT make up answers, DO NOT hallucinate, DO NOT use general knowledge.
    If the answer is not in the provided documents, reply EXACTLY with:
    "I don't have that information in the provided documents."
```

### 18.7 Slow Responses

**Problem:** Chat responses take too long

**Solutions:**
1. Use a smaller model: `ollama pull qwen2.5:1.5b`
2. Add a GPU (4GB VRAM minimum)
3. Reduce `max_tokens` in config.yaml
4. Reduce `top_k` (fewer chunks to search)
5. Switch to cloud mode for faster inference

### 18.8 Port Already in Use

**Problem:** Another service is using port 9000

**Solution:**
```bash
# Find what's using the port
netstat -ano | findstr :9000        # Windows
lsof -i :9000                        # Linux/macOS

# Change the port in config.yaml
# server.port = 8080
```

### 18.9 Embedding Model Not Loading

**Problem:** Embedding model fails to load

**Solution:**
```bash
# Check network access to HuggingFace
# The embedding model is downloaded from HuggingFace automatically

# If behind a proxy, set environment variables:
# export HF_ENDPOINT=https://your-proxy.com

# Or configure a different model in config.yaml:
# ollama:
#   embedding_model: "all-MiniLM-L6-v2"
```

### 18.10 Widget Config Not Applied

**Problem:** Widget settings don't apply after saving

**Solution:**
```bash
# The server reloads config automatically when settings are saved
# Check the server logs for:
# INFO: webaichat - Config reloaded

# Verify the config file was updated:
cat config.yaml | grep -A 5 widget:

# Hard refresh the browser (Ctrl+Shift+R / Cmd+Shift+R)
```

---

## 19. Customization

### 19.1 Widget Colors and Branding

Edit `config.yaml`:

```yaml
widget:
  color: "#ff6b35"              # Your brand color
  company_name: "My Company"    # Your company name
  logo: "https://example.com/logo.png"  # Your logo URL
  greeting: "Welcome! How can we help?"  # Custom greeting
```

### 19.2 Custom Quick Replies

```yaml
widget:
  show_quick_replies: true
  quick_replies:
    - "What are your business hours?"
    - "Get a quote"
    - "Talk to sales"
    - "Support"
```

### 19.3 Custom CSS (Advanced)

You can inject custom CSS into the widget by modifying `static/widget.js` directly. Look for the CSS injection section near the top of the file.

### 19.4 Custom System Prompt

The system prompt controls how the AI behaves. Edit in `config.yaml`:

```yaml
chat:
  system_prompt: >
    You are a professional customer support assistant for Acme Corp.
    Your tone is friendly and professional.
    Answer ONLY from the provided documents.
    Keep responses concise (under 3 sentences).
    If the answer is not in the documents, say:
    "Let our team help you with that. Please contact us at info@acme.com"
```

### 19.5 Custom Crawl Patterns

```yaml
crawler:
  rate_limit: 2.0               # Slower crawling (2 seconds between requests)
  skip_patterns:
    - "/login"
    - "/admin"
    - "/api/*"
    - "/wp-admin/*"
    - "/blog/*"                 # Skip blog posts
```

---

## Appendix A: File Structure

```
WebAI-Chat/
├── config.yaml                  # Main configuration file
├── config.yaml.example          # Example configuration template
├── requirements.txt             # Python dependencies
├── setup.py                     # Package setup
├── README.md                    # Quick start guide
│
├── webaichat/                   # Python backend package
│   ├── __init__.py
│   ├── __main__.py              # CLI entry point
│   ├── main.py                  # FastAPI application
│   ├── chat.py                  # Chat engine
│   ├── config.py                # Configuration management
│   ├── conversation.py          # Conversation management
│   ├── ingest.py                # Document ingestion
│   ├── vector_store.py          # ChromaDB integration
│   ├── utils.py                 # Utility functions
│   └── cli.py                   # CLI commands
│
├── static/                      # Static files
│   ├── widget.js                # Chat widget JavaScript
│   ├── widget.html              # Widget demo page
│   ├── sample-site.html         # Sample demo website
│   └── favicon.svg              # Favicon
│
├── templates/                   # HTML templates
│   ├── chat.html                # Chat interface
│   ├── admin.html               # Admin panel
│   └── login.html               # Login page
│
├── data/                        # Runtime data
│   ├── chroma/                  # ChromaDB in-memory data
│   ├── crawled/                 # Crawled website content
│   ├── docs/                    # Uploaded documents
│   ├── conversations/           # Conversation data
│   ├── logs/                    # Log files
│   └── webaichat.db             # SQLite database
│
├── .cache/                      # HuggingFace model cache
│   └── huggingface/
│       └── hub/
│           └── models/          # Downloaded embedding models
│
├── webaichat.egg-info/          # Package metadata
│
└── venv/                        # Python virtual environment
```

---

## Appendix B: Model Comparison

### Language Models (Ollama)

| Model | Parameters | VRAM Required | Speed | Quality | Best For |
|-------|-----------|---------------|-------|---------|----------|
| qwen2.5:1.5b | 1.5B | ~1 GB | Very Fast | Good | Low-resource servers |
| qwen2.5:3b | 3B | ~2 GB | Fast | Very Good | **Recommended default** |
| qwen2.5:7b | 7B | ~5 GB | Moderate | Excellent | High-quality responses |
| llama3.2:3b | 3B | ~2 GB | Fast | Very Good | General purpose |
| mistral:7b | 7B | ~5 GB | Moderate | Excellent | Knowledge-intensive tasks |

### Embedding Models (SentenceTransformer)

| Model | Dimensions | Quality | Size | Best For |
|-------|-----------|---------|------|----------|
| all-MiniLM-L6-v2 | 384 | Good | ~80MB | **Default** - fast and lightweight |
| nomic-ai/nomic-embed-text-v1 | 768 | Very Good | ~270MB | Higher quality embeddings |

---

## Appendix C: Common Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| `Connection refused` | Ollama not running | Run `ollama serve` |
| `Model not found` | Model not pulled | Run `ollama pull <model>` |
| `Permission denied` | Port < 1024 without root | Use port >= 1024 or run with sudo |
| `ModuleNotFoundError` | Virtual env not activated | Run `source venv/bin/activate` |
| `SSL certificate verify failed` | Self-signed cert | Use HTTPS with valid cert or disable verify |
| `CORS error` | Domain mismatch | Ensure widget domain matches API base URL |
| `Disk space full` | Model/data too large | Free disk space or use smaller model |
| `OSError: [Errno 24] Too many open files` | File descriptor limit | Increase limit: `ulimit -n 65536` |
| `Embedding model failed` | HuggingFace access blocked | Check network or configure proxy |
| `Vector store empty` | No documents indexed | Crawl a website or upload documents |

---

## Appendix D: Security Recommendations

### For Production Deployments

1. **Enable Basic Authentication:**
   ```yaml
   server:
     username: "admin"
     password: "strong-password-here"
   ```

2. **Use HTTPS:**
   - Set up SSL/TLS with Let's Encrypt or a commercial CA
   - Use a reverse proxy (Nginx/Apache) with SSL termination

3. **Restrict Network Access:**
   ```yaml
   server:
     host: "127.0.0.1"  # Only allow local connections
   ```
   Then use a reverse proxy for external access.

4. **Regular Backups:**
   ```bash
   # Backup the data directory
   tar -czf webaichat-backup-$(date +%Y%m%d).tar.gz data/

   # Backup the config
   cp config.yaml config-backup.yaml
   ```

5. **Keep Dependencies Updated:**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

---

## Need Help?

- **Documentation:** See `README.md` for quick start
- **Configuration:** See `config.yaml.example` for all options
- **Admin Panel:** Navigate to `/admin` for dashboard and settings
- **API Docs:** Open `/docs` when server is running for Swagger API documentation

---

*Last updated: 2026*
*Version: 0.1.0*
