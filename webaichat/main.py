import os
import uuid
import json
import yaml
import secrets
import base64
import bcrypt
from typing import List, Optional
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse, Response, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from urllib.parse import unquote

from .config import config, reload_config
from .chat import ChatEngine
from .conversation import (
    create_session, add_message, get_messages,
    get_all_conversations, search_conversations,
    get_conversation_by_id,
    delete_conversation, export_conversations, get_stats, init_db,
)
from .vector_store import get_vector_store
from .ingest import crawl_and_save_sync
from .utils import logger, DATA_DIR, CHROMA_DIR

app = FastAPI(title="WebAI Chat", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chat_engine = ChatEngine()

# In-memory session store for admin authentication
admin_sessions = {}
ADMIN_SESSION_TIMEOUT = timedelta(hours=8)


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def is_admin_authenticated(request: Request) -> bool:
    if not config.server.username or not config.server.password:
        return True
    session_token = request.cookies.get("admin_session")
    if not session_token:
        return False
    if session_token in admin_sessions:
        session_data = admin_sessions[session_token]
        if datetime.fromisoformat(session_data["expires"]) > datetime.now():
            return True
        else:
            del admin_sessions[session_token]
    return False

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if config.server.username and config.server.password:
    _password_hash = get_password_hash(config.server.password)
else:
    _password_hash = None


def check_auth(request: Request):
    if not config.server.username or not config.server.password:
        return
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Basic "):
        raise HTTPException(status_code=401, detail="Authentication required")
    import base64
    try:
        credentials = base64.b64decode(auth[6:]).decode("utf-8")
        username, password = credentials.split(":", 1)
        if username != config.server.username or not verify_password(password, _password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class CrawlRequest(BaseModel):
    url: str
    skip_patterns: Optional[List[str]] = None


class UploadRequest(BaseModel):
    session_id: Optional[str] = None


@app.on_event("startup")
def startup():
    init_db()
    _auto_index_docs()
    logger.info("WebAI Chat started")


def _auto_index_docs():
    docs_dir = os.path.join(DATA_DIR, "docs")
    if not os.path.exists(docs_dir):
        return
    txt_files = [f for f in os.listdir(docs_dir) if f.endswith(".txt") or f.endswith(".md")]
    if not txt_files:
        return
    all_chunks = []
    for fname in txt_files:
        fpath = os.path.join(docs_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        from .ingest import chunk_text
        chunks = chunk_text(content)
        for c in chunks:
            c["metadata"]["source"] = fname
        all_chunks.extend(chunks)
    vector_store = get_vector_store()
    vector_store.ingest(all_chunks)
    logger.info(f"Auto-indexed {len(all_chunks)} chunks from {len(txt_files)} files")


# ── Admin Authentication ──────────────────────────────────────────────

def require_admin(request: Request):
    """Middleware-like dependency to require admin authentication."""
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")


@app.get("/login", response_class=HTMLResponse)
def login_page():
    """Render the login page."""
    return FileResponse(os.path.join(os.path.dirname(__file__), "..", "templates", "login.html"))


@app.post("/api/admin/login")
async def admin_login(request: Request):
    """Authenticate admin and create session."""
    body = await request.json()
    username = body.get("username", "")
    password = body.get("password", "")

    if not config.server.username or not config.server.password:
        return {"logged_in": True}

    if username != config.server.username:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if _password_hash is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not verify_password(password, _password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = generate_session_token()
    admin_sessions[token] = {
        "username": username,
        "expires": (datetime.now() + ADMIN_SESSION_TIMEOUT).isoformat()
    }

    response = HTMLResponse(content=json.dumps({"logged_in": True}))
    response.set_cookie(key="admin_session", value=token, httponly=True, max_age=28800)
    return response


@app.post("/api/admin/logout")
def admin_logout():
    """Clear admin session."""
    response = HTMLResponse(content=json.dumps({"logged_out": True}))
    response.delete_cookie(key="admin_session")
    return response


@app.get("/api/admin/check-auth")
def check_admin_auth(request: Request):
    """Check if admin is currently authenticated."""
    authenticated = is_admin_authenticated(request)
    return {"authenticated": authenticated}


@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request):
    """Render admin panel (requires authentication)."""
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/login", status_code=303)
    return FileResponse(os.path.join(os.path.dirname(__file__), "..", "templates", "admin.html"))


@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "..", "templates", "chat.html"))


@app.get("/chat", response_class=HTMLResponse)
def chat_page():
    return FileResponse(os.path.join(os.path.dirname(__file__), "..", "templates", "chat.html"))


@app.get("/sample-site")
@app.get("/sample-site.html")
def sample_site():
    return FileResponse(os.path.join(os.path.dirname(__file__), "..", "static", "sample-site.html"), media_type="text/html")


@app.post("/api/chat")
def chat(req: ChatRequest):
    if not req.session_id:
        req.session_id = str(uuid.uuid4())
        create_session(req.session_id)
    response = chat_engine.chat(req.session_id, req.message)
    return {"session_id": req.session_id, "response": response}


@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest):
    if not req.session_id:
        req.session_id = str(uuid.uuid4())
        create_session(req.session_id)

    async def event_generator():
        for token in chat_engine.stream_chat(req.session_id, req.message):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/admin/documents")
