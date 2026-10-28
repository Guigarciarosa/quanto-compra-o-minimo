"""Índice vetorial no próprio DuckDB (tabela chunks com FLOAT[]) e busca por similaridade de cosseno."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .corpus import chunk, todos
from .embeddings import HashingEmbedder, OllamaEmbedder, default_embedder
from .warehouse import connect


@dataclass
class Hit:
    doc_id: str
    titulo: str
    texto: str
    fonte: str
    score: float


def index(embedder=None) -> tuple[int, str]:
    embedder = embedder or default_embedder()
    linhas = [(d.id, d.titulo, c, d.fonte) for d in todos() for c in chunk(d.texto)]
    vetores = embedder.embed([f"{t}\n{c}" for _, t, c, _ in linhas])
    with connect() as con:
        con.execute(
            "CREATE OR REPLACE TABLE chunks (doc_id VARCHAR, titulo VARCHAR, texto VARCHAR, fonte VARCHAR, embedder VARCHAR, emb FLOAT[])"
        )
        con.executemany(
            "INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?)",
            [(*l, embedder.name, v.tolist()) for l, v in zip(linhas, vetores)],
        )
    return len(linhas), embedder.name


def _embedder_do_indice(nome: str):
    if nome.startswith("ollama:"):
        return OllamaEmbedder(model=nome.split(":", 1)[1])
    return HashingEmbedder()


def _termos_exatos(texto: str) -> set[str]:
    """Anos, valores e números de norma: o que busca vetorial costuma errar e busca lexical acerta."""
    return set(re.findall(r"\d[\d.,/]*\d|\d", texto))


def _rerank(pergunta: str, hits: list[Hit], peso: float = 0.5) -> list[Hit]:
    termos = _termos_exatos(pergunta)
    if not termos:
        return hits
    for h in hits:
        h.score += peso * len(termos & _termos_exatos(f"{h.titulo} {h.texto}")) / len(termos)
    return sorted(hits, key=lambda h: h.score, reverse=True)


def search(pergunta: str, k: int = 5, embedder=None, candidatos: int = 30) -> list[Hit]:
    """Busca híbrida: top-N por cosseno no DuckDB, depois rerank por termos exatos (anos, valores, normas)."""
    with connect(read_only=True) as con:
        nome = con.execute("SELECT any_value(embedder) FROM chunks").fetchone()[0]
        # a pergunta precisa ser vetorizada pelo mesmo modelo que indexou os chunks
        embedder = embedder or _embedder_do_indice(nome)
        q = embedder.embed([pergunta])[0].tolist()
        rows = con.execute(
            """
            SELECT doc_id, titulo, texto, fonte, list_cosine_similarity(emb, ?::FLOAT[]) AS score
            FROM chunks ORDER BY score DESC LIMIT ?
            """,
            [q, max(k, candidatos)],
        ).fetchall()
    return _rerank(pergunta, [Hit(*r) for r in rows])[:k]
