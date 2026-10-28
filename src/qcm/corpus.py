"""Gera o corpus de documentos (fichas por ano e por norma) a partir do warehouse + docs/ escritos à mão."""
from __future__ import annotations

from dataclasses import dataclass

from . import DOCS
from .warehouse import connect

MESES = "jan fev mar abr mai jun jul ago set out nov dez".split()


@dataclass
class Doc:
    id: str
    titulo: str
    texto: str
    fonte: str


def _fmt(v: float | None, casas: int = 2) -> str:
    if v is None:
        return "sem dado"
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fichas_ano() -> list[Doc]:
    with connect(read_only=True) as con:
        rows = con.execute("SELECT * FROM poder_compra_anual").fetchall()
    docs = []
    for ano, sal, gas, litros, bm, bigmacs in rows:
        partes = [f"Em {ano}, o salário mínimo médio no ano foi de R$ {_fmt(sal)}."]
        if gas:
            partes.append(
                f"O litro da gasolina C custou em média R$ {_fmt(gas, 3)} (média das UFs, ANP), "
                f"então um salário mínimo comprava cerca de {_fmt(litros, 1)} litros de gasolina."
            )
        if bm:
            partes.append(
                f"O Big Mac custava R$ {_fmt(bm)} no Brasil (The Economist), "
                f"o que dava cerca de {_fmt(bigmacs, 1)} Big Macs por salário mínimo."
            )
        docs.append(Doc(f"ano-{ano}", f"Poder de compra do salário mínimo em {ano}", " ".join(partes), "warehouse:poder_compra_anual"))
    return docs


def fichas_norma() -> list[Doc]:
    with connect(read_only=True) as con:
        rows = con.execute(
            """
            SELECT vigencia, valor, norma, lag(valor) OVER (ORDER BY vigencia) AS anterior
            FROM bronze_salario_minimo ORDER BY vigencia
            """
        ).fetchall()
    docs = []
    for vig, valor, norma, anterior in rows:
        ano, mes = vig.split("-")
        txt = f"A norma {norma} fixou o salário mínimo em R$ {_fmt(valor)} a partir de {MESES[int(mes) - 1]}/{ano}."
        if anterior:
            txt += f" O valor anterior era R$ {_fmt(anterior)}, um reajuste nominal de {_fmt((valor / anterior - 1) * 100, 1)}%."
        docs.append(Doc(f"norma-{vig}", f"{norma}: salário mínimo de R$ {_fmt(valor)}", txt, "snapshot:salario_minimo.csv"))
    return docs


def docs_manuais() -> list[Doc]:
    return [Doc(p.stem, p.stem, p.read_text(encoding="utf-8"), f"docs/{p.name}") for p in sorted(DOCS.glob("*.md"))]


def todos() -> list[Doc]:
    return fichas_ano() + fichas_norma() + docs_manuais()


def chunk(texto: str, tamanho: int = 700, sobreposicao: int = 120) -> list[str]:
    """Quebra por seção markdown e depois por janela de caracteres com sobreposição."""
    secoes = [s.strip() for s in texto.split("\n## ") if s.strip()]
    pedacos = []
    for s in secoes:
        if len(s) <= tamanho:
            pedacos.append(s)
            continue
        i = 0
        while i < len(s):
            fim = min(len(s), i + tamanho)
            corte = s.rfind(" ", i, fim) if fim < len(s) else fim
            corte = corte if corte > i else fim
            pedacos.append(s[i:corte].strip())
            if corte >= len(s):
                break
            i = max(corte - sobreposicao, i + 1)
    return pedacos