def admin_list_documents():
    docs_dir = os.path.join(DATA_DIR, "docs")
    crawled_dir = os.path.join(DATA_DIR, "crawled")
    documents = []
    crawled_files = []
    if os.path.exists(docs_dir):
        for f in os.listdir(docs_dir):
            fpath = os.path.join(docs_dir, f)
            if os.path.isfile(fpath):
                documents.append({
                    "name": f,
                    "size": os.path.getsize(fpath),
                    "modified": datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat(),
                    "type": "uploaded"
                })
    if os.path.exists(crawled_dir):
        for f in os.listdir(crawled_dir):
            fpath = os.path.join(crawled_dir, f)
            if os.path.isfile(fpath):
                crawled_files.append({
                    "name": f,
                    "size": os.path.getsize(fpath),
                    "modified": datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat(),
                    "type": "crawled"
                })
    return {"documents": documents, "crawled": crawled_files, "docs_dir": docs_dir, "crawled_dir": crawled_dir}


@app.get("/api/admin/open-folder")
def admin_open_folder(path: str):
    import subprocess
    try:
        subprocess.Popen(['explorer', path])
        return {"status": "ok", "message": f"Opened folder: {path}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/admin/clear-crawl")
def clear_crawl_data():
    import shutil
    import stat

    def remove_readonly(func, path, excinfo):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    try:
        # Clear docs directory
        docs_dir = os.path.join(DATA_DIR, "docs")
        if os.path.exists(docs_dir):
            shutil.rmtree(docs_dir, onerror=remove_readonly)
            os.makedirs(docs_dir, exist_ok=True)

        # Clear crawled directory
        crawled_dir = os.path.join(DATA_DIR, "crawled")
        if os.path.exists(crawled_dir):
            shutil.rmtree(crawled_dir, onerror=remove_readonly)
            os.makedirs(crawled_dir, exist_ok=True)

        # Clear in-memory vector store
        vector_store = get_vector_store()
        vector_store.clear()

        return {"status": "ok", "message": "All crawl data cleared"}
    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "trace": traceback.format_exc()}


@app.get("/api/sessions/{session_id}/messages")
def get_session_messages(session_id: str, limit: int = 50):
    messages = get_messages(session_id, limit)
    return {"messages": list(reversed(messages))}


