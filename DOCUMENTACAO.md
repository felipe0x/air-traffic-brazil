# DOCUMENTACAO — decisões do projeto, uma a uma

Documento de apoio (interno): registra **cada escolha** do projeto — o que foi decidido, o
que foi testado como alternativa, e qual é o efeito no resultado. O README que vai ao
GitHub é o `README_proposto.md`; este arquivo serve à revisão e à defesa no vídeo.

Todo número citado aqui é reproduzível pelo código do repositório (notebooks + `src/malha.py`);
as saídas ficam em `resultados/*.csv` e `figuras/*.png`.

---

## 1. Dados: fonte e obtenção

- **Arquivo:** `data/2025.csv` — ANAC, *Dados Estatísticos do Transporte Aéreo* (dados
  abertos), baixado em 16/10/2026 da página "Dados e Estatísticas" da ANAC.
- **Formato:** 37.988 linhas, 38 colunas, separador `;`, encoding latin1; voos domésticos
  **e** internacionais de 2025 (coluna `MÊS`, 12 meses).
- **Sem script de download:** o arquivo está versionado no repositório (9,7 MB); o
  enunciado aceita "dados, ou o script que os obtém". O `data/README.md` documenta a fonte.
- **Pendência do Felipe:** registrar o link exato do arquivo baixado e a data de acesso
  (hoje o `data/README.md` tem essa lacuna marcada — não foi editado nesta rodada).

## 2. Recorte canônico (a decisão central)

**Decisão:** `ANO = 2025` · `PAÍS` de origem **e** destino = `BRASIL` · `DECOLAGENS > 0` ·
sem self-loop (origem ≠ destino) · agregado por par origem–destino somando
`DECOLAGENS` e `PASSAGEIROS PAGOS`.

**Resultado:** 176 nós, 1.660 arestas dirigidas, 987 pares não dirigidos, densidade 0,0539.
Tabela completa em `resultados/tabela_recortes.csv`; efeito visual em
`figuras/01_efeito_dos_recortes.png`.

O que foi testado como alternativa (e por que ficou de fora):

| decisão | alternativa testada | efeito medido | por que a escolha |
|---|---|---|---|
| janela | mês (janeiro) / 1º semestre | 158 nós / 1.039 rotas; 170 / 1.396 | o ano (176 / 1.660) é a estrutura; janeiro perde 18 aeródromos e 93% dos voos são sazonais demais para a pergunta. Rede anual = união das 12 redes mensais |
| domesticidade | campo `NATUREZA` da ANAC | 1.654 rotas × 1.660 (6 rotas; 534 linhas) | `NATUREZA` marca **671 linhas internas como `INTERNACIONAL`** (erro do campo: ex. Curitiba→Campinas); `PAÍS` das duas pontas é verificável linha a linha |
| malha | "tudo" (com internacional) / só origem BR | 396 nós / 3.020 rotas; 333 / 2.119 | a pergunta é doméstica; o internacional conecta o país por poucos aeroportos e muda a geografia da rede (exclui 18% das decolagens) |
| self-loop | manter origem = destino | 1.744 → 1.660 arestas | 84 "rotas" com origem = destino (963 linhas) são contabilização da base, não ligação; inflariam grau, densidade e clustering |
| rota ativa | `DECOLAGENS > 0` × `PASSAGEIROS > 0` | 5.586 linhas domésticas têm 0 passageiro pago com decolagem > 0 | decolagem é a oferta (o voo aconteceu); exigir passageiro pago descartaria posicionamento/instrução reais. Fica como artefato reconhecido (seção 7) |
| grupo de voo | só `REGULAR` | 161 nós / 1.299 rotas | voos não regulares/improdutivos são **32% das linhas, mas só 3,5% das decolagens** (28.294 de 802.910); excluí-los derrubaria 15 aeródromos que só têm esse tipo de operação. Ficam dentro — o voo existiu |

Linhas: 37.988 brutas → 23.091 (BR/BR, `DECOLAGENS > 0`, com self-loops) → **22.128 no
recorte canônico** → agregadas por par em **1.660 rotas** (`resultados/base_rotas_2025.csv`).

## 3. Coordenadas e mapa base

Duas alternativas foram consideradas para obter lat/lon dos 176 aeródromos:

