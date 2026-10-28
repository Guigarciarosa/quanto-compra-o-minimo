"""Baixa as fontes oficiais. Se a rede falhar, usa os snapshots versionados em data/snapshots."""
from __future__ import annotations

import csv
import io
import shutil

import requests

from . import RAW, SNAPSHOTS

# Série 1619 do SGS/Banco Central: salário mínimo mensal (R$).
BCB_SALARIO_MINIMO = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1619/dados?formato=json"
# Anuário Estatístico ANP 2026, tabela 3.20: preço médio da gasolina C por UF, 2016-2025.
ANP_GASOLINA = (
    "https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/arquivos/"
    "anuario-estatistico-2026/secao-3/anuario-2026-dados_abertos-tabela3-20.csv"
)
BIGMAC = "https://raw.githubusercontent.com/TheEconomist/big-mac-data/master/source-data/big-mac-source-data-v2.csv"


def _get(url: str) -> bytes:
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.content


def _fallback(name: str) -> str:
    shutil.copy(SNAPSHOTS / name, RAW / name)
    return f"{name}: snapshot"


def ingest_bigmac() -> str:
    try:
        (RAW / "bigmac_economist.csv").write_bytes(_get(BIGMAC))
        return "bigmac_economist.csv: The Economist (online)"
    except requests.RequestException:
        return _fallback("bigmac_economist.csv")


def ingest_gasolina() -> str:
    try:
        text = _get(ANP_GASOLINA).decode("utf-8-sig", errors="replace")
        rows = list(csv.reader(io.StringIO(text), delimiter=";"))[1:]
        with open(RAW / "gasolina_c_anp_uf.csv", "w", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["regiao", "uf", "ano", "preco_litro"])
            for regiao, uf, preco, ano in rows:
                w.writerow([regiao.replace("Região ", ""), uf, ano, preco.replace(",", ".")])
        return "gasolina_c_anp_uf.csv: ANP (online)"
    except (requests.RequestException, ValueError):
        return _fallback("gasolina_c_anp_uf.csv")


def ingest_salario_minimo() -> str:
    """A tabela de vigências (com a norma legal) é o snapshot; o BCB serve de checagem cruzada."""
    status = _fallback("salario_minimo.csv")
    try:
        serie = requests.get(BCB_SALARIO_MINIMO, timeout=60).json()
        with open(RAW / "salario_minimo_bcb_mensal.csv", "w", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["data", "valor"])
            for p in serie:
                w.writerow([p["data"], p["valor"]])
        status += " + série BCB 1619 (online)"
    except (requests.RequestException, ValueError):
        pass
    return status


def run() -> list[str]:
    RAW.mkdir(parents=True, exist_ok=True)
    return [ingest_salario_minimo(), ingest_gasolina(), ingest_bigmac()]
