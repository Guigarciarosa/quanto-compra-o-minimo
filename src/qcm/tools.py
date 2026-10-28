"""Ferramentas expostas ao LLM (agente local e servidor MCP)."""
from __future__ import annotations

import re

from .rag import search
from .warehouse import SCHEMA_DOC, connect

MAX_LINHAS = 50


def consultar_sql(sql: str) -> str:
    """Executa um SELECT somente leitura no warehouse e devolve até 50 linhas em texto."""
    limpo = sql.strip().rstrip(";")
    if not re.match(r"(?is)^\s*(select|with)\b", limpo) or ";" in limpo:
        return "Erro: só é permitido um único SELECT/WITH."
    try:
        with connect(read_only=True) as con:
            cur = con.execute(limpo)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchmany(MAX_LINHAS)
    except Exception as e:  # o erro volta para o modelo corrigir a query
        return f"Erro SQL: {e}"
    linhas = [" | ".join(cols)] + [" | ".join("" if v is None else str(v) for v in r) for r in rows]
    return "\n".join(linhas)


def buscar_documentos(pergunta: str, k: int = 5) -> str:
    """Busca semântica no corpus (fichas por ano, por norma legal e notas de metodologia)."""
    hits = search(pergunta, k=k)
    return "\n\n".join(f"[{h.doc_id}] ({h.fonte}, score {h.score:.2f})\n{h.texto}" for h in hits)


def esquema() -> str:
    return SCHEMA_DOC


TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "consultar_sql",
            "description": "Roda um SELECT (DuckDB) para números exatos. " + SCHEMA_DOC,
            "parameters": {
                "type": "object",
                "properties": {"sql": {"type": "string", "description": "Uma única query SELECT"}},
                "required": ["sql"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_documentos",
            "description": "Busca trechos de contexto: normas que fixaram o salário mínimo, fichas anuais e metodologia/limitações das fontes.",
            "parameters": {
                "type": "object",
                "properties": {"pergunta": {"type": "string"}},
                "required": ["pergunta"],
            },
        },
    },
]

FUNCS = {"consultar_sql": consultar_sql, "buscar_documentos": buscar_documentos}
