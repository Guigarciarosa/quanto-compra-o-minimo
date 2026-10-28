from qcm import agent, evaluate, tools
from qcm.corpus import chunk


def test_salario_medio_considera_dois_valores_no_ano():
    # 2023: R$ 1.302 de jan a abr e R$ 1.320 de mai a dez
    out = tools.consultar_sql("select salario_medio from salario_minimo_anual where ano = 2023")
    assert out.splitlines()[1] == "1314.0"


def test_poder_compra_gasolina_2021():
    out = tools.consultar_sql("select litros_gasolina from poder_compra_anual where ano = 2021")
    assert float(out.splitlines()[1]) == 189.0


def test_sql_somente_leitura():
    assert tools.consultar_sql("drop table gasolina_uf").startswith("Erro")
    assert tools.consultar_sql("select 1; drop table gasolina_uf").startswith("Erro")
    assert "Erro SQL" in tools.consultar_sql("select * from tabela_que_nao_existe")


def test_chunk_com_sobreposicao():
    texto = " ".join(f"palavra{i}" for i in range(400))
    partes = chunk(texto, tamanho=300, sobreposicao=50)
    assert len(partes) > 1
    assert all(len(p) <= 300 for p in partes)
    assert partes[0].split()[-1] in partes[1]


def test_recuperacao_hit_rate():
    assert evaluate.run(k=3)["hit_rate"] >= 0.9


def test_agente_chama_ferramenta_e_responde(monkeypatch):
    """Simula o Ollama: 1ª resposta pede SQL, 2ª responde usando o resultado da ferramenta."""
    respostas = iter([
        {"message": {"role": "assistant", "content": "", "tool_calls": [
            {"function": {"name": "consultar_sql", "arguments": {"sql": "select litros_gasolina from poder_compra_anual where ano = 2021"}}}
        ]}},
        {"message": {"role": "assistant", "content": "Cerca de 189 litros.\nFontes: poder_compra_anual"}},
    ])
    enviados = []

    class Resp:
        def __init__(self, data):
            self.data = data

        def raise_for_status(self):
            pass

        def json(self):
            return self.data

    def fake_post(url, json, timeout):
        enviados.append(json)
        return Resp(next(respostas))

    monkeypatch.setattr(agent, "modelo_instalado", lambda m: True)
    monkeypatch.setattr(agent.requests, "post", fake_post)
    resposta = agent.ask("Quantos litros de gasolina um salário mínimo comprava em 2021?")
    assert "189" in resposta
    ultima_tool = [m for m in enviados[1]["messages"] if m["role"] == "tool"][0]
    assert "189.0" in ultima_tool["content"]
