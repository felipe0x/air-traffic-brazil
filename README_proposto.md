# Malha aérea brasileira: aeroportos e rotas críticos e alternativas de contorno

Projeto da Unidade 01 de Algoritmos e Estrutura de Dados II (Grafos) — UFRN.

## Integrantes

Felipe Rocha Silva · Kaiky Hanry Alencar Fernandes

## Vídeo

**A preencher** — vídeo no YouTube (não listado), até 15 minutos no total, todos os integrantes com câmera aberta e rosto visível.

> Requisito do enunciado: sem o link explícito aqui, a nota do projeto é zero.

## Problema e pergunta

A malha aérea doméstica brasileira é concentrada: poucos aeródromos respondem pela maior parte dos voos e ligam regiões que, sem eles, deixariam de ter ligação direta ou razoável. Uma indisponibilidade (interdição de pista, evento climático, atraso sistêmico) em um ponto desses não afeta apenas quem passa por ele, mas a possibilidade de chegar a outros aeroportos.

**Pergunta:** quais aeroportos e quais rotas são críticos para a conectividade da malha aérea doméstica brasileira e, quando um deles fica indisponível, quais rotas alternativas restam?

Quem se beneficia da resposta: quem decide contingência na malha (operador, regulador, gestor de aeroporto). E por que a estrutura da rede importa: criticidade não é volume — um aeroporto pequeno pode ser o único caminho de uma região inteira, e um aeroporto grande pode ter alternativas. Só a topologia (caminhos, componentes, redundância) distingue os dois casos; é isso que o projeto mede.

## Dados (fonte, como obter, limpeza)

- **Fonte:** ANAC — Dados Estatísticos do Transporte Aéreo (dados abertos). Página "Dados e Estatísticas": https://www.gov.br/anac/pt-br/assuntos/dados-e-estatisticas/dados-estatisticos
- **Como obter:** o arquivo está versionado em [`data/2025.csv`](data/2025.csv) (9,7 MB), baixado manualmente da página acima em 16/10/2026. Como o arquivo está no repositório, não há script de download; `scripts/gerar_coordenadas.py` e `scripts/gerar_mapa_base.py` obtêm os auxiliares (seção Modelagem).
- **Formato:** CSV, separador `;`, encoding latin1, 37.988 linhas, 38 colunas; voos domésticos **e** internacionais de 2025.
- **Limpeza:** recorte `PAÍS` de origem **e** destino `= BRASIL`, `DECOLAGENS > 0`, sem self-loop; agregação por par origem–destino somando `DECOLAGENS` e `PASSAGEIROS PAGOS`. Resultado: **176 aeródromos e 1.660 rotas**. A trilha completa (37.988 linhas brutas → 22.128 no recorte canônico → 1.660 rotas) e o efeito medido de cada escolha estão em `notebooks/01_dados.ipynb` e em [`DOCUMENTACAO.md`](DOCUMENTACAO.md).

## Modelagem (nó, aresta, peso, direção, o que ficou de fora)

