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
- **Limpeza:** recorte `PAÍS` de origem **e** destino `= BRASIL`, `DECOLAGENS > 0`, sem self-loop; agregação por par origem–destino somando `DECOLAGENS` e `PASSAGEIROS PAGOS`. Resultado: **176 aeródromos e 1.660 rotas**. A trilha completa (37.988 linhas brutas → 22.128 no recorte adotado → 1.660 rotas) e a tabela de decisões estão em `notebooks/apresentacao.ipynb`, In[2] e In[3]; o CSV é `resultados/decisoes_recorte.csv`.
- **Por que essas escolhas:** `PAÍS` nas duas pontas porque a pergunta é sobre a malha nacional e o campo `NATUREZA` da ANAC classifica 671 linhas domésticas como internacionais; `DECOLAGENS > 0` porque a análise mede operação efetiva, não venda de assento; sem self-loop porque um aeroporto não é rota para si; ano inteiro e agregação por par porque a pergunta é estrutural e o volume entra como peso, não como filtro. A tabela de decisões mede a alternativa descartada: incluir internacional levaria a **396 aeródromos e 2.912 rotas**; exigir só voo regular, a **161 e 1.299**; usar só janeiro, a **158 e 1.039**.

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
| densidade | 2 | In[4] (`malha.metricas_basicas`) | mostrar que a malha é esparsa (0,054) |
| grau e distribuição de grau | 2 | In[5] (`malha.tabela_graus`, `malha.ccdf`) | cauda longa; média não descreve o aeródromo |
| reciprocidade | 2 | In[4] | 673/987 pares bidirecionais justificam o dirigido |
| BFS em camadas | 3 | In[6] (`malha.camadas_bfs`) | mundo pequeno: 97% a ≤ 2 saltos de SBGR; núcleo × periferia |
| grau de entrada e de saída | 3 | In[5] (`malha.tabela_graus`) | condições de partida/chegada usadas na falha |
| caminhos mais curtos e distâncias | 4 | In[7] (`malha.distancia_e_eficiencia`), In[13] (`malha.pares_afetados`) | comprimento médio de 2,47 saltos; rota que resta após a falha |
| componentes (WCC/SCC) | 4 | In[7] (`malha.resumo_componentes`) | malha é 1 WCC; `SBBP` fora do SCC |
| diâmetro, raio, centro/periferia | 4 | In[7] (`malha.distancia_e_eficiencia`) | pior caso de 5 saltos; periferia de 9 aeródromos |
| eficiência global | 4 | In[7] (`malha.eficiencia_global`) | régua da robustez (pune desconexão) |
| centralidades: grau, proximidade, intermediação, autovetor | 4 | In[8] (`malha.tabela_centralidades`) | achar os gargalos (SBKP, SBCF, SBEG) |
| k-core, core number e degeneracy | 5 | In[9] (`malha.tabela_kcore`; `nx.core_number`/`nx.k_core`) | miolo denso de 24 aeródromos; degeneração 18 |
| Jaccard de vizinhança | 6 | In[10] (`malha.jaccard_vizinhanca`) | redundância de vizinhança (SBGL–SBGR, 0,73) |
| arestas críticas e caminhos alternativos | 4 | In[12]–In[13] (`malha.arestas_criticas`, `malha.pares_afetados`) | responder "quais rotas restam" |

> Cada linha corresponde a conteúdo nomeado no código; `In[k]` é a célula executada em
> `notebooks/apresentacao.ipynb`. A mesma tabela está condensada no vídeo.

## Estrutura do repositório

```
.
├── notebooks/apresentacao.ipynb   # análise completa, executada e com saídas
├── src/malha.py                   # funções reutilizadas pelo notebook
├── scripts/reproduzir.sh          # reprodução em um comando
├── scripts/gerar_coordenadas.py   # auxiliar: coordenadas dos aeródromos (OurAirports)
├── scripts/gerar_mapa_base.py     # auxiliar: contorno dos estados (GeoJSON)
├── data/                          # 2025.csv da ANAC + auxiliares versionados
├── figuras/                       # 01 a 06, geradas pelo notebook
└── resultados/                    # 10 CSVs gerados pelo notebook
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
direções; quase todas as 15 rotas do topo têm alternativa de +1 salto, mas duas relações
direcionais perdem o caminho por completo (`SBEG→SBUY`, `SBTT→SBEG`).

**Estrutura.** A malha doméstica de 2025 é um único componente fraco com 176 aeródromos e
1.660 rotas (densidade 0,054) e um núcleo denso de 24 aeródromos no k-core k=18. Fora do
miolo, 64 aeródromos têm core number ≤ 2: a periferia depende de poucos caminhos.

**Artefatos reconhecidos.**

- **Amostragem.** A base é o censo de 2025, não uma amostra; os números valem para as rotas
  reportadas, não para uma estimativa do universo.
- **Projeção.** O k-core de 24 aeródromos sai da projeção não dirigida; nela um ciclo
  dirigido de 3 nós vira triângulo.
- **Dados faltantes.** Ausência de aresta é rota não reportada na janela, não isolamento real.
  `SBBP` é o único nó fora do SCC: não tem rota de entrada, só 1 decolagem e 0 passageiro pago
  no ano. `DISTÂNCIA VOADA (KM)`, com 622 nulos nas linhas Brasil–Brasil, não entra nos
  cálculos; a distância vem de haversine.
- **Medida sem peso.** `SBJD` (Jundiaí) aparece no top-10 de intermediação com 0 passageiro pago:
  a centralidade conta passagem topológica, não demanda.

**Figuras e tabelas.** A análise completa está em `notebooks/apresentacao.ipynb`
(executado), com as figuras numeradas de 01 a 06 em `figuras/` e as tabelas em
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
