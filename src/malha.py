"""Funções da análise da malha aérea doméstica brasileira (Projeto AEDII/U1).

Cada função corresponde a uma ferramenta das semanas 2 a 6 do curso; a
documentação diz o que ela mede no domínio do problema e a limitação dela.
O notebook ``apresentacao`` chama essas funções.

Convenções:
- nó = aeródromo (sigla ICAO); aresta dirigida = rota doméstica origem -> destino;
- atributos de aresta: ``decolagens``, ``passageiros`` e ``distancia_km``
  (haversine, usada como custo nas variantes de intermediação);
- recorte canônico: PAÍS == BRASIL nas duas pontas, ``DECOLAGENS > 0``,
  sem self-loops, agregado por par.
"""

from __future__ import annotations

import itertools
import math
import random
from pathlib import Path

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# caminhos do projeto
# ---------------------------------------------------------------------------

def raiz_projeto() -> Path:
    """Diretório que contém ``data/2025.csv``, subindo a partir do diretório atual."""
    atual = Path.cwd().resolve()
    for candidato in [atual, *atual.parents]:
        if (candidato / "data" / "2025.csv").exists():
            return candidato
    raise FileNotFoundError("não encontrei data/2025.csv a partir de " + str(atual))


def caminho_data() -> Path:
    return raiz_projeto() / "data"


# ---------------------------------------------------------------------------
# dados: leitura, recorte e alternativas
# ---------------------------------------------------------------------------

COL_ORIGEM = "AEROPORTO DE ORIGEM (SIGLA)"
COL_DESTINO = "AEROPORTO DE DESTINO (SIGLA)"


def carregar_bruto() -> pd.DataFrame:
    """Lê ``data/2025.csv`` exatamente como baixado da ANAC (latin1, separador ';')."""
    return pd.read_csv(
        raiz_projeto() / "data" / "2025.csv",
        sep=";",
        encoding="latin1",
        low_memory=False,
    )


def recortar(
    bruto: pd.DataFrame,
    pais: str | None = "BRASIL",
    somente_origem: bool = False,
    decolagens_maior_que_zero: bool = True,
    sem_self_loop: bool = True,
    natureza: str | None = None,
    grupo: str | None = None,
    meses: list[int] | None = None,
) -> pd.DataFrame:
    """Aplica um recorte qualquer sobre o arquivo bruto (linha = combo empresa/mês/rota).

    Cada parâmetro é uma decisão de modelagem que o notebook ``apresentacao``
    compara: ``pais`` filtra as pontas domésticas, ``natureza`` usa o campo
    oficial da ANAC, ``grupo`` separa voo regular, ``meses`` restringe a janela.
    """
    d = bruto
    if pais is not None:
        d = d[d["AEROPORTO DE ORIGEM (PAÍS)"] == pais]
        if not somente_origem:
            d = d[d["AEROPORTO DE DESTINO (PAÍS)"] == pais]
    if decolagens_maior_que_zero:
        d = d[d["DECOLAGENS"] > 0]
    if sem_self_loop:
        d = d[d[COL_ORIGEM] != d[COL_DESTINO]]
    if natureza is not None:
        d = d[d["NATUREZA"] == natureza]
    if grupo is not None:
        d = d[d["GRUPO DE VOO"] == grupo]
    if meses is not None:
        d = d[d["MÊS"].isin(meses)]
    return d.copy()


def _resumo_recorte(d: pd.DataFrame) -> dict:
    """Nós, arestas, densidade e volume de um recorte (arestas = pares distintos)."""
    pares = d.groupby([COL_ORIGEM, COL_DESTINO]).size()
    nos = sorted(set(d[COL_ORIGEM]) | set(d[COL_DESTINO]))
    n, l = len(nos), len(pares)
    return {
        "linhas": len(d),
        "nos": n,
        "arestas": l,
        "densidade": l / (n * (n - 1)) if n > 1 else float("nan"),
        "decolagens": int(d["DECOLAGENS"].sum()),
        "passageiros": int(d["PASSAGEIROS PAGOS"].sum()),
    }


