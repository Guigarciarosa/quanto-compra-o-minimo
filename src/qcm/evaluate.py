"""Avaliação offline da recuperação: hit@k sobre um conjunto de perguntas com o documento esperado."""
from __future__ import annotations

import json

from . import ROOT
from .rag import search


def run(k: int = 3) -> dict:
    casos = json.loads((ROOT / "eval" / "perguntas.json").read_text(encoding="utf-8"))
    acertos, detalhes = 0, []
    for c in casos:
        ids = [h.doc_id for h in search(c["pergunta"], k=k)]
        esperados = c["doc_esperado"] if isinstance(c["doc_esperado"], list) else [c["doc_esperado"]]
        ok = any(e in ids for e in esperados)
        acertos += ok
        detalhes.append({"pergunta": c["pergunta"], "esperado": c["doc_esperado"], "top": ids, "ok": ok})
    return {"k": k, "hit_rate": round(acertos / len(casos), 3), "n": len(casos), "detalhes": detalhes}
