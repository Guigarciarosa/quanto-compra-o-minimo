"""Agente com tool calling via Ollama: decide entre SQL (números) e RAG (contexto) e cita as fontes."""
from __future__ import annotations

import json
import os

import requests

from .embeddings import OLLAMA_URL, modelo_instalado
from .tools import FUNCS, TOOL_SPECS, buscar_documentos

CHAT_MODEL = os.getenv("QCM_CHAT_MODEL", "qwen2.5:7b")

SYSTEM = """Você é um analista de dados econômicos do Brasil. Responda em português, de forma curta.
Regras:
1. Para qualquer número, use a ferramenta consultar_sql. Nunca invente valores.
2. Para contexto (qual norma, metodologia, limitações), use buscar_documentos.
3. Termine com uma linha 'Fontes:' citando tabelas ou ids de documentos usados.
4. Se o dado não existir no warehouse, diga isso claramente."""


def ask(pergunta: str, model: str = CHAT_MODEL, max_passos: int = 6, verbose: bool = False) -> str:
    if not modelo_instalado(model):
        return "[modo offline: sem LLM, mostrando só a recuperação]\n\n" + buscar_documentos(pergunta, k=4)

    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": pergunta}]
    for _ in range(max_passos):
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": model, "messages": msgs, "tools": TOOL_SPECS, "stream": False, "options": {"temperature": 0}},
            timeout=600,
        )
        r.raise_for_status()
        msg = r.json()["message"]
        msgs.append(msg)
        calls = msg.get("tool_calls") or []
        if not calls:
            return msg.get("content", "")
        for c in calls:
            nome, args = c["function"]["name"], c["function"]["arguments"]
            if isinstance(args, str):
                args = json.loads(args)
            saida = FUNCS[nome](**args) if nome in FUNCS else f"Ferramenta desconhecida: {nome}"
            if verbose:
                print(f"\n>> {nome}({args})\n{saida[:800]}")
            msgs.append({"role": "tool", "name": nome, "content": saida})
    return "Não consegui concluir dentro do limite de passos."
