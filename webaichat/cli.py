import os
import sys
import subprocess
import argparse
import yaml

from .utils import logger, DATA_DIR


def ensure_ollama_model(model: str):
    try:
        import ollama
        models = ollama.list()
        model_names = [m.name for m in models.get("models", [])]
        if model not in model_names:
            print(f"Downloading model: {model} (this may take a few minutes)...")
            ollama.pull(model)
            print(f"Model {model} downloaded successfully.")
        else:
            print(f"Model {model} is already available.")
    except Exception as e:
        print(f"Warning: Could not check/download model: {e}")
        print("Make sure Ollama is running and the model is available.")


def get_mode_from_config():
    mode = os.environ.get("WEBAI_CHAT_MODE", "")
    if mode:
        return mode
    cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "config.yaml")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data and "chat" in data and "mode" in data["chat"]:
                return data["chat"]["mode"]
    return "local"


def main_cli():
    parser = argparse.ArgumentParser(description="WebAI Chat - AI Chatbot for Websites")
    subparsers = parser.add_subparsers(dest="command")

    serve_parser = subparsers.add_parser("serve", help="Start the WebAI Chat server")
    serve_parser.add_argument("--host", default=None, help="Server host")
    serve_parser.add_argument("--port", type=int, default=None, help="Server port")

    crawl_parser = subparsers.add_parser("crawl", help="Crawl a website")
    crawl_parser.add_argument("url", help="Website URL to crawl")
    crawl_parser.add_argument("--skip", nargs="*", default=None, help="URL patterns to skip")

    ingest_parser = subparsers.add_parser("ingest", help="Ingest text files from a directory")
    ingest_parser.add_argument("directory", help="Path to folder containing .txt/.md files")
    ingest_parser.add_argument("--source", default="manual", help="Source name for metadata (default: manual)")

    model_parser = subparsers.add_parser("model", help="Manage SLM model")
    model_parser.add_argument("action", choices=["pull", "check", "info"], help="Model action")
    model_parser.add_argument("--model", default=None, help="Model name")

    args = parser.parse_args()

    if args.command == "serve":
        from .config import config
        from .conversation import init_db
        import uvicorn

        init_db()

        host = args.host or config.server.host
        port = args.port or config.server.port

        mode = get_mode_from_config()

        if mode == "cloud":
            print(f"Mode: cloud ({config.cloud.provider}/{config.cloud.model})")
        elif mode == "hybrid":
            ensure_ollama_model(config.ollama.model)
            print(f"Mode: hybrid (Ollama first, fallback to {config.cloud.provider}/{config.cloud.model})")
        else:
            ensure_ollama_model(config.ollama.model)
            print(f"Mode: local (Ollama - {config.ollama.model})")

        print(f"Starting WebAI Chat on http://{host}:{port}")
        print(f"Admin panel: http://{host}:{port}/admin")
        print(f"Widget: http://{host}:{port}/")
        uvicorn.run("webaichat.main:app", host=host, port=port, reload=False)

    elif args.command == "crawl":
        from .config import config
        from .ingest import crawl_and_save_sync
        from .vector_store import VectorStore
        from .ingest import chunk_text

        docs_dir = os.path.join(DATA_DIR, "docs")
        output_dir = os.path.join(DATA_DIR, "crawled")
        os.makedirs(docs_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        print(f"Crawling {args.url}...")
        skip = args.skip or config.crawler.skip_patterns
        result = crawl_and_save_sync(
            base_url=args.url,
            skip_patterns=skip,
            rate_limit=config.crawler.rate_limit,
            docs_dir=docs_dir,
            output_dir=output_dir,
        )
        print(f"Crawled {result['pages_crawled']} pages")
        if result["errors"]:
            print(f"Errors: {result['errors']}")

        txt_files = [f for f in os.listdir(docs_dir) if f.endswith(".txt")]
        all_chunks = []
        for fname in txt_files:
            fpath = os.path.join(docs_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            chunks = chunk_text(content)
            for c in chunks:
                c["metadata"]["source"] = args.url
            all_chunks.extend(chunks)

        vector_store = VectorStore()
        vector_store.ingest(all_chunks)
        print(f"Indexed {len(all_chunks)} chunks")

    elif args.command == "ingest":
        from .ingest import chunk_text
        from .vector_store import VectorStore

        input_dir = args.directory
        if not os.path.isdir(input_dir):
            print(f"Error: '{input_dir}' is not a valid directory")
            sys.exit(1)

        supported_extensions = {".txt", ".md"}
        files = [
            f for f in os.listdir(input_dir)
            if os.path.isfile(os.path.join(input_dir, f))
            and os.path.splitext(f)[1].lower() in supported_extensions
        ]

        if not files:
            print(f"No .txt or .md files found in '{input_dir}'")
            sys.exit(1)

        print(f"Found {len(files)} file(s) in '{input_dir}'")

        all_chunks = []
        for fname in files:
            fpath = os.path.join(input_dir, fname)
            print(f"  Processing: {fname}")
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            chunks = chunk_text(content)
            for c in chunks:
                c["metadata"]["source"] = fname
            all_chunks.extend(chunks)
            print(f"    {len(chunks)} chunk(s) from {fname}")

        if not all_chunks:
            print("No chunks generated")
            sys.exit(0)

        vector_store = VectorStore()
        vector_store.ingest(all_chunks)
        print(f"\nIndexed {len(all_chunks)} chunks from {len(files)} file(s)")

    elif args.command == "model":
        import ollama
        model_name = args.model or "qwen2.5:3b"

        if args.action == "pull":
            ensure_ollama_model(model_name)
        elif args.action == "check":
            try:
                models = ollama.list()
                model_names = [m.name for m in models.get("models", [])]
                if model_name in model_names:
                    print(f"Model {model_name} is available.")
                else:
                    print(f"Model {model_name} is NOT available. Run: webaichat model pull --model {model_name}")
            except Exception as e:
                print(f"Error checking model: {e}")
        elif args.action == "info":
            try:
                models = ollama.list()
                for m in models.get("models", []):
                    print(f"  {m['name']} ({m.get('size', 0) // 1024 // 1024}MB)")
            except Exception as e:
                print(f"Error getting model info: {e}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main_cli()