def tabela_alternativas_recorte(bruto: pd.DataFrame) -> pd.DataFrame:
    """Compara recortes alternativos: é o efeito das escolhas de modelagem.

    Cada linha é uma decisão possível (incluir internacional, usar o campo
    NATUREZA em vez do PAÍS, manter self-loops, só voo regular, janela mensal)
    e o efeito dela no tamanho e na forma da rede.
    """
    variantes = {
        "tudo (com internacional)": dict(pais=None, sem_self_loop=False),
        "só origem no Brasil": dict(somente_origem=True, sem_self_loop=True),
        "BR/BR com self-loops": dict(sem_self_loop=False),
        "canônico (BR/BR, sem self-loop)": dict(),
        "campo NATUREZA = DOMÉSTICA": dict(pais=None, natureza="DOMÉSTICA"),
        "canônico, só voo REGULAR": dict(grupo="REGULAR"),
        "canônico, só janeiro": dict(meses=[1]),
        "canônico, 1º semestre": dict(meses=[1, 2, 3, 4, 5, 6]),
    }
    linhas = []
    for nome, parametros in variantes.items():
        resumo = _resumo_recorte(recortar(bruto, **parametros))
        resumo["recorte"] = nome
        linhas.append(resumo)
    tabela = pd.DataFrame(linhas).set_index("recorte")
    tabela["fracao_decolagens"] = tabela["decolagens"] / tabela.loc["tudo (com internacional)", "decolagens"]
    return tabela.reset_index()


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância em km entre dois pontos (fórmula de haversine, raio médio da Terra)."""
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _renomear_colunas(d: pd.DataFrame) -> pd.DataFrame:
    """Renomeia as colunas longas da ANAC para nomes curtos e válidos em Python."""
    return d.rename(columns={
        COL_ORIGEM: "origem",
        COL_DESTINO: "destino",
        "AEROPORTO DE ORIGEM (NOME)": "nome_origem",
        "AEROPORTO DE ORIGEM (UF)": "uf_origem",
        "AEROPORTO DE ORIGEM (REGIÃO)": "regiao_origem",
        "AEROPORTO DE DESTINO (NOME)": "nome_destino",
        "AEROPORTO DE DESTINO (UF)": "uf_destino",
        "AEROPORTO DE DESTINO (REGIÃO)": "regiao_destino",
        "EMPRESA (SIGLA)": "empresa",
    })


def agregar_rotas(d: pd.DataFrame) -> pd.DataFrame:
    """Agrega as linhas recortadas por par (origem, destino).

    Saída: uma linha por rota com os volumes somados no ano e os atributos de
    nó das duas pontas. É a tabela de arestas usada por todos os grafos.
    """
    d = _renomear_colunas(d)
    return (
        d.groupby(["origem", "destino"])
        .agg(
            decolagens=("DECOLAGENS", "sum"),
            passageiros=("PASSAGEIROS PAGOS", "sum"),
            nome_origem=("nome_origem", "first"),
            uf_origem=("uf_origem", "first"),
            regiao_origem=("regiao_origem", "first"),
            nome_destino=("nome_destino", "first"),
            uf_destino=("uf_destino", "first"),
            regiao_destino=("regiao_destino", "first"),
        )
        .reset_index()
    )


# ---------------------------------------------------------------------------
# construção do grafo
# ---------------------------------------------------------------------------

def _coordenadas() -> dict[str, tuple[float, float]]:
    tabela = pd.read_csv(caminho_data() / "aerodromos_coordenadas.csv")
    return {r.icao: (r.latitude, r.longitude) for r in tabela.itertuples()}


def posicoes(g: nx.Graph) -> dict[str, tuple[float, float]]:
    """Posição (longitude, latitude) de cada nó, para os mapas."""
    return {no: (dados["lon"], dados["lat"]) for no, dados in g.nodes(data=True)}


def fundo_mapa(eixo, cor: str = "#f2f2f2", borda: str = "#cccccc") -> bool:
    """Desenha o contorno dos estados brasileiros no eixo (cópia local do GeoJSON).

    Devolve False se o arquivo ``data/brasil_estados.geojson`` não existir: os
    mapas continuam válidos, só ficam sem o contorno. Gerar com
    ``python scripts/gerar_mapa_base.py``.
    """
    caminho = caminho_data() / "brasil_estados.geojson"
    if not caminho.exists():
        return False
    estados = gpd.read_file(caminho)
    estados.plot(ax=eixo, color=cor, edgecolor=borda, linewidth=0.6, zorder=0)
    return True


def construir_digrafo(rotas: pd.DataFrame) -> nx.DiGraph:
    """Digrafo da malha: cada linha de ``rotas`` vira uma aresta dirigida com atributos."""
    coordenadas = _coordenadas()
    g = nx.DiGraph()
    for r in rotas.itertuples():
        u, v = r.origem, r.destino
        if u not in g:
            lat, lon = coordenadas.get(u, (float("nan"), float("nan")))
            g.add_node(u, nome=r.nome_origem, uf=r.uf_origem, regiao=r.regiao_origem, lat=lat, lon=lon)
        if v not in g:
            lat, lon = coordenadas.get(v, (float("nan"), float("nan")))
            g.add_node(v, nome=r.nome_destino, uf=r.uf_destino, regiao=r.regiao_destino, lat=lat, lon=lon)
        distancia = _haversine(g.nodes[u]["lat"], g.nodes[u]["lon"], g.nodes[v]["lat"], g.nodes[v]["lon"])
        g.add_edge(u, v,
                   decolagens=float(r.decolagens),
                   passageiros=float(r.passageiros),
                   distancia_km=round(distancia, 1))
    return g


def grafo_nao_dirigido(g: nx.DiGraph) -> nx.Graph:
    """Projeção não dirigida: soma os volumes das duas direções de cada par.

    Necessária para as ferramentas que só existem em grafo não dirigido
    (triângulos, clustering, k-core, k-truss, pontes, articulações). Limitação
    declarada: um ciclo dirigido 1->2->3->1 vira triângulo na projeção.
    """
    h = nx.Graph()
    for no, atributos in g.nodes(data=True):
        h.add_node(no, **atributos)
    for u, v, dados in g.edges(data=True):
        if h.has_edge(u, v):
            h[u][v]["decolagens"] += dados["decolagens"]
            h[u][v]["passageiros"] += dados["passageiros"]
        else:
            h.add_edge(u, v, decolagens=dados["decolagens"], passageiros=dados["passageiros"])
    return h


# ---------------------------------------------------------------------------
# semana 2: fundamentos
# ---------------------------------------------------------------------------

def metricas_basicas(g: nx.Graph) -> dict:
    """Tamanho, densidade e grau médio: o cartão de identidade da rede."""
    n, l = g.number_of_nodes(), g.number_of_edges()
    graus = [d for _, d in g.degree()]
    return {
        "nos": n,
        "arestas": l,
        "densidade": nx.density(g),
        "grau_medio": float(np.mean(graus)),
        "grau_maximo": int(np.max(graus)),
        "grau_minimo": int(np.min(graus)),
    }


def tabela_graus(g: nx.DiGraph) -> pd.DataFrame:
    """Grau de entrada e de saída, simples e ponderado, por aeródromo."""
    linhas = []
    for no in g.nodes():
        entrada = g.in_degree(no)
        saida = g.out_degree(no)
        linhas.append({
            "icao": no,
            "nome": g.nodes[no].get("nome", ""),
            "uf": g.nodes[no].get("uf", ""),
            "regiao": g.nodes[no].get("regiao", ""),
            "grau_entrada": entrada,
            "grau_saida": saida,
            "grau_total": entrada + saida,
            "decolagens_entrada": g.in_degree(no, weight="decolagens"),
            "decolagens_saida": g.out_degree(no, weight="decolagens"),
            "passageiros_entrada": g.in_degree(no, weight="passageiros"),
            "passageiros_saida": g.out_degree(no, weight="passageiros"),
        })
    tabela = pd.DataFrame(linhas)
    tabela["passageiros_total"] = tabela["passageiros_entrada"] + tabela["passageiros_saida"]
    return tabela.sort_values("passageiros_total", ascending=False).reset_index(drop=True)


def ccdf(valores: pd.Series | np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """CCDF: P(K > k), a fração de nós com grau maior que k (cauda em escala log)."""
    v = np.sort(np.asarray(valores))
    x = np.unique(v)
    y = [(v > valor).mean() for valor in x]
    return x, np.asarray(y)


def matriz_adjacencia(g: nx.Graph, ordem: list) -> np.ndarray:
    """Matriz de adjacência ponderada por ``decolagens``, na ordem de nós dada.

    Em grafo não dirigido a matriz é espelhada. Arestas com ponta fora de
    ``ordem`` são ignoradas; a matriz serve para ler um recorte da topologia,
    não o grafo inteiro.
    """
    indice = {no: i for i, no in enumerate(ordem)}
    a = np.zeros((len(ordem), len(ordem)))
    for u, v, dados in g.edges(data=True):
        if u not in indice or v not in indice:
            continue
        a[indice[u], indice[v]] += dados["decolagens"]
        if not g.is_directed():
            a[indice[v], indice[u]] += dados["decolagens"]
    return a


# ---------------------------------------------------------------------------
# semana 3: travessia e amostragem
# ---------------------------------------------------------------------------

def camadas_bfs(g: nx.Graph, semente: str) -> dict[str, int]:
    """Nível de cada nó alcançável a partir da semente, em número de arestas (BFS)."""
    return dict(nx.single_source_shortest_path_length(g, semente))


def experimento_snowball(g: nx.DiGraph, semente: str, camadas_max: int = 5) -> pd.DataFrame:
    """Efeito da amostragem por bola de neve na estrutura da rede.

    Simula a coleta por vizinhança: em cada camada só se enxerga o subgrafo
    induzido pelos nós alcançados até ali. Compara tamanho, densidade, grau
    médio e clustering da amostra com a rede completa.
    """
    niveis = camadas_bfs(g, semente)
    linhas = []
    for camada in range(1, camadas_max + 1):
        amostra = [no for no, nivel in niveis.items() if nivel <= camada]
        sub = g.subgraph(amostra)
        h = grafo_nao_dirigido(sub)
        linhas.append({
            "camada": camada,
            "nos": sub.number_of_nodes(),
            "arestas": sub.number_of_edges(),
            "fracao_nos": sub.number_of_nodes() / g.number_of_nodes(),
            "densidade": nx.density(sub),
            "grau_medio": np.mean([d for _, d in sub.degree()]),
            "clustering_medio": nx.average_clustering(h),
        })
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# semana 4: conectividade, distâncias e centralidades
# ---------------------------------------------------------------------------

def maior_scc(g: nx.DiGraph) -> set:
    """Conjunto de nós do maior componente fortemente conectado."""
    return max(nx.strongly_connected_components(g), key=len)


def eficiencia_global(g: nx.Graph) -> float:
    """Eficiência global: média de 1/d(i, j) sobre todos os pares ordenados.

    E = 1/(N(N-1)) * soma_{i != j} 1/d(i,j). O networkx não implementa a versão
    para digrafo, então segue a fórmula do resumo (seção 7). O par inalcançável
    contribui 0 em vez de infinito, o que permite medir a rede fragmentada.
    """
    n = g.number_of_nodes()
    if n < 2:
        return 0.0
    total = 0.0
    for no in g:
        for alvo, distancia in nx.single_source_shortest_path_length(g, no).items():
            if alvo != no and distancia > 0:
                total += 1.0 / distancia
    return total / (n * (n - 1))


def resumo_componentes(g: nx.DiGraph) -> dict:
    """WCC e SCC: quantos componentes, tamanho do maior e quem está fora do maior SCC."""
    wccs = sorted(nx.weakly_connected_components(g), key=len, reverse=True)
    sccs = sorted(nx.strongly_connected_components(g), key=len, reverse=True)
    grande = sccs[0]
    return {
        "n_wcc": len(wccs),
        "maior_wcc": len(wccs[0]),
        "tamanhos_wcc": [len(c) for c in wccs],
        "n_scc": len(sccs),
        "maior_scc": len(grande),
        "tamanhos_scc": [len(c) for c in sccs],
        "fora_do_maior_scc": sorted(set(g) - grande),
    }


def distancia_e_eficiencia(g: nx.DiGraph) -> dict:
    """Comprimento médio, diâmetro, raio e eficiência global.

    Diâmetro, raio e comprimento médio exigem conexidade: são calculados no
    maior SCC. A eficiência global usa todos os pares (par inalcançável
    contribui 0) e dá para comparar a rede antes e depois de uma falha.
    """
    grande = maior_scc(g)
    sub = g.subgraph(grande)
    return {
        "n_scc": len(grande),
        "comprimento_medio_scc": nx.average_shortest_path_length(sub),
        "diametro_scc": nx.diameter(sub),
        "raio_scc": nx.radius(sub),
        "centro_scc": sorted(nx.center(sub)),
        "periferia_scc": sorted(nx.periphery(sub)),
        "eficiencia_global": eficiencia_global(g),
    }


def tabela_clustering(g: nx.Graph) -> pd.DataFrame:
    """Triângulos e coeficiente de agrupamento por aeródromo (grafo não dirigido)."""
    triangulos = nx.triangles(g)
    clustering = nx.clustering(g)
    linhas = [{
        "icao": no,
        "grau": g.degree(no),
        "triangulos": triangulos[no],
        "clustering": clustering[no],
        "regiao": g.nodes[no].get("regiao", ""),
    } for no in g.nodes()]
    return pd.DataFrame(linhas).sort_values(["clustering", "grau"], ascending=False).reset_index(drop=True)


def tabela_centralidades(g: nx.DiGraph) -> pd.DataFrame:
    """As quatro centralidades do curso (e as variantes de direção).

    - grau: contagem de conexões (entrada/saída);
    - proximidade: quão perto de todos. O networkx mede distância de ENTRADA
      em digrafo; a versão de saída é calculada no grafo transposto;
    - intermediação: passagem obrigatória nos caminhos mais curtos (sem peso).
      As variantes com custo entram na análise: peso é custo, não importância;
    - autovetor: importância por associação. Em digrafo o padrão usa arestas de
      ENTRADA (autoridade); no transposto, de saída (hub).
    """
    entre = nx.betweenness_centrality(g)
    prox_entrada = nx.closeness_centrality(g)
    prox_saida = nx.closeness_centrality(g.reverse())
    autovetor_entrada = nx.eigenvector_centrality(g, max_iter=1000, tol=1e-10)
    autovetor_saida = nx.eigenvector_centrality(g.reverse(), max_iter=1000, tol=1e-10)
    linhas = []
    for no in g.nodes():
        linhas.append({
            "icao": no,
            "nome": g.nodes[no].get("nome", ""),
            "uf": g.nodes[no].get("uf", ""),
            "regiao": g.nodes[no].get("regiao", ""),
            "grau_entrada": g.in_degree(no),
            "grau_saida": g.out_degree(no),
            "grau_total": g.degree(no),
            "grau_entrada_pond": g.in_degree(no, weight="passageiros"),
            "grau_saida_pond": g.out_degree(no, weight="passageiros"),
            "proximidade_entrada": prox_entrada[no],
            "proximidade_saida": prox_saida[no],
            "intermediacao": entre[no],
            "autovetor_entrada": autovetor_entrada[no],
            "autovetor_saida": autovetor_saida[no],
        })
    tabela = pd.DataFrame(linhas)
    tabela["passageiros_total"] = tabela["grau_entrada_pond"] + tabela["grau_saida_pond"]
    return tabela


def tabela_intermediacao_variantes(g: nx.DiGraph) -> pd.DataFrame:
    """Intermediação sob três definições de caminho mais curto.

    - saltos: caminho mais curto em número de arestas (padrão);
    - frequencia: custo = 1/decolagens (esperar menos é mais barato, como quem
      troca de voo prefere conexão frequente);
    - distancia: custo = distância em km (voo mais curto).

    Compara os rankings: mede o quanto "gargalo topológico" depende da noção de custo.
    """
    sem_peso = nx.betweenness_centrality(g)
    g_frequencia = nx.DiGraph()
    g_distancia = nx.DiGraph()
    for u, v, dados in g.edges(data=True):
        g_frequencia.add_edge(u, v, custo=1.0 / max(dados["decolagens"], 1.0))
        g_distancia.add_edge(u, v, custo=max(dados["distancia_km"], 1.0))
    por_frequencia = nx.betweenness_centrality(g_frequencia, weight="custo")
    por_distancia = nx.betweenness_centrality(g_distancia, weight="custo")
    return pd.DataFrame({
        "icao": list(g.nodes()),
        "intermediacao_saltos": [sem_peso[n] for n in g.nodes()],
        "intermediacao_frequencia": [por_frequencia[n] for n in g.nodes()],
        "intermediacao_distancia": [por_distancia[n] for n in g.nodes()],
    })


# ---------------------------------------------------------------------------
# semana 5: decomposição em núcleos
# ---------------------------------------------------------------------------

def tabela_kcore(g: nx.Graph) -> pd.DataFrame:
    """Core number de cada nó, com grau e região, ordenado do miolo para a periferia."""
    core = nx.core_number(g)
    return (
        pd.DataFrame({
            "icao": list(g.nodes()),
            "core_number": [core[n] for n in g.nodes()],
            "grau": [g.degree(n) for n in g.nodes()],
            "regiao": [g.nodes[n].get("regiao", "") for n in g.nodes()],
        })
        .sort_values(["core_number", "grau"], ascending=False)
        .reset_index(drop=True)
    )


def tabela_ktuss(g: nx.Graph, ks: range = range(3, 8)) -> pd.DataFrame:
    """Tamanho do k-truss: subgrafo em que toda aresta participa de >= k-2 triângulos."""
    linhas = []
    for k in ks:
        try:
            truss = nx.k_truss(g, k)
        except nx.NetworkXError:
            continue
        linhas.append({"k": k, "nos": truss.number_of_nodes(), "arestas": truss.number_of_edges()})
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# semana 6: bipartido, projeção, Jaccard e esqueleto por limiar
# ---------------------------------------------------------------------------

def bipartido_aeroporto_empresa(d: pd.DataFrame) -> nx.Graph:
    """Rede bipartida aeroporto x empresa aérea.

    Ligação existe quando a empresa operou a rota de/para o aeroporto na janela;
    o peso é o total de decolagens. A projeção para aeroportos (adiante) mede
    similaridade operacional: dois aeródromos ligados às mesmas empresas.
    """
    d = _renomear_colunas(d)
    b = nx.Graph()
    for aeroporto in set(d["origem"]) | set(d["destino"]):
        b.add_node(("aeroporto", aeroporto))
    for empresa in set(d["empresa"]):
        b.add_node(("empresa", empresa))
    for linha in d.itertuples():
        for lado in (linha.origem, linha.destino):
            no_aero = ("aeroporto", lado)
            no_emp = ("empresa", linha.empresa)
            if b.has_edge(no_aero, no_emp):
                b[no_aero][no_emp]["decolagens"] += linha.DECOLAGENS
            else:
                b.add_edge(no_aero, no_emp, decolagens=linha.DECOLAGENS)
    return b


def jaccard_empresas(b: nx.Graph, minimo_empresas: int = 2) -> pd.DataFrame:
    """Projeção do bipartido com peso de Jaccard.

    J(a,b) = |E(a) ∩ E(b)| / |E(a) ∪ E(b)|, onde E(x) é o conjunto de empresas
    do aeroporto x. Contagem bruta devolveria pares que só aparecem juntos
    porque ambos têm muitas empresas; o Jaccard normaliza e revela os pares
    exclusivos, candidatos a substitutos operacionais.
    """
    empresas = {
        aeroporto: {v for _, v in b.neighbors(("aeroporto", aeroporto))}
        for _, aeroporto in (n for n in b.nodes if n[0] == "aeroporto")
    }
    linhas = []
    for a, c in itertools.combinations(sorted(empresas), 2):
        e_a, e_c = empresas[a], empresas[c]
        uniao = e_a | e_c
        if len(uniao) == 0:
            continue
        intersecao = e_a & e_c
        if len(intersecao) < minimo_empresas:
            continue
        linhas.append({
            "aeroporto_a": a,
            "aeroporto_b": c,
            "empresas_comuns": len(intersecao),
            "empresas_uniao": len(uniao),
            "jaccard": len(intersecao) / len(uniao),
        })
    return pd.DataFrame(linhas).sort_values("jaccard", ascending=False).reset_index(drop=True)


def jaccard_vizinhanca(g: nx.Graph) -> pd.DataFrame:
    """Similaridade de Jaccard entre os vizinhos das duas pontas de cada aresta.

    J(u,v) = |N(u) ∩ N(v)| / |N(u) ∪ N(v)| com os conjuntos descontando u e v
    (convenção para predição de aresta). Responde: os vizinhos de u e v são os
    mesmos? Se sim, a rota é redundante para a região e a rede tolera a queda
    de uma das duas pontas; se não, cada aresta conecta "mundos" diferentes.
    """
    linhas = []
    for u, v in g.edges():
        viz_u = set(g.neighbors(u)) - {u, v}
        viz_v = set(g.neighbors(v)) - {u, v}
        uniao = viz_u | viz_v
        if not uniao:
            continue
        linhas.append({
            "origem": u,
            "destino": v,
            "grau_origem": g.degree(u),
            "grau_destino": g.degree(v),
            "vizinhos_comuns": len(viz_u & viz_v),
            "vizinhos_uniao": len(uniao),
            "jaccard": len(viz_u & viz_v) / len(uniao),
            "decolagens": g[u][v]["decolagens"],
        })
    return pd.DataFrame(linhas).sort_values("jaccard", ascending=False).reset_index(drop=True)


def esqueleto_limiar(g: nx.DiGraph, fracoes: list[float] | None = None) -> pd.DataFrame:
    """Esqueleto por limiar: mantém as rotas mais movimentadas até cobrir x% dos voos.

    Para cada fração de cobertura, mede o que resta da rede. O ponto em que o
    maior componente fraco encolhe é o limite em que o "tronco" deixa de ligar
    o país; é o critério para escolher o que não pode cair.
    """
    if fracoes is None:
        fracoes = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0]
    arestas = sorted(g.edges(data=True), key=lambda e: e[2]["decolagens"], reverse=True)
    total = sum(d["decolagens"] for _, _, d in arestas)
    linhas = []
    for fracao in fracoes:
        corte = fracao * total
        h = nx.DiGraph()
        h.add_nodes_from(g.nodes())
        acumulado = 0.0
        for u, v, dados in arestas:
            if acumulado >= corte:
                break
            h.add_edge(u, v, **dados)
            acumulado += dados["decolagens"]
        wcc = sorted(nx.weakly_connected_components(h), key=len, reverse=True)
        scc = sorted(nx.strongly_connected_components(h), key=len, reverse=True)
        linhas.append({
            "fracao_alvo": fracao,
            "fracao_real": acumulado / total,
            "arestas": h.number_of_edges(),
            "nos": h.number_of_nodes(),
            "nos_com_conexao": sum(1 for no in h if h.degree(no) > 0),
            "componentes_fracos": len(wcc),
            "maior_wcc": len(wcc[0]),
            "maior_scc": len(scc[0]),
            "decolagens_cobertas": acumulado,
        })
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# análise de falha e rotas alternativas (a pergunta do projeto)
# ---------------------------------------------------------------------------

def impacto_remocao(g: nx.DiGraph, no: str) -> dict:
    """O que muda na rede quando um aeródromo fica indisponível.

    Mede o efeito no maior componente fraco (fragmentação), na eficiência
    global (alcance médio em número de saltos, com par inalcançável contando 0)
    e quem perde ligação direta: aeródromos que ficam sem rota de saída.
    """
    if no not in g:
        raise KeyError(f"{no} não está no grafo")
    h = g.copy()
    h.remove_node(no)
    base = resumo_componentes(g)
    depois = resumo_componentes(h)
    efic_base = eficiencia_global(g)
    efic_depois = eficiencia_global(h)
    sem_saida = sorted([x for x in h if h.out_degree(x) == 0])
    sem_entrada = sorted([x for x in h if h.in_degree(x) == 0])
    return {
        "icao_removido": no,
        "nos_restantes": h.number_of_nodes(),
        "componentes_antes": base["n_wcc"],
        "componentes_depois": depois["n_wcc"],
        "maior_wcc_antes": base["maior_wcc"],
        "maior_wcc_depois": depois["maior_wcc"],
        "perda_maior_wcc": base["maior_wcc"] - depois["maior_wcc"],
        "eficiencia_antes": efic_base,
        "eficiencia_depois": efic_depois,
        "perda_eficiencia_relativa": (efic_base - efic_depois) / efic_base,
        "aerodromos_sem_rota_saida": len(sem_saida),
        "lista_sem_rota_saida": sem_saida,
        "aerodromos_sem_rota_entrada": len(sem_entrada),
        "lista_sem_rota_entrada": sem_entrada,
    }


def _efeito_remocao(h: nx.DiGraph, eficiencia_base: float, wcc_base: int) -> dict:
    """Efeito imediato de uma remoção: eficiência e maior WCC relativos, e nós isolados."""
    maior = len(max(nx.weakly_connected_components(h), key=len))
    return {
        "eficiencia_relativa": eficiencia_global(h) / eficiencia_base,
        "maior_wcc_relativo": maior / wcc_base,
        "nos_isolados": sum(1 for x in h if h.degree(x) == 0),
    }


def curva_remocao_alvo(g: nx.DiGraph, ordem: list[str], k_max: int = 12) -> pd.DataFrame:
    """Curva de robustez sob remoção dos k primeiros da ordem dada (ex.: betweenness)."""
    eficiencia_0 = eficiencia_global(g)
    wcc_0 = len(max(nx.weakly_connected_components(g), key=len))
    h = g.copy()
    linhas = [{"k": 0, "eficiencia_relativa": 1.0, "maior_wcc_relativo": 1.0, "nos_isolados": 0}]
    for k, no in enumerate([x for x in ordem if x in g][:k_max], start=1):
        h.remove_node(no)
        linhas.append({"k": k, **_efeito_remocao(h, eficiencia_0, wcc_0)})
    return pd.DataFrame(linhas)


def curva_remocao_aleatoria(
    g: nx.DiGraph, k_max: int = 12, sorteios: int = 12, seed: int = 42
) -> pd.DataFrame:
    """Mesma curva, removendo nós aleatórios: a linha de base para comparar.

    A distância entre a curva aleatória e a curva alvo mostra se a rede tem
    alvos preferenciais: se derrubar os hubs dói muito mais do que sortear
    aeródromos ao acaso, a rede é concentrada (e o ataque informado compensa).
    """
    rng = random.Random(seed)
    eficiencia_0 = eficiencia_global(g)
    wcc_0 = len(max(nx.weakly_connected_components(g), key=len))
    acumulado = {k: [] for k in range(1, k_max + 1)}
    for _ in range(sorteios):
        ordem = list(g.nodes())
        rng.shuffle(ordem)
        h = g.copy()
        for k, no in enumerate(ordem[:k_max], start=1):
            h.remove_node(no)
            efeito = _efeito_remocao(h, eficiencia_0, wcc_0)
            acumulado[k].append((efeito["eficiencia_relativa"], efeito["maior_wcc_relativo"]))
    linhas = []
    for k in range(1, k_max + 1):
        valores = acumulado[k]
        linhas.append({
            "k": k,
            "eficiencia_relativa_media": float(np.mean([v[0] for v in valores])),
            "eficiencia_relativa_desvio": float(np.std([v[0] for v in valores])),
            "maior_wcc_relativo_medio": float(np.mean([v[1] for v in valores])),
            "sorteios": sorteios,
            "seed": seed,
        })
    return pd.DataFrame(linhas)


def arestas_criticas(g: nx.DiGraph, k: int = 15) -> pd.DataFrame:
    """Intermediação de aresta: a rota que mais corta caminhos mais curtos.

    Para cada aresta, mede-se também o que acontece quando ela sai: os dois
    sentidos ainda se alcançam? em quantos saltos? A coluna
    ``ponte_na_projecao`` marca a rota cuja remoção (em qualquer sentido)
    separa a projeção não dirigida em dois pedaços.
    """
    pontes = {frozenset(aresta) for aresta in nx.bridges(grafo_nao_dirigido(g))}
    entre = nx.edge_betweenness_centrality(g)
    linhas = []
    for (u, v), valor in entre.items():
        sem_aresta = g.copy()
        sem_aresta.remove_edge(u, v)
        alcanca = nx.has_path(sem_aresta, u, v)
        saltos = nx.shortest_path_length(sem_aresta, u, v) if alcanca else np.nan
        linhas.append({
            "origem": u,
            "destino": v,
            "intermediacao_aresta": valor,
            "decolagens": g[u][v]["decolagens"],
            "passageiros": g[u][v]["passageiros"],
            "conecta_sem_aresta": alcanca,
            "saltos_sem_aresta": saltos,
            "ponte_na_projecao": frozenset((u, v)) in pontes,
        })
    tabela = pd.DataFrame(linhas).sort_values("intermediacao_aresta", ascending=False).reset_index(drop=True)
    return tabela.head(k)


def _km_do_caminho(g: nx.DiGraph, caminho: list[str]) -> float:
    """Distância geográfica somada ao longo de um caminho de nós."""
    return sum(g[caminho[i]][caminho[i + 1]]["distancia_km"] for i in range(len(caminho) - 1))


def pares_afetados(g: nx.DiGraph, no: str) -> pd.DataFrame:
    """Pares de aeroportos cujo caminho mais curto passa pelo aeródromo ``no``.

    Para a pergunta do projeto: se um aeródromo fica indisponível, quais ligações
    perdem o caminho mais curto e quanto elas alongam. Mede-se o antes e o depois
    em saltos e em km, e se sobra caminho nenhum.

    Estratégia: uma árvore de caminhos por origem no grafo completo e outra no
    grafo sem ``no``; para cada destino, compara.
    """
    h = g.copy()
    h.remove_node(no)

    linhas = []
    for origem in g:
        if origem not in h:
            continue
        antes_map = nx.single_source_shortest_path(g, origem)
        depois_map = nx.single_source_shortest_path(h, origem)
        for destino, antes in antes_map.items():
            if destino == origem or no not in antes[1:-1]:
                continue
            depois = depois_map.get(destino)
            linhas.append({
                "origem": origem,
                "destino": destino,
                "saltos_antes": len(antes) - 1,
                "saltos_depois": len(depois) - 1 if depois else np.nan,
                "delta_saltos": (len(depois) - len(antes)) if depois else np.nan,
                "km_antes": round(_km_do_caminho(g, antes), 1),
                "km_depois": round(_km_do_caminho(h, depois), 1) if depois else np.nan,
                "sobrou_caminho": bool(depois),
                "caminho_antes": " -> ".join(antes),
                "caminho_depois": " -> ".join(depois) if depois else "",
            })
    tabela = pd.DataFrame(linhas)
    if tabela.empty:
        return tabela
    return (
        tabela.sort_values(["sobrou_caminho", "delta_saltos", "km_antes"],
                           ascending=[True, False, False])
        .reset_index(drop=True)
    )
