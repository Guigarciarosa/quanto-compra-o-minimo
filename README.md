# Quanto Compra o Mínimo

Pergunte em português e receba a resposta com fonte: **quantos litros de gasolina, quantos Big Macs e qual norma legal** estão por trás do salário mínimo brasileiro de 1994 a 2026.

O projeto junta **Text-to-SQL** (para números exatos) e **RAG** (para contexto: leis, metodologia, limitações) num agente que roda **100% local com Ollama**, e expõe as mesmas ferramentas por um **servidor MCP**, então dá para plugar no Claude Desktop, Claude Code ou qualquer cliente MCP.

```
$ qcm sql "select ano, salario_medio, gasolina_litro, litros_gasolina, bigmacs from poder_compra_anual where ano between 2019 and 2023"
ano | salario_medio | gasolina_litro | litros_gasolina | bigmacs
2019 | 998.0 | 4.409 | 226.4 | 58.0
2020 | 1044.5 | 4.305 | 242.6 | 51.2
2021 | 1100.0 | 5.82 | 189.0 | 49.1
2022 | 1212.0 | 6.157 | 196.8 | 52.9
2023 | 1314.0 | 5.596 | 234.8 | 57.4
```

Em 2021 o litro subiu 35% e o salário 5,3%: o mínimo passou de 242,6 para 189 litros. É esse tipo de pergunta ("quanto comprava e por quê") que o agente responde, buscando o número no SQL e o contexto (qual norma, qual política de reajuste) no RAG.

## Arquitetura

```
 fontes públicas            DuckDB (medallion)                     agente (Ollama, tool calling)
 ─────────────────          ──────────────────────────────         ──────────────────────────────
 Salário mínimo + norma ─┐  bronze_*  →  silver (mês a mês)  ─┐    consultar_sql  → números exatos
 ANP gasolina C por UF  ─┼→ gold: poder_compra_anual / _uf   ─┼──→ buscar_documentos → contexto
 Big Mac (The Economist)─┘  chunks(emb FLOAT[])  ← corpus    ─┘    resposta + "Fontes:"
                                    ↑                                     │
                     fichas por ano, por norma, docs/*.md      servidor MCP (stdio ou HTTP)
```

- **Ingestão** (`qcm ingest`): baixa ANP, The Economist e a série 1619 do Banco Central; se a rede falhar, usa os snapshots versionados em `data/snapshots/`.
- **Warehouse** (`qcm build`): DuckDB com camadas bronze/silver/gold. O salário anual é a média dos 12 meses, porque vários anos tiveram dois valores (2011, 2020, 2023).
- **Corpus + chunking** (`qcm index`): fichas geradas por ano e por norma legal, mais notas de metodologia escritas à mão; quebra por seção com janela de 700 caracteres e 120 de sobreposição.
- **Embeddings**: `nomic-embed-text` via Ollama; sem Ollama, um embedder de hashing determinístico deixa tudo rodando offline (testes e CI).
- **Busca híbrida**: top 30 por similaridade de cosseno dentro do DuckDB (`list_cosine_similarity`) e rerank por termos exatos (anos, valores, números de lei), que é onde busca puramente vetorial erra.
- **Agente**: `qwen2.5:7b` com tool calling. Regra do prompt: todo número vem de SQL, nunca do modelo. SQL somente leitura, uma query por vez, 50 linhas no máximo.
- **Avaliação** (`qcm eval`): hit@3 da recuperação num conjunto de perguntas com o documento esperado (`eval/perguntas.json`). Hoje: 10/10.

## Rodando

```bash
pip install -e ".[dev]"
qcm all                      # ingest + build + index
qcm sql "select * from poder_compra_anual where ano >= 2016"
qcm ask "Qual decreto definiu o salário mínimo de 2026?" -v
pytest -q
```

Com Ollama local: `ollama pull nomic-embed-text && ollama pull qwen2.5:7b`, depois `qcm index` de novo para reindexar com embeddings reais.

### No ZimaOS (ou qualquer servidor com Docker)

```bash
docker compose up -d          # sobe Ollama, baixa os modelos e serve o MCP na porta 8000
docker compose exec qcm python -m qcm index   # reindexa depois que os modelos baixarem
docker compose exec qcm qcm ask "Quantos Big Macs um mínimo comprava em 2000 e em 2026?"
```

### Como servidor MCP no Claude Desktop / Claude Code

```json
{ "mcpServers": { "quanto-compra-o-minimo": { "command": "qcm-mcp" } } }
```

## Fontes e limitações

| Dado | Fonte | Período |
|---|---|---|
| Salário mínimo e norma legal | Tabela de vigências (IEPREV), conferível com SGS/BCB série 1619 | jul/1994 a 2026 |
| Gasolina C, R$/litro por UF | ANP, Anuário Estatístico 2026, tabela 3.20 | 2016 a 2025 |
| Big Mac no Brasil | The Economist, big-mac-data | 2000 a 2026 |

Valores nominais. A média Brasil da gasolina é a média simples das UFs. O projeto não faz inferência causal sobre leis; ele mostra o reajuste de cada norma contra a variação dos preços.

## Roadmap
- Gasolina 2001-2015 pela série histórica semanal da ANP.
- Tomate e cesta básica (DIEESE / IBGE-IPCA) e meses de salário para comprar um carro popular (tabela FIPE).
- Corpus com o texto integral das leis (Planalto/LexML) para perguntas sobre o conteúdo das normas.
- Interface web e deploy no ZimaOS com Cloudflare Tunnel.