1. `data/2025.csv` da ANAC — **não publica** latitude/longitude;
2. OpenFlights `airports.dat` — cobria só **132/176** siglas ICAO do recorte;
3. **OurAirports** (`airports.csv`, domínio público) — **176/176**.

**Decisão:** OurAirports. `scripts/gerar_coordenadas.py` baixa, filtra `BR` e grava
`data/aerodromos_coordenadas.csv` (23 KB, versionado). Para o fundo dos mapas, o contorno
dos estados vem do GeoJSON público do projeto *click_that_hood* (derivado de dados do
IBGE), simplificado a 0,05° por `scripts/gerar_mapa_base.py` → `data/brasil_estados.geojson`
(92 KB, versionado). Os notebooks usam as cópias locais: **executam sem rede**.

Limite: nome do aeródromo/aeródromo pode divergir levemente da ANAC (divergência de
município); afeta mapas e distâncias haversine, não a topologia.

## 4. Modelagem

- **Nó:** aeródromo (sigla ICAO, ex. `SBGR`), com atributos nome, UF e região da ANAC.
- **Aresta dirigida** origem → destino: os volumes de ida e volta diferem — 68,2% dos 987
  pares têm rota nos dois sentidos, 314 pares em sentido único (somar as direções apagaria
  a assimetria). Reciprocidade calculada em `02_rede`, In[2].
- **Pesos:** `DECOLAGENS` (oferta) e `PASSAGEIROS PAGOS` (demanda), como atributos
  distintos; cada cálculo declara qual usa. **Agregação por par**: soma dos 12 meses.
- **Projeção não dirigida** (`h`) para as medidas que o networkx só calcula em grafo não
  dirigido (clustering, k-core, k-truss, pontes, articulações): um ciclo dirigido de 3 nós
  vira triângulo — artefato declarado.
- **Fica de fora:** malha internacional, voos com escala (o dado é ponto a ponto),
  frequência por dia/hora, aeronave, preço, carga, capacidade operacional do aeroporto.

## 5. Pipeline e reprodutibilidade

```
data/2025.csv ──► notebooks/01_dados.ipynb ──► resultados/base_rotas_2025.csv
                                                        │
                                notebooks/02_rede.ipynb ┘ (semanas 2–3)
                                                        │
                                notebooks/03_analise.ipynb (semanas 4–6, falha e resposta)
```

- Toda a lógica é função de `src/malha.py` (o notebook chama, não reimplementa — exceções
  didáticas: `core_numbers_manual` e `k_core_manual`, que cumprem o teste manual==networkx).
- `scripts/reproduzir.sh` reproduz em um comando: venv + dependências + os 3 notebooks na
  ordem, via `jupyter nbconvert --execute` com kernel `python3` do próprio venv.
- Dependência extra: **nxviz ≥ 0.7.4** (figura 07, circos). Não está no
  `requirements.txt` (arquivo não editado nesta rodada); o script de reprodução instala e o
  README registra.
- Ajuste de compatibilidade: com matplotlib 3.11 (removido `matplotlib.cm.get_cmap`) o
  nxviz quebra no import; a célula de circos aplica um *patch* de 2 linhas documentado
  no próprio código.
- Aleatoriedade: tudo determinístico; o único sorteio (remoção aleatória da análise de
  falha) usa `seed=42`.

## 6. Decisões de medida (com o porquê e o teste)

1. **WCC/SCC no digrafo** — WCC mede "existe caminho em algum sentido"; SCC, "o retorno é
   garantido". A malha é 1 WCC (176) e 2 SCC: o maior com 175, e `SBBP` sozinho (a
   decolagem única `SBBP→SBSJ`, 1 voo, 0 passageiro pago — artefato, seção 7).
2. **Comprimento médio, diâmetro, raio, centro/periferia** no maior SCC (exigem
   conexidade). Resultado: 2,4715 saltos; diâmetro 5; raio 3; centro 24; periferia 9.
3. **Eficiência global** com par inalcançável = 0, implementada à mão
   (`M.eficiencia_global`) porque `nx.global_efficiency` não aceita `DiGraph`. É a régua
   da análise de falha: pune desconexão, não só alongamento. Valor intacto: 0,4404.
4. **Intermediação (betweenness) sem peso é a medida primária** (saltos — a distância que
   o passageiro sente). Variantes de sensibilidade com custo = distância km (Spearman
   0,905 com a primária) e custo = 1/decolagens (0,656; SBGR assume o topo com 0,604).
   As variantes e a matriz de correlação estão em `resultados/intermediacao_variantes.csv`
   e `figuras/10_correlacao_medidas.png`.
