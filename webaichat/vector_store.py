import os
import hashlib
import chromadb
from chromadb.config import Settings
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import yaml

from .utils import CHROMA_DIR, logger
from .config import config

_global_embedding_model = None
_vector_store_instance = None


def get_vector_store():
    """Get or create the singleton VectorStore instance."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance


class VectorStore:
    def __init__(self):
        self._embedding_model = None
        # Use in-memory client to avoid Windows file locking issues
        # Data is re-indexed on each server restart from data/docs/
        self.client = chromadb.Client(Settings(anonymized_telemetry=False))
        self.collection = self.client.get_or_create_collection("documents")
        self._persist_path = CHROMA_DIR

    @property
    def embedding_model(self):
        global _global_embedding_model
        if self._embedding_model is None:
            if _global_embedding_model is None:
                model_name = config.ollama.embedding_model or "all-MiniLM-L6-v2"
                logger.info(f"Loading embedding model: {model_name}")
                _global_embedding_model = SentenceTransformer(model_name)
                logger.info("Embedding model loaded")
            self._embedding_model = _global_embedding_model
        return self._embedding_model

    def ingest(self, chunks: List[dict]):
        if not chunks:
            logger.info("No chunks to ingest")
            return
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        contents = [c["content"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        embeddings = self.embedding_model.encode(contents).tolist()

        # Delete all existing data first
        try:
            self.collection.delete(where={"chunk_index": {"$gte": 0}})
        except Exception:
            pass

        self.collection.add(
            ids=ids,
            documents=contents,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        logger.info(f"Ingested {len(chunks)} chunks into vector store")

    def search(self, query: str, top_k: int = 5) -> List[dict]:
        try:
            collection = self.client.get_collection("documents")
        except Exception:
            return []
        if collection.count() == 0:
            return []
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )
        chunks = []
        for i in range(len(results["ids"][0])):
            chunks.append({
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })
        return chunks

    def clear(self):
        try:
            self.client.delete_collection("documents")
        except Exception:
            pass
        self.client.create_collection("documents")
        logger.info("Vector store cleared")

    def count(self) -> int:
        try:
            return self.client.get_collection("documents").count()
        except Exception:
            return 0

    def get_source_stats(self) -> dict:
        """Get chunk counts grouped by source."""
        try:
            collection = self.client.get_collection("documents")
            if collection.count() == 0:
                return {}
            results = collection.get(include=["metadatas"])
            source_counts = {}
            for i, metadata in enumerate(results["metadatas"] or []):
                source = metadata.get("source", "unknown")
                if source not in source_counts:
                    source_counts[source] = 0
                source_counts[source] += 1
            return source_counts
        except Exception:
            return {}
            results = collection.get(include=["metadatas"])
            source_counts = {}
            for i, metadata in enumerate(results["metadatas"] or []):
                source = metadata.get("source", "unknown")
                if source not in source_counts:
                    source_counts[source] = 0
                source_counts[source] += 1
            return source_counts
        except Exception:
            return {}