- **Nó:** aeródromo, identificado pela sigla ICAO (ex. `SBGR`), com nome, UF e região.
- **Aresta:** rota doméstica origem → destino observada na janela de 2025.
- **Direção:** dirigido — os volumes de ida e volta diferem (dos 987 pares ligados, 314 têm rota em um sentido só).
- **Peso:** `DECOLAGENS` (oferta) e `PASSAGEIROS PAGOS` (demanda) como atributos distintos; cada cálculo declara qual usa.
- **Fica de fora:** malha internacional, voos com escala (o dado é ponto a ponto), frequência por dia/hora, tipo de aeronave, preço, carga e capacidade operacional do aeroporto.
- **Hipóteses:** janela anual agregada; ausência de aresta = rota inexistente na janela; `DECOLAGENS > 0` define rota ativa.
- **Auxiliares reprodutíveis:** coordenadas dos aeródromos via [OurAirports](https://davidmegginson.github.io/ourairports-data/) (176/176, `scripts/gerar_coordenadas.py` → `data/aerodromos_coordenadas.csv`) e contorno dos estados via *click_that_hood*/IBGE simplificado (`scripts/gerar_mapa_base.py` → `data/brasil_estados.geojson`).

## Conteúdo do curso utilizado

| conceito | semana | onde aparece (notebook, célula/função) | para que serviu |
|---|---|---|---|
| digrafo e atributos de nó/aresta | 2 | `02_rede`, In[2] (`malha.construir_digrafo`) | modelar rota com direção e pesos |
| densidade | 2 | `02_rede`, In[2] | mostrar que a malha é esparsa (0,054) |
| grau e distribuição de grau | 2 | `02_rede`, In[3] (`malha.tabela_graus`) | cauda longa; média não descreve o aeródromo |
| matriz de adjacência | 2 | `02_rede`, In[5] | ver a topologia inteira do top-40 (massa nos hubs) |
| subgrafo/subrede | 2 | `02_rede`, In[5] e In[9] | recortes top-40 / top-30 para visualização |
| reciprocidade | 2 | `02_rede`, In[2] | 673/987 pares bidirecionais — justifica o dirigido |
| BFS em camadas | 3 | `02_rede`, In[7] (`malha.camadas_bfs`) | mundo pequeno: 97% dos aeródromos a ≤ 2 saltos de SBGR |
| núcleo e periferia (BFS) | 3 | `02_rede`, In[7] (`malha.nucleo_periferia_bfs`) | separar quem chega cedo de quem fica na borda |
| grau de entrada e de saída | 3 | `02_rede`, In[3] | condições de partida/chegada usadas na falha |
| amostragem por bola de neve | 3 | `02_rede`, In[8] (`malha.amostragem_snowball`) | demonstrar o viés de coleta por vizinhança |
| caminhos mais curtos e distâncias | 4 | `03_analise`, In[3] (`malha.distancia_e_eficiencia`), In[4] | comprimento médio de 2,47 saltos |
| componentes (WCC/SCC) | 4 | `03_analise`, In[2] (`malha.resumo_componentes`) | malha é 1 WCC; `SBBP` fora do SCC |
| diâmetro, raio, excentricidade, centro/periferia | 4 | `03_analise`, In[3]–In[4] | pior caso de 5 saltos; periferia de 9 aeródromos |
| eficiência global | 4 | `03_analise`, In[3] e In[21] (`malha.eficiencia_global`) | régua da robustez (pune desconexão) |
| centralidades: grau, proximidade, intermediação, autovetor | 4 | `03_analise`, In[5] (`malha.tabela_centralidades`), In[6] | achar os gargalos (SBKP, SBCF, SBEG) |
| variantes de custo da intermediação | 4 | `03_analise`, In[7] (`malha.tabela_intermediacao_variantes`) | sensibilidade: saltos × km × frequência |
| triângulos e clustering | 4 | `03_analise`, In[9] (`malha.tabela_clustering`) | coesão regional (SUL 0,78 × SUDESTE 0,62) |
| nxviz (circos) | 4 | `02_rede`, In[9] | visão por região do top-30 |
| k-core, k-shell, core number, degeneracy | 5 | `03_analise`, In[10]–In[12] (`malha.core_numbers_manual`, `malha.tabela_kcore`) | miolo denso de 24 aeródromos; degeneração 18 |
| k-truss | 5 | `03_analise`, In[13] (`malha.tabela_ktuss`) | núcleo coeso (70 nós no k=7) por critério de triângulo |
| grafo bipartido e matriz de incidência | 6 | `03_analise`, In[14] (`malha.bipartido_aeroporto_empresa`) | quem opera onde (176 aeroportos × 73 empresas) |
| projeção e Jaccard (empresas) | 6 | `03_analise`, In[14] (`malha.jaccard_empresas`) | pares de aeródromos substitutos operacionais |
| Jaccard de vizinhança | 6 | `03_analise`, In[15] (`malha.jaccard_vizinhanca`) | redundância de destinos (SBGL–SBGR, 0,73) |
| esqueleto por limiar | 6 | `03_analise`, In[17]–In[18] (`malha.esqueleto_limiar`) | tronco que carrega 80% das decolagens em 283 rotas |
| articulações e pontes (complementar) | 4–5 | `03_analise`, In[19] | 16 dos 20 hubs são pontos de corte da projeção |
| remoção de nó e curvas de falha | 4–5 | `03_analise`, In[20]–In[21] (`malha.impacto_remocao`, `malha.curva_remocao_*`) | medir o estrago (alvo × aleatória) |
| arestas críticas e caminhos alternativos | 4–6 | `03_analise`, In[22]–In[24] (`malha.arestas_criticas`, `malha.pares_afetados`) | responder "quais rotas restam" |

> Cada linha corresponde a conteúdo nomeado no código; `In[k]` é a célula executada no
> notebook indicado. A mesma tabela está condensada no vídeo.

## Como executar

```bash
git clone https://github.com/felipe0x/air-traffic-brazil.git
cd air-traffic-brazil
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt "nxviz>=0.7.4"   # nxviz: circos da figura 07 (fora do requirements)
bash scripts/reproduzir.sh                        # executa os 3 notebooks na ordem
```

`scripts/reproduzir.sh` executa `01_dados` → `02_rede` → `03_analise`, regenerando figuras
(`figuras/`) e tabelas (`resultados/`) com as mesmas versões de biblioteca
(`requirements.txt`, Python 3.12). Requisitos de dados: `data/2025.csv` já está no
repositório; `data/aerodromos_coordenadas.csv` e `data/brasil_estados.geojson` também — os
scripts `scripts/gerar_coordenadas.py` e `scripts/gerar_mapa_base.py` regeneram esses dois
arquivos a partir das fontes públicas (requer internet apenas para isso).

Para rodar célula a célula: `jupyter lab` e abrir os notebooks na ordem 01 → 02 → 03.

## Resultados

**Resposta curta.** Os aeródromos críticos de verdade são **SBKP (Campinas)**, **SBCF
(Confins)** e **SBEG (Manaus)** — não os de maior volume. Na intermediação (quanto dos
caminhos curtos do país passa por lá) Campinas lidera (0,252); no impacto medido por
remoção, Manaus lidera: sozinho tira **10,3% da eficiência global** da malha e deixa
`SBTT`, `SWBC` e `SWBR` **sem nenhuma rota de saída** — mais da metade (57%) dos pares que
usavam Manaus perde alternativa. Guarulhos, o maior em passageiros, custa 1,8%: tem
alternativas. **Na rede, crítico = único, não maior.**

**Rotas críticas.** O corredor `SBKP↔SBEG` lidera a intermediação de aresta nas duas
direções; nenhuma das 15 rotas mais críticas é ponte da projeção (o tronco tem alternativa
de +1 salto), mas duas relações direcionais perdem o caminho por completo (`SBEG→SBUY`,
`SBTT→SBEG`). As 22 pontes existentes ligam aeródromos pequenos a um único hub.

**Estrutura.** A malha doméstica de 2025 é um único componente fraco com 176 aeródromos e
1.660 rotas (densidade 0,054) e um núcleo denso de 24 aeródromos no k-core k=18. O tronco
de volume é minúsculo: 283 rotas (17%) carregam 80% das decolagens. A remoção informada de
12 aeródromos derruba a eficiência para 33% do original, enquanto 12 remoções aleatórias
custam 7% — a malha é tolerante a falha aleatória e sensível a falha escolhida.

**Figuras e tabelas.** A análise completa está em `notebooks/01_dados.ipynb`,
`02_rede.ipynb` e `03_analise.ipynb` (executados), com figuras numeradas em `figuras/`
(01 a 19) e tabelas em `resultados/` — destaque para `ranking_criticidade.csv` (síntese de
criticidade por aeródromo), `arestas_criticas.csv`, `rotas_alternativas_SBKP.csv` e
`rotas_alternativas_SBEG.csv` (os pares afetados e o caminho que resta em cada caso).

## Limitações e próximos passos

**Limitações reconhecidas** (detalhadas no notebook 03 e em `DOCUMENTACAO.md`):

1. **Janela anual:** a rede de 2025 é a união de 12 meses; um aeródromo que só opera
   sazonalmente aparece como contínuo (janeiro isolado tem 158 nós, não 176).
2. **`NATUREZA` da ANAC contraditória:** o campo marca 671 linhas Brasil–Brasil como
   `INTERNACIONAL`; usamos `PAÍS` das pontas (diferença de 0,4% nas rotas).
3. **Voo ≠ rota:** `DECOLAGENS` é oferta agregada; não há frequência diária nem escala.
4. **Distância:** haversine das coordenadas (OurAirports); o campo da ANAC tem 622 nulos no
   recorte e foi usado só como conferência.
5. **Medidas estruturais na projeção não dirigida** (clustering, k-core, k-truss, pontes,
   articulações): um ciclo dirigido de 3 nós vira triângulo.
6. **Intermediação anunciada sem peso:** por km o ranking é quase o mesmo (Spearman 0,905);
   por frequência Guarulhos assume o topo (0,656). As três concordam no conjunto de gargalos.
7. **Artefatos tratados:** grau 1–2 com clustering/Jaccard = 1 por construção; `SBBP` (1
   decolagem de posicionamento, 0 passageiro); `SBJD` (Jundiaí) no top-10 de intermediação
   com 0 passageiro pago — voos não comerciais como atalhos na medida sem peso.

**Próximos passos:** repetir a análise por mês (sazonalidade); falha por companhia aérea
(o bipartido está pronto); cruzar com capacidade de pista/terminal (conectividade ≠
capacidade); incluir exposição internacional dos hubs; comparar 2024 × 2025.

## Referências

- ANAC. *Dados Estatísticos do Transporte Aéreo* (dados abertos). https://www.gov.br/anac/pt-br/assuntos/dados-e-estatisticas/dados-estatisticos
- OurAirports. *airports.csv*. https://davidmegginson.github.io/ourairports-data/
- *click_that_hood* (contorno de estados, derivado do IBGE). https://github.com/codeforamerica/click_that_hood
- NetworkX. *Documentation*. https://networkx.org/documentation/stable/
- nxviz. *Documentation*. https://nxviz.readthedocs.io/
- Coscia, M. *The Atlas for the Aspiring Network Scientist*. 2ª ed. — material de apoio do curso (semanas 2–6).
