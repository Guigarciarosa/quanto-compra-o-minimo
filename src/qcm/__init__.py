"""Quanto Compra o Mínimo: RAG + Text-to-SQL sobre dados públicos do salário mínimo."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
SNAPSHOTS = DATA / "snapshots"
RAW = DATA / "raw"
DB_PATH = Path(os.getenv("QCM_DB", DATA / "qcm.duckdb"))
DOCS = ROOT / "docs"