5. **Clustering na projeção** (networkx não calcula em digrafo). Média 0,688; por região:
   SUL 0,778 > NORDESTE 0,720 > NORTE 0,684 > CENTRO-OESTE 0,665 > SUDESTE 0,622.
6. **k-core/k-shell/core number/degeneração** com implementação manual **por definição**
   (descascamento iterativo), validada contra `nx.core_number` no próprio notebook
   (`implementação manual == networkx: True`). Degeneração 18; miolo (k=18) com 24
   aeródromos; 64 aeródromos com core number ≤ 2.
7. **k-truss** k=3..8 na projeção: 154 nós/964 arestas no k=3; 70 nós no k=7; 61 nós no
   k=8. Comparação k-core × k-truss em `resultados/kcore_vs_ktuss.csv` e `figura 13`.
8. **Bipartido aeroporto × empresa** (`M.bipartido_aeroporto_empresa`): 176 × 73 empresas
   (no recorte doméstico; 106 no arquivo inteiro, com as internacionais) e 721 ligações;
   projeção por **Jaccard** (não contagem bruta — contagem premiaria aeroportos com muitas
   empresas sem medir sobreposição). Matriz de incidência top 18 × top 12 na `figura 14`.
9. **Jaccard de vizinhança** (`M.jaccard_vizinhanca`): descarta as próprias pontas do
   conjunto (convenção de predição de aresta). Filtro de leitura: dois lados com grau ≥ 8
   (grau 1–2 dá J = 1 por construção). Top real: `SBGL–SBGR` J=0,732 (52/71 vizinhos).
10. **Esqueleto por limiar** (`M.esqueleto_limiar`, 5% a 100% em passos de 5): 80% das
    decolagens em 283 rotas (17% do total) ligando 48 aeródromos; 40% em 66 rotas/20 nós.
    É a definição operacional do "tronco".
11. **Análise de falha — remoção de nó** (`M.impacto_remocao`): mede componentes fracas
    depois, perda do maior componente, perda de eficiência relativa e aeródromos que ficam
    sem **nenhuma rota de saída** (grau de saída 0). Removidos testados: top 10 de
    intermediação **+** top 10 de passageiros (a intuição de volume entra para comparação).
12. **Curvas alvo × aleatória** (`M.curva_remocao_alvo`, `M.curva_remocao_aleatoria`,
    seed 42): k de 1 a 12 remoções; a curva aleatória é a média de 12 sorteios com desvio.
    Com 12 remoções: eficiência 0,334 (alvo) × 0,927 (aleatória).
13. **Arestas críticas** (`M.arestas_criticas`): intermediação de aresta (sem peso) +
    `conecta_sem_aresta` (a dupla dirigida ainda se alcança sem a aresta?) + `ponte_na_projecao`.
    Top: `SBKP→SBEG` (0,0140) e `SBEG→SBKP` (0,0127); nenhuma das 15 é ponte; duas perdem
    caminho (`SBEG→SBUY`, `SBTT→SBEG`).
14. **Rotas alternativas** (`M.pares_afetados`): para **todos** os pares ordenados, uma
    árvore de caminhos por origem no grafo intacto e outra no grafo sem o obstáculo,
    comparando saltos, km e "sobrou caminho". Resultado: com SBKP fora, 5.009 pares
    afetados e 31% sem alternativa; com SBEG fora, 5.874 e 57% — é a resposta literal à
    pergunta "quais rotas alternativas restam".
15. **Distância em km das alternativas:** haversine das coordenadas (OurAirports). O campo
    `DISTÂNCIA VOADA (KM)` da ANAC tem 622 linhas nulas no recorte doméstico — foi usado
    como conferência, não como fonte.

## 7. Artefatos reconhecidos (e o que foi feito com eles)

