"""Embeddings: Ollama (nomic-embed-text) quando disponível; senão, hashing determinístico para rodar offline."""
from __future__ import annotations

import hashlib
import os
import re
import unicodedata

import numpy as np
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("QCM_EMBED_MODEL", "nomic-embed-text")


def _normalize(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


class HashingEmbedder:
    """Bag of words + trigramas de caracteres com hashing. Sem rede, sem modelo: bom para testes e CI."""

    name = "hashing-1024"

    def __init__(self, dim: int = 1024):
        self.dim = dim

    def _vec(self, text: str) -> np.ndarray:
        v = np.zeros(self.dim, dtype=np.float32)
        palavras = re.findall(r"\w+", _normalize(text))
        feats = palavras + [p[i : i + 3] for p in palavras if len(p) > 3 for i in range(len(p) - 2)]
        for f in feats:
            h = int(hashlib.md5(f.encode()).hexdigest(), 16)
            v[h % self.dim] += 1.0 if f in palavras else 0.3
        n = np.linalg.norm(v)
        return v / n if n else v

    def embed(self, textos: list[str]) -> np.ndarray:
        return np.stack([self._vec(t) for t in textos])


class OllamaEmbedder:
    def __init__(self, model: str = EMBED_MODEL, url: str = OLLAMA_URL):
        self.model, self.url, self.name = model, url, f"ollama:{model}"

    def embed(self, textos: list[str]) -> np.ndarray:
        r = requests.post(f"{self.url}/api/embed", json={"model": self.model, "input": textos}, timeout=300)
        r.raise_for_status()
        m = np.array(r.json()["embeddings"], dtype=np.float32)
        return m / np.linalg.norm(m, axis=1, keepdims=True)


def ollama_disponivel(url: str = OLLAMA_URL) -> bool:
    try:
        return requests.get(f"{url}/api/tags", timeout=2).ok
    except requests.RequestException:
        return False


def modelo_instalado(model: str, url: str = OLLAMA_URL) -> bool:
    try:
        nomes = [m["name"] for m in requests.get(f"{url}/api/tags", timeout=2).json().get("models", [])]
    except (requests.RequestException, ValueError):
        return False
    return any(n == model or n.startswith(f"{model}:") for n in nomes)


def default_embedder():
    if os.getenv("QCM_EMBEDDER") == "hashing" or not modelo_instalado(EMBED_MODEL):
        return HashingEmbedder()
    return OllamaEmbedder()