@app.post("/api/crawl")
@app.post("/api/admin/crawl")
def crawl(req: CrawlRequest):
    try:
        import logging
        logger = logging.getLogger("webaichat")
        skip_patterns = config.crawler.skip_patterns if req.skip_patterns is None else req.skip_patterns
        docs_dir = os.path.join(DATA_DIR, "docs")
        output_dir = os.path.join(DATA_DIR, "crawled")
        os.makedirs(docs_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Crawling URL: {req.url}, skip_patterns: {skip_patterns}, rate_limit: {config.crawler.rate_limit}")
        logger.info(f"docs_dir: {docs_dir}, output_dir: {output_dir}")
        result = crawl_and_save_sync(
            base_url=req.url,
            skip_patterns=skip_patterns,
            rate_limit=config.crawler.rate_limit,
            docs_dir=docs_dir,
            output_dir=output_dir,
        )
        logger.info(f"Crawl result: {result}")
        logger.info(f"Files in docs_dir: {os.listdir(docs_dir)}")
        logger.info(f"Files in output_dir: {os.listdir(output_dir)}")
        vector_store = get_vector_store()
        txt_files = [f for f in os.listdir(docs_dir) if f.endswith(".txt")]
        logger.info(f"TXT files found: {txt_files}")
        all_chunks = []
        for fname in txt_files:
            fpath = os.path.join(docs_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            from .ingest import chunk_text
            chunks = chunk_text(content)
            for c in chunks:
                c["metadata"]["source"] = req.url
            all_chunks.extend(chunks)
        vector_store.ingest(all_chunks)
        result["chunks_indexed"] = len(all_chunks)
        return result
    except Exception as e:
        import traceback
        logger.error(f"Crawl error: {e}\n{traceback.format_exc()}")
        return {"status": "error", "message": str(e), "pages_crawled": 0, "chunks_indexed": 0, "errors": [str(e)]}


@app.post("/api/upload")
async def upload_file(request: Request):
    file = await request.form()
    if "file" not in file:
        raise HTTPException(status_code=400, detail="No file provided")
    uploaded_file = file["file"]
    docs_dir = os.path.join(DATA_DIR, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    filepath = os.path.join(docs_dir, uploaded_file.filename)
    with open(filepath, "wb") as f:
        content = await uploaded_file.read()
        f.write(content)
    from .ingest import extract_text_from_pdf, chunk_text
    text = ""
    if uploaded_file.filename.endswith(".pdf"):
        text = extract_text_from_pdf(filepath)
    elif uploaded_file.filename.endswith((".txt", ".md")):
        text = (await uploaded_file.read()).decode("utf-8")
    else:
        return {"error": "Unsupported file type. Use .pdf, .txt, or .md"}
    chunks = chunk_text(text)
    for c in chunks:
        c["metadata"]["source"] = uploaded_file.filename
    vector_store = get_vector_store()
    vector_store.ingest(chunks)
    return {"chunks_indexed": len(chunks)}


@app.get("/api/admin/conversations")
def admin_conversations(search: Optional[str] = None, limit: int = 100):
    if search:
        conversations = search_conversations(search, limit)
    else:
        conversations = get_all_conversations(limit)
    return {"conversations": conversations}


@app.get("/api/admin/conversations/{session_id}")
def admin_get_conversation(session_id: str):
    return get_conversation_by_id(session_id)


@app.delete("/api/admin/conversations/{session_id}")
def admin_delete_conversation(session_id: str):
    delete_conversation(session_id)
    return {"message": "Deleted"}


@app.get("/api/admin/export")
def admin_export(format: str = "json"):
    data = export_conversations(format)
    if format == "csv":
        from fastapi.responses import Response
        return Response(content=data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=conversations.csv"})
    from fastapi.responses import JSONResponse
    return JSONResponse(content=data)


@app.get("/api/admin/stats")
def admin_stats():
    stats = get_stats()
    vector_store = get_vector_store()
    stats["indexed_chunks"] = vector_store.count()
    return stats


@app.get("/api/admin/model-info")
def admin_model_info():
    try:
        import ollama
        models = ollama.list()
        return {"models": models}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/admin/health")
def admin_health():
    mode = os.environ.get("WEBAI_CHAT_MODE", "")
    if not mode:
        cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                import yaml
                data = yaml.safe_load(f)
                if data and "chat" in data and "mode" in data["chat"]:
                    mode = data["chat"]["mode"]
    if not mode:
        mode = "local"

    ollama_status = "skipped"
    model_loaded = None
    expected_model = None
    if mode in ("local", "hybrid"):
        try:
            import ollama
            models = ollama.list()
            model_list = models.models if hasattr(models, "models") else (models.get("models", []) if isinstance(models, dict) else [])
            model_names = []
            for m in model_list:
                if hasattr(m, "model"):
                    model_names.append(m.model)
                elif isinstance(m, dict):
                    model_names.append(m.get("name", ""))
            loaded_model = config.ollama.model
            if loaded_model in model_names:
                ollama_status = "ok"
                model_loaded = True
            else:
                ollama_status = "warning"
                model_loaded = False
        except Exception:
            ollama_status = "error"
            model_loaded = False
        expected_model = config.ollama.model

    cloud_status = "skipped"
    cloud_model = None
    cloud_error_msg = None
    if mode == "cloud" or mode == "hybrid":
        try:
            import litellm
            provider = config.cloud.provider
            if provider == "google":
                provider = "gemini"
            model_name = f"{provider}/{config.cloud.model}"
            kwargs = {
                "model": model_name,
                "messages": [{"role": 'user', "content": "ping"}],
                "max_tokens": 5,
            }
            if config.cloud.api_key:
                kwargs["api_key"] = config.cloud.api_key
            if config.cloud.base_url:
                kwargs["base_url"] = config.cloud.base_url
            response = litellm.completion(**kwargs)
            if response.choices and response.choices[0].message.content:
                cloud_status = "ok"
            else:
                cloud_status = "warning"
            cloud_model = config.cloud.model
        except Exception as e:
            cloud_model = config.cloud.model
            error_str = str(e).lower()
            if "rate" in error_str or "429" in error_str or "quota" in error_str or "exceeded" in error_str:
                cloud_status = "rate_limited"
                cloud_error_msg = str(e)[:200]
            elif "auth" in error_str or "unauthorized" in error_str or "401" in error_str or "forbidden" in error_str or "403" in error_str:
                cloud_status = "auth_failed"
                cloud_error_msg = "Invalid API key or authentication failed"
            else:
                cloud_status = "error"
                cloud_error_msg = str(e)[:200]

    vector_store = get_vector_store()
    return {
        "ollama": ollama_status,
        "model_loaded": model_loaded,
        "expected_model": expected_model,
        "cloud": cloud_status,
        "cloud_model": cloud_model,
        "cloud_error": cloud_error_msg,
        "mode": mode,
        "indexed_chunks": vector_store.count(),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/admin/source-stats")
def admin_source_stats():
    """Get indexed chunk counts grouped by source (file or website)."""
    vector_store = get_vector_store()
    source_stats = vector_store.get_source_stats()
    return {"sources": source_stats}


@app.get("/api/widget/health")
def widget_health():
    mode = os.environ.get("WEBAI_CHAT_MODE", "")
    if not mode:
        cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                import yaml
                data = yaml.safe_load(f)
                if data and "chat" in data and "mode" in data["chat"]:
                    mode = data["chat"]["mode"]
    if not mode:
        mode = "local"

    is_healthy = False
    status_text = "Offline"

    if mode in ("local", "hybrid"):
        try:
            import ollama
            models = ollama.list()
            model_list = models.models if hasattr(models, "models") else (models.get("models", []) if isinstance(models, dict) else [])
            model_names = []
            for m in model_list:
                if hasattr(m, "model"):
                    model_names.append(m.model)
                elif isinstance(m, dict):
                    model_names.append(m.get("name", ""))
            if config.ollama.model in model_names:
                is_healthy = True
                status_text = "Online"
        except Exception:
            pass

    if not is_healthy and (mode == "cloud" or mode == "hybrid"):
        try:
            import litellm
            provider = config.cloud.provider
            if provider == "google":
                provider = "gemini"
            model_name = f"{provider}/{config.cloud.model}"
            kwargs = {"model": model_name, "messages": [{"role": 'user', "content": "ping"}], "max_tokens": 5}
            if config.cloud.api_key:
                kwargs["api_key"] = config.cloud.api_key
            if config.cloud.base_url:
                kwargs["base_url"] = config.cloud.base_url
            response = litellm.completion(**kwargs)
            if response.choices and response.choices[0].message.content:
                is_healthy = True
                status_text = "Online"
        except Exception:
            pass

    return {"status": "online" if is_healthy else "busy", "text": status_text}


@app.get("/api/widget/config")
def widget_config():
    # Reload config to get latest settings
    reload_config()
    return {
        "position": config.widget.position,
        "color": config.widget.color,
        "logo": config.widget.logo,
        "greeting": config.widget.greeting,
        "theme": config.widget.theme,
        "company_name": config.widget.company_name,
        "button_shape": config.widget.button_shape,
        "button_size": config.widget.button_size,
        "show_quick_replies": config.widget.show_quick_replies,
        "quick_replies": config.widget.quick_replies,
        "show_emoji_picker": config.widget.show_emoji_picker,
        "show_source_citations": config.widget.show_source_citations,
        "typing_animation": config.widget.typing_animation,
        "avatar_style": config.widget.avatar_style,
        "unread_count": config.widget.unread_count,
        "corner_radius": getattr(config.widget, "corner_radius", 16),
        "font_family": getattr(config.widget, "font_family", "system"),
        "animation_speed": getattr(config.widget, "animation_speed", "normal"),
        "auto_open_delay": getattr(config.widget, "auto_open_delay", 0),
        "status": getattr(config.widget, "status", "online"),
        "show_timestamps": getattr(config.widget, "show_timestamps", False),
        "minimize_to_icon": getattr(config.widget, "minimize_to_icon", False),
        "show_admin_button": getattr(config.widget, "show_admin_button", True),
        "show_status": getattr(config.widget, "show_status", True),
        "customCSS": getattr(config.widget, "customCSS", ""),
    }


@app.post("/api/widget/config")
def widget_config_update(req: dict):
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if "widget" not in data:
            data["widget"] = {}
        widget_fields = ["position", "color", "logo", "greeting", "theme", "company_name",
                         "button_shape", "button_size", "corner_radius", "font_family",
                         "animation_speed", "typing_animation", "auto_open_delay", "status",
                         "show_quick_replies", "quick_replies", "show_emoji_picker",
                         "show_source_citations", "unread_count", "show_timestamps",
                         "minimize_to_icon", "show_admin_button", "customCSS", "avatar_style"]
        for field in widget_fields:
            if field in req and req[field] is not None:
                data["widget"][field] = req[field]
        with open(cfg_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False)
        # Reload config to apply changes immediately
        reload_config()
    return {"message": "Widget settings saved"}


@app.get("/favicon.ico")
def favicon():
    return FileResponse(os.path.join(STATIC_DIR, "favicon.svg"), media_type="image/svg+xml")


@app.get("/config.yaml")
def serve_config():
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="text/plain")
    return Response(content="Config not found", media_type="text/plain", status_code=404)


@app.get("/api/admin/mode")
def admin_mode():
    mode = os.environ.get("WEBAI_CHAT_MODE", "")
    if not mode:
        cfg_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                import yaml
                data = yaml.safe_load(f)
                if data and "chat" in data and "mode" in data["chat"]:
                    mode = data["chat"]["mode"]
    if not mode:
        mode = "local"
    return {
        "mode": mode,
        "ollama": {
            "url": config.ollama.url,
            "model": config.ollama.model,
        },
        "cloud": {
            "provider": config.cloud.provider,
            "model": config.cloud.model,
            "has_api_key": bool(config.cloud.api_key),
            "base_url": config.cloud.base_url,
        },
    }


@app.post("/api/admin/mode")
def admin_update_mode(req: dict):
    mode = req.get("mode", "local")
    if mode not in ("local", "cloud", "hybrid"):
        raise HTTPException(status_code=400, detail="Invalid mode")
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            data = {}
        if "chat" not in data:
            data["chat"] = {}
        data["chat"]["mode"] = mode
        with open(cfg_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False)
        reload_config()
    return {"message": f"Mode updated to {mode}", "mode": mode}


@app.get("/api/admin/settings")
def admin_get_settings():
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data
    return {}


@app.get("/api/admin/config/raw")
def admin_get_config_raw():
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            return {"config": f.read()}
    return {"config": ""}


@app.post("/api/admin/config/raw")
def admin_save_config_raw(req: dict):
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    try:
        data = yaml.safe_load(req.get("config", ""))
        if data is None:
            data = {}
        with open(cfg_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False)
        reload_config()
        return {"status": "ok", "message": "Configuration saved"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/admin/settings")
def admin_update_settings(req: dict):
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    data = {}
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if "ollama" in req:
            if "url" in req["ollama"]:
                data["ollama"]["url"] = req["ollama"]["url"]
            if "model" in req["ollama"]:
                data["ollama"]["model"] = req["ollama"]["model"]
            if "embedding_model" in req["ollama"]:
                data["ollama"]["embedding_model"] = req["ollama"]["embedding_model"]
        if "cloud" in req:
            if "provider" in req["cloud"]:
                data["cloud"]["provider"] = req["cloud"]["provider"]
            if "model" in req["cloud"]:
                data["cloud"]["model"] = req["cloud"]["model"]
            if "api_key" in req["cloud"]:
                data["cloud"]["api_key"] = req["cloud"]["api_key"]
            if "base_url" in req["cloud"]:
                data["cloud"]["base_url"] = req["cloud"]["base_url"]
        with open(cfg_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False)
    return {"message": "Settings saved", "config": data}


@app.post("/api/admin/settings/reset")
def admin_reset_settings():
    example_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml.example")
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    if os.path.exists(example_path):
        with open(example_path, "r", encoding="utf-8") as f:
            default_data = yaml.safe_load(f)
        with open(cfg_path, "w", encoding="utf-8") as f:
            yaml.dump(default_data, f, default_flow_style=False)
    return {"message": "Defaults restored"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.server.host, port=config.server.port)