| artefato | origem | tratamento |
|---|---|---|
| aeródromos de grau 1–2 com clustering e Jaccard = 1 | definição matemática (sem espaço para variar) | filtros de leitura (grau ≥ 8) e ressalva no texto |
| `SBBP` isolado no SCC / grau 1 | uma decolagem de posicionamento (1 voo, 0 passageiro) | mantido no dado, marcado como artefato de registro |
| `SBJD` (Jundiaí) no top-10 de intermediação com **0 passageiro pago** | voos não comerciais (posicionamento/instrução) como atalhos na medida sem peso | variante por frequência aplicada e discutida (0,045 → 0,039) |
| `NATUREZA` da ANAC contraditória (671 linhas BR–BR como `INTERNACIONAL`) | erro do campo editorial | filtro por `PAÍS`; divergência de 0,4% documentada |
| 622 linhas sem `DISTÂNCIA VOADA (KM)` | dado incompleto da ANAC | distância haversine própria, com conferência |
| projeção não dirigida nas medidas estruturais | limitação do networkx/lógica do clustering | declarado onde aparece (clustering, k-core, k-truss, pontes) |
| bola de neve distorcida (fronteira 68 nós, densidade 5× real) | amostragem por vizinhança | usado como **demonstração** do viés, não como medida |
| sazonalidade escondida na agregação anual | rede anual = união de 12 redes mensais | listado em limitações e próximos passos (análise por mês) |

## 8. Resultados — inventário de saídas

**Figuras** (`figuras/`, geradas pelos notebooks):

| figura | conteúdo | notebook |
|---|---|---|
| 01 | efeito de cada recorte na rede (nós/arestas/volume) | 01 |
| 02 | distribuição de grau, hubs, grau × volume | 02 |
| 03 | matriz de adjacência (top 40, log) | 02 |
| 04 | mapa da malha (geopandas) | 02 |
| 05 | BFS em camadas a partir de SBGR | 02 |
| 06 | amostragem por bola de neve (SBGR × SBRB) | 02 |
| 07 | circos nxviz por região | 02 |
| 08 | distribuição de distâncias + excentricidade | 03 |
| 09 | top-15 intermediação + grau × intermediação | 03 |
| 10 | Spearman entre medidas + variantes de custo | 03 |
| 11 | clustering por aeródromo e por região | 03 |
| 12 | grau × core number + mapa do core number | 03 |
| 13 | k-core × k-truss por k | 03 |
| 14 | incidência aeroporto × empresa + Jaccard de empresas | 03 |
| 15 | Jaccard de vizinhança (top 12) | 03 |
| 16 | curva do esqueleto + mapa do tronco (80%) | 03 |
| 17 | falha: remoção alvo × aleatória (eficiência e WCC) | 03 |
| 18 | mapa da rota alternativa sem SBEG | 03 |
| 19 | impacto por aeródromo testado (perda de eficiência) | 03 |

**CSVs** (`resultados/`): `tabela_recortes.csv`, `decisoes_recorte.csv`,
`base_rotas_2025.csv`, `por_regiao.csv` (01); `metricas_basicas.csv`, `graus.csv`,
`amostragem_snowball.csv` (02); `componentes.csv`, `distancia_eficiencia.csv`,
`excentricidade.csv`, `centralidades.csv`, `intermediacao_variantes.csv`,
`clustering.csv`, `clustering_por_regiao.csv`, `kcore.csv`, `ktuss.csv`,
`kcore_vs_ktuss.csv`, `projecao_empresas_top.csv`, `jaccard_vizinhanca.csv`,
`esqueleto_limiar.csv`, `articulacoes_pontes.csv`, `falha_alvo.csv`, `falha_curvas.csv`,
`arestas_criticas.csv`, `rotas_alternativas_SBKP.csv`, `rotas_alternativas_SBEG.csv`,
`ranking_criticidade.csv` (03). O `ranking_criticidade.csv` é a tabela-síntese:
intermediação + core number + perda de eficiência medida + aeródromos isolados.

## 9. Pendências desta rodada (para o Felipe)

1. **Vídeo** (≤ 15 min, YouTube não listado, todos com câmera aberta) e o link na seção
   "Vídeo" do README.
2. **Publicar**: nada foi commitado/enviado nesta rodada (decisão combinada). Antes de
   subir, revisar `README_proposto.md` → copiar para `README.md`; os `.ipynb` executados,
   `figuras/` e `resultados/` entram no commit.
3. **Link exato** do `data/2025.csv` (URL e data de acesso) no `data/README.md` e no README.
4. **Convidar Kaiky** como colaborador do repositório (não há `gh` na máquina).
5. Conferir no GitHub que `AGENTS.md` e `Avaliacao_1_Projeto.pdf` ficaram fora (`.gitignore`).
