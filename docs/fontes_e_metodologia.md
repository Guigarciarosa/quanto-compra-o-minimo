# Fontes e metodologia

## Salário mínimo
Tabela de vigências do salário mínimo nacional de julho de 1994 até janeiro de 2026, com a norma legal (lei, medida provisória ou decreto) que fixou cada valor. Fonte: tabela pública do IEPREV, conferível com a série 1619 do SGS do Banco Central, que o `qcm ingest` baixa quando há rede. O valor anual usado nas comparações é a média dos 12 meses do ano, porque em vários anos o reajuste não aconteceu em janeiro (antes de 2010 os reajustes eram entre março e junho; em 2011, 2020 e 2023 houve dois valores no mesmo ano).

## Gasolina
Preço médio da gasolina C ao consumidor por unidade da Federação, em reais por litro e valores correntes, de 2016 a 2025. Fonte: ANP, Anuário Estatístico Brasileiro do Petróleo, Gás Natural e Biocombustíveis 2026, tabela 3.20, ponderado pelas vendas das distribuidoras. A média Brasil do projeto é a média simples das 27 UFs, não a média ponderada nacional da ANP, então pode diferir alguns centavos do número oficial.

## Big Mac
Preço local do Big Mac no Brasil, em reais, do Índice Big Mac da revista The Economist (repositório público big-mac-data), com pesquisas de 2000 a 2026. A partir de 2006 há duas pesquisas por ano; o projeto usa a média das pesquisas do ano.

## Limitações
Todos os valores são nominais, sem correção pela inflação, o que não atrapalha a razão "quantas unidades um salário compra", porque salário e preço estão na mesma moeda e no mesmo ano. Antes de 2016 não há gasolina no snapshot atual; para 2001-2015 a fonte é a série histórica semanal do levantamento de preços da ANP, prevista no roadmap. Preço de tomate e cesta básica (DIEESE/IBGE) e preço de carro (FIPE) ainda não foram integrados.
