# Malha aérea brasileira: aeroportos e rotas críticos e alternativas de contorno

Projeto da Unidade 01 de Algoritmos e Estrutura de Dados II (Grafos), UFRN.

## Integrantes

Felipe Rocha Silva · Kaiky Hanry Alencar Fernandes

## Vídeo

**A preencher:** vídeo no YouTube (não listado), até 15 minutos no total, todos os integrantes com câmera aberta e rosto visível.

> Requisito do enunciado: sem o link explícito aqui, a nota do projeto é zero.

## Problema e pergunta

A malha aérea doméstica brasileira é concentrada: poucos aeródromos respondem pela maior parte dos voos e ligam regiões que, sem eles, deixariam de ter ligação direta ou razoável. Uma indisponibilidade (interdição de pista, evento climático, atraso sistêmico) em um ponto desses não afeta apenas quem passa por ele, mas a possibilidade de chegar a outros aeroportos.

**Pergunta:** quais aeroportos atuam como gargalos críticos na malha nacional e qual o impacto real da interrupção de um hub regional no isolamento do país?

**Decisão prática atrelada:** orientar planos de contingência governamentais e a alocação estratégica de investimentos em infraestrutura aeroportuária regional.

Criticidade não é volume. Um aeroporto pequeno pode ser o único caminho de uma região inteira, enquanto um aeroporto grande tem alternativas. Só a topologia (caminhos, componentes, redundância) distingue os dois casos; é isso que o projeto mede.

## Dados (fonte, como obter, limpeza)

- **Fonte:** ANAC, Dados Estatísticos do Transporte Aéreo (dados abertos). Página "Dados e Estatísticas": https://www.gov.br/anac/pt-br/assuntos/dados-e-estatisticas/dados-estatisticos
- **Como obter:** o arquivo está versionado em [`data/2025.csv`](data/2025.csv) (9,7 MB), baixado manualmente da página acima em 16/10/2026. Como o arquivo está no repositório, não há script de download; `scripts/gerar_coordenadas.py` e `scripts/gerar_mapa_base.py` obtêm os auxiliares (seção Modelagem).
- **Formato:** CSV, separador `;`, encoding latin1, 37.988 linhas, 38 colunas; voos domésticos **e** internacionais de 2025.
- **Limpeza:** recorte `PAÍS` de origem **e** destino `= BRASIL`, `DECOLAGENS > 0`, sem self-loop; agregação por par origem–destino somando `DECOLAGENS` e `PASSAGEIROS PAGOS`. Resultado: **176 aeródromos e 1.660 rotas**. A trilha completa (37.988 linhas brutas → 22.128 no recorte canônico → 1.660 rotas) e o efeito medido de cada escolha estão em `notebooks/apresentacao.ipynb`, In[3] e In[4].
- **Efeito das escolhas** (In[3]): incluir o voo internacional levaria a 396 aeródromos e 3.020 rotas; filtrar pelo campo `NATUREZA` da ANAC custaria 6 rotas; exigir voo regular derrubaria para 161 aeródromos e 1.299 rotas (21% das decolagens fora); usar só janeiro deixaria 158 aeródromos. O recorte canônico preserva 82% das decolagens do arquivo inteiro.

## Modelagem (nó, aresta, peso, direção, o que ficou de fora)

