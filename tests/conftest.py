import pytest

from qcm import ingest, rag, warehouse
from qcm.embeddings import HashingEmbedder


@pytest.fixture(scope="session", autouse=True)
def warehouse_pronto(tmp_path_factory):
    import qcm

    db = tmp_path_factory.mktemp("db") / "qcm.duckdb"
    qcm.DB_PATH = db
    warehouse.DB_PATH = db
    for name in ("salario_minimo.csv", "gasolina_c_anp_uf.csv", "bigmac_economist.csv"):
        ingest.RAW.mkdir(parents=True, exist_ok=True)
        ingest._fallback(name)
    warehouse.build()
    rag.index(HashingEmbedder())
    yield
