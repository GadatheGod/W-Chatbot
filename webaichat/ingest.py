import os
import re
import html
from pathlib import Path
from typing import List, Tuple
from datetime import datetime

import pdfplumber
import yaml
from bs4 import BeautifulSoup


def extract_text_from_pdf(filepath: str) -> str:
    text = ""
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def extract_text_from_html(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    soup = BeautifulSoup(content, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)
    text = html.unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[dict]:
    words = text.split()
    if len(words) <= chunk_size:
        return [{"content": text, "metadata": {"source": "", "chunk_index": 0}}]
    chunks = []
    i = 0
    chunk_index = 0
    while i < len(words):
        end = min(i + chunk_size, len(words))
        chunk = " ".join(words[i:end])
        chunks.append({
            "content": chunk,
            "metadata": {"source": "", "chunk_index": chunk_index},
        })
        chunk_index += 1
        i += chunk_size - overlap
    return chunks


def crawl_and_save(base_url: str, skip_patterns: list, rate_limit: float,
                   docs_dir: str, output_dir: str) -> dict:
    import aiohttp
    import asyncio
    from urllib.parse import urljoin, urlparse

    os.makedirs(output_dir, exist_ok=True)
    visited = set()
    to_visit = [base_url]
    saved_files = []
    errors = []
    all_text = ""

    async def fetch(url: str, session: aiohttp.ClientSession):
        nonlocal all_text
        try:
            await asyncio.sleep(rate_limit)
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    errors.append(f"{url}: {resp.status}")
                    return
                content_type = resp.headers.get("Content-Type", "")
                is_html = "text/html" in content_type or url.endswith(".html")
                if not is_html:
                    return
                raw = await resp.read()
                try:
                    html_content = raw.decode("utf-8")
                except UnicodeDecodeError:
                    html_content = raw.decode("utf-8", errors="replace")
                soup = BeautifulSoup(html_content, "lxml")
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                text = soup.get_text(separator="\n")
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                text = "\n".join(lines)
                text = html.unescape(text)
                text = re.sub(r"\n{3,}", "\n\n", text)
                parsed = urlparse(url)
                filename = parsed.path.strip("/").replace("/", "_") or "index"
                filename = re.sub(r"[^a-zA-Z0-9_-]", "_", filename) + ".html"
                filepath = os.path.join(output_dir, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(html_content)
                saved_files.append(filename)
                all_text += text + "\n"
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    if isinstance(href, str) and (href.startswith("#") or href.startswith("mailto:")):
                        continue
                    if not isinstance(href, str):
                        continue
                    full_url = urljoin(url, href)
                    parsed_full = urlparse(full_url)
                    if parsed_full.netloc != parsed.netloc:
                        continue
                    if full_url in visited:
                        continue
                    skip = False
                    for pattern in skip_patterns:
                        if pattern in full_url:
                            skip = True
                            break
                    if not skip:
                        to_visit.append(full_url)
        except Exception as e:
            errors.append(f"{url}: {str(e)}")

    async def run():
        async with aiohttp.ClientSession() as session:
            while to_visit:
                url = to_visit.pop(0)
                if url in visited:
                    continue
                visited.add(url)
                await fetch(url, session)

    asyncio.run(run())

    if all_text:
        chunks = chunk_text(all_text)
        for c in chunks:
            c["metadata"]["source"] = base_url
        with open(os.path.join(docs_dir, "crawled_text.txt"), "w", encoding="utf-8") as f:
            f.write(all_text)
    return {
        "url": base_url,
        "pages_crawled": len(saved_files),
        "files": saved_files,
        "errors": errors,
        "timestamp": datetime.now().isoformat(),
    }


def crawl_and_save_sync(base_url: str, skip_patterns: list, rate_limit: float,
                        docs_dir: str, output_dir: str) -> dict:
    return crawl_and_save(base_url, skip_patterns, rate_limit, docs_dir, output_dir)