- **Nó:** aeródromo, identificado pela sigla ICAO (ex. `SBGR`), com nome, UF e região.
- **Aresta:** rota doméstica origem → destino observada na janela de 2025.
- **Direção:** dirigida. Os volumes de ida e volta diferem: dos 987 pares ligados, 314 têm rota em um sentido só.
- **Peso:** `DECOLAGENS` e `PASSAGEIROS PAGOS` como atributos distintos; cada cálculo declara qual dos dois usa.
- **Fica de fora:** malha internacional, voos com escala (o dado é ponto a ponto), frequência por dia/hora, tipo de aeronave, preço, carga e capacidade operacional do aeroporto.
- **Hipóteses:** janela anual agregada; ausência de aresta = rota inexistente na janela; `DECOLAGENS > 0` define rota ativa.
- **Auxiliares reprodutíveis:** coordenadas dos aeródromos via [OurAirports](https://davidmegginson.github.io/ourairports-data/) (176/176, `scripts/gerar_coordenadas.py` → `data/aerodromos_coordenadas.csv`) e contorno dos estados via *click_that_hood*/IBGE simplificado (`scripts/gerar_mapa_base.py` → `data/brasil_estados.geojson`).

## Conteúdo do curso utilizado

| conceito | semana | onde aparece (notebook, célula/função) | para que serviu |
|---|---|---|---|
| digrafo e atributos de nó/aresta | 2 | In[2] (`malha.construir_digrafo`) | modelar rota com direção e pesos |
| densidade | 2 | In[5] (`malha.metricas_basicas`) | mostrar que a malha é esparsa (0,054) |
| grau e distribuição de grau | 2 | In[6] (`malha.tabela_graus`, `malha.ccdf`) | cauda longa; média não descreve o aeródromo |
| reciprocidade | 2 | In[5] | 673/987 pares bidirecionais justificam o dirigido |
| BFS em camadas | 3 | In[7] (`malha.camadas_bfs`) | mundo pequeno: 97% a ≤ 2 saltos de SBGR; núcleo × periferia |
| grau de entrada e de saída | 3 | In[6] (`malha.tabela_graus`) | condições de partida/chegada usadas na falha |
| caminhos mais curtos e distâncias | 4 | In[8] (`malha.distancia_e_eficiencia`), In[18] (`malha.pares_afetados`) | comprimento médio de 2,47 saltos; rota que resta após a falha |
| componentes (WCC/SCC) | 4 | In[8] (`malha.resumo_componentes`) | malha é 1 WCC; `SBBP` fora do SCC |
| diâmetro, raio, centro/periferia | 4 | In[8] (`malha.distancia_e_eficiencia`) | pior caso de 5 saltos; periferia de 9 aeródromos |
| eficiência global | 4 | In[8] e In[15]–In[16] (`malha.eficiencia_global`) | régua da robustez (pune desconexão) |
| centralidades: grau, proximidade, intermediação, autovetor | 4 | In[9] (`malha.tabela_centralidades`), In[10] | achar os gargalos (SBKP, SBCF, SBEG) |
| variantes de custo da intermediação | 4 | In[10] (`malha.tabela_intermediacao_variantes`) | sensibilidade: saltos × km × frequência |
| k-core, core number e degeneracy | 5 | In[11] (`malha.tabela_kcore`; `nx.core_number`/`nx.k_core`) | miolo denso de 24 aeródromos; degeneração 18 |
| Jaccard de vizinhança | 6 | In[12] (`malha.jaccard_vizinhanca`) | redundância de destinos (SBGL–SBGR, 0,73) |
| esqueleto por limiar | 6 | In[13] (`malha.esqueleto_limiar`) | tronco que carrega 80% das decolagens em 283 rotas |
| arestas críticas e caminhos alternativos | 4 | In[17]–In[18] (`malha.arestas_criticas`, `malha.pares_afetados`) | responder "quais rotas restam" |

> Cada linha corresponde a conteúdo nomeado no código; `In[k]` é a célula executada em
> `notebooks/apresentacao.ipynb`. A mesma tabela está condensada no vídeo.

**Fora da caixa do curso.** O notebook também usa articulações e pontes (In[14]) e curvas de
remoção alvo × aleatória (In[15]–In[16]) como apoio à interpretação. Não são conteúdo das
semanas 2 a 6, então ficam fora da tabela e não entram na contagem de conceitos do curso.

## Estrutura do repositório

```
.
├── notebooks/apresentacao.ipynb   # análise completa, executada e com saídas
├── src/malha.py                   # funções reutilizadas pelo notebook
├── scripts/reproduzir.sh          # reprodução em um comando
├── scripts/gerar_coordenadas.py   # auxiliar: coordenadas dos aeródromos (OurAirports)
├── scripts/gerar_mapa_base.py     # auxiliar: contorno dos estados (GeoJSON)
├── data/                          # 2025.csv da ANAC + auxiliares versionados
├── figuras/                       # 01 a 09, geradas pelo notebook
└── resultados/                    # 14 CSVs gerados pelo notebook
```

## Como executar

```bash
git clone https://github.com/felipe0x/air-traffic-brazil.git
cd air-traffic-brazil
bash scripts/reproduzir.sh
```

Um comando basta. O `scripts/reproduzir.sh` cria o `.venv`, instala as dependências fixadas
(`requirements.txt`), regenera os auxiliares que estiverem faltando e executa
`notebooks/apresentacao.ipynb`, sobrescrevendo `figuras/` e `resultados/`.

Requisitos: Python 3.12 e internet (para instalar as bibliotecas e, se os auxiliares
faltarem, para alcançar as fontes públicas abaixo). O `data/2025.csv` já está no repositório
e não é baixado.

Para inspecionar o código célula a célula, o ambiente criado pelo comando acima já serve:

```bash
source .venv/bin/activate
jupyter lab        # abrir notebooks/apresentacao.ipynb
```

Sem usar o script: `python3 -m venv .venv`, `source .venv/bin/activate`,
`pip install -r requirements.txt` e então `jupyter lab`.

## Resultados

**Resposta curta.** Os aeródromos críticos de verdade são **SBKP (Campinas)**, **SBCF
(Confins)** e **SBEG (Manaus)**, não os de maior volume. Na intermediação (quanto dos
caminhos curtos do país passa por lá) Campinas lidera (0,252); no impacto medido por
remoção, Manaus lidera: sozinho tira **10,3% da eficiência global** da malha e deixa
`SBTT`, `SWBC` e `SWBR` **sem nenhuma rota de saída**; mais da metade (57%) dos pares que
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
custam 7,5%: a malha é tolerante a falha aleatória e sensível a falha escolhida.

**Artefatos reconhecidos.**

- **Amostragem.** A base é o censo de 2025, não uma amostra; os números valem para as rotas
  reportadas, não para uma estimativa do universo.
- **Projeção.** O k-core de 24 aeródromos, as 18 articulações e as 22 pontes saem da projeção
  não dirigida; nela um ciclo dirigido de 3 nós vira triângulo.
- **Dados faltantes.** Ausência de aresta é rota não reportada na janela, não isolamento real.
  `SBBP` é o único nó fora do SCC porque tem 1 decolagem e 0 passageiro pago no ano (voo de
  posicionamento). `DISTÂNCIA VOADA (KM)`, com 622 nulos nas linhas Brasil–Brasil, não entra nos
  cálculos; a distância vem de haversine.
- **Medida sem peso.** `SBJD` (Jundiaí) aparece no top-10 de intermediação com 0 passageiro pago,
  voos não comerciais como atalho; nós de grau 1–2 têm Jaccard 1 por construção.

**Figuras e tabelas.** A análise completa está em `notebooks/apresentacao.ipynb`
(executado), com as figuras numeradas de 01 a 09 em `figuras/` e as tabelas em
`resultados/`, com destaque para `ranking_criticidade.csv` (síntese de criticidade por
aeródromo), `arestas_criticas.csv`, `rotas_alternativas_SBKP.csv` e
`rotas_alternativas_SBEG.csv` (os pares afetados e o caminho que resta em cada caso).

## Limitações do modelo e próximos passos

1. **Demanda reprimida.** A análise usa dados operados: não contabiliza trechos sem voos
   operantes por falta de infraestrutura, então mede o impacto sobre a malha que existe, não
   sobre a demanda que gostaria de existir.
2. **Dinâmica temporal.** O dado é agregado no ano; a média esconde sazonalidades de alta
   temporada e picos diários.
3. **Conexões de passageiros.** Não mapeia a bilhetagem de ponta a ponta (*origin–destination
   true passenger itineraries*): quem faz escala conta como dois trechos.

**Próximos passos:** repetir a análise por mês; falha por companhia aérea (exige cruzar a
operação por empresa, que a agregação por rota descarta); cruzar com capacidade de
pista/terminal (conectividade ≠ capacidade); comparar 2024 × 2025.

## Referências

- ANAC. *Dados Estatísticos do Transporte Aéreo* (dados abertos). https://www.gov.br/anac/pt-br/assuntos/dados-e-estatisticas/dados-estatisticos
- OurAirports. *airports.csv*. https://davidmegginson.github.io/ourairports-data/
- *click_that_hood* (contorno de estados, derivado do IBGE). https://github.com/codeforamerica/click_that_hood
- NetworkX. *Documentation*. https://networkx.org/documentation/stable/
- Coscia, M. *The Atlas for the Aspiring Network Scientist*. 2ª ed. Material de apoio do curso (semanas 2–6).
