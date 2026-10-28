"""Camadas bronze/silver/gold no DuckDB."""
from __future__ import annotations

import duckdb

from . import DB_PATH, RAW

SQL = """
-- bronze
CREATE OR REPLACE TABLE bronze_salario_minimo AS
SELECT * FROM read_csv('{raw}/salario_minimo.csv', delim=';', header=true,
                       columns={{'vigencia':'VARCHAR','valor':'DOUBLE','norma':'VARCHAR'}});
CREATE OR REPLACE TABLE bronze_gasolina AS
SELECT * FROM read_csv('{raw}/gasolina_c_anp_uf.csv', delim=';', header=true,
                       columns={{'regiao':'VARCHAR','uf':'VARCHAR','ano':'INTEGER','preco_litro':'DOUBLE'}});
CREATE OR REPLACE TABLE bronze_bigmac AS
SELECT * FROM read_csv('{raw}/bigmac_economist.csv', header=true, auto_detect=true);

-- silver: salário mínimo expandido mês a mês (vale do mês de vigência até a próxima)
CREATE OR REPLACE TABLE salario_minimo_mensal AS
WITH v AS (
  SELECT strptime(vigencia || '-01', '%Y-%m-%d')::DATE AS inicio, valor, norma,
         lead(strptime(vigencia || '-01', '%Y-%m-%d')::DATE) OVER (ORDER BY vigencia) AS fim
  FROM bronze_salario_minimo
)
SELECT m::DATE AS mes, year(m) AS ano, v.valor, v.norma
FROM v, generate_series(v.inicio, coalesce(v.fim - INTERVAL 1 MONTH, DATE '{ultimo_ano}-12-01'), INTERVAL 1 MONTH) t(m);

CREATE OR REPLACE TABLE gasolina_uf AS SELECT regiao, uf, ano, preco_litro FROM bronze_gasolina;

CREATE OR REPLACE TABLE bigmac_br AS
SELECT year(date) AS ano, date AS data_pesquisa, local_price AS preco_reais, dollar_ex AS cambio_usd
FROM bronze_bigmac WHERE iso_a3 = 'BRA';

-- gold
CREATE OR REPLACE VIEW salario_minimo_anual AS
SELECT ano, round(avg(valor), 2) AS salario_medio, max(valor) AS salario_dez,
       string_agg(DISTINCT norma, ', ') AS normas
FROM salario_minimo_mensal GROUP BY ano;

CREATE OR REPLACE VIEW gasolina_br_anual AS
SELECT ano, round(avg(preco_litro), 3) AS preco_medio_ufs FROM gasolina_uf GROUP BY ano;

CREATE OR REPLACE VIEW bigmac_br_anual AS
SELECT ano, round(avg(preco_reais), 2) AS preco_bigmac FROM bigmac_br GROUP BY ano;

CREATE OR REPLACE VIEW poder_compra_anual AS
SELECT s.ano, s.salario_medio, g.preco_medio_ufs AS gasolina_litro,
       round(s.salario_medio / g.preco_medio_ufs, 1) AS litros_gasolina,
       b.preco_bigmac, round(s.salario_medio / b.preco_bigmac, 1) AS bigmacs
FROM salario_minimo_anual s
LEFT JOIN gasolina_br_anual g USING (ano)
LEFT JOIN bigmac_br_anual b USING (ano)
ORDER BY s.ano;

CREATE OR REPLACE VIEW poder_compra_uf AS
SELECT g.uf, g.regiao, g.ano, g.preco_litro, s.salario_medio,
       round(s.salario_medio / g.preco_litro, 1) AS litros_gasolina
FROM gasolina_uf g JOIN salario_minimo_anual s USING (ano);
"""

SCHEMA_DOC = """Tabelas e views disponíveis (DuckDB):
- salario_minimo_mensal(mes DATE, ano INT, valor DOUBLE, norma VARCHAR)
- salario_minimo_anual(ano, salario_medio, salario_dez, normas)  -- média dos 12 meses
- gasolina_uf(regiao, uf, ano, preco_litro)  -- ANP, gasolina C, R$/litro, 2016-2025
- gasolina_br_anual(ano, preco_medio_ufs)  -- média simples das 27 UFs
- bigmac_br(ano, data_pesquisa, preco_reais, cambio_usd)  -- The Economist, 2000-2026
- bigmac_br_anual(ano, preco_bigmac)
- poder_compra_anual(ano, salario_medio, gasolina_litro, litros_gasolina, preco_bigmac, bigmacs)
- poder_compra_uf(uf, regiao, ano, preco_litro, salario_medio, litros_gasolina)
Nomes de UF por extenso, com acento (ex.: 'Paraná', 'São Paulo')."""


def connect(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH), read_only=read_only)


def build(ultimo_ano: int = 2026) -> None:
    with connect() as con:
        con.execute(SQL.format(raw=RAW.as_posix(), ultimo_ano=ultimo_ano))
