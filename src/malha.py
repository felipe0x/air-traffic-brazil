"""Funções da análise da malha aérea doméstica brasileira (Projeto AEDII/U1).

Cada função corresponde a uma ferramenta das semanas 2 a 6 do curso; a
documentação diz o que ela mede no domínio do problema e a limitação dela.
O notebook ``apresentacao`` chama essas funções.

Convenções:
- nó = aeródromo (sigla ICAO); aresta dirigida = rota doméstica origem -> destino;
- atributos de aresta: ``decolagens``, ``passageiros`` e ``distancia_km``
  (haversine);
- recorte do projeto: PAÍS == BRASIL nas duas pontas, ``DECOLAGENS > 0``,
  sem self-loops, agregado por par.
"""

from __future__ import annotations

import math
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
# dados: leitura e recorte
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


def _mascara_domestica(bruto: pd.DataFrame) -> pd.Series:
    """Linhas de 2025, domésticas, com decolagem e sem self-loop."""
    return (
        (bruto["ANO"] == 2025)
        & (bruto["AEROPORTO DE ORIGEM (PAÍS)"] == "BRASIL")
        & (bruto["AEROPORTO DE DESTINO (PAÍS)"] == "BRASIL")
        & (bruto["DECOLAGENS"] > 0)
        & (bruto[COL_ORIGEM] != bruto[COL_DESTINO])
    )


def recortar(bruto: pd.DataFrame) -> pd.DataFrame:
    """Aplica o recorte do projeto ao arquivo bruto da ANAC.

    A pergunta é sobre a malha doméstica e o efeito de uma interrupção, então
    entram as linhas de 2025 com origem e destino no Brasil, pelo menos uma
    decolagem e origem diferente do destino. O campo ``NATUREZA`` não é usado
    porque classifica linhas domésticas como internacionais; ``PAÍS`` é o
    critério direto. A agregação por par fica em :func:`agregar_rotas`.
    """
    return bruto[_mascara_domestica(bruto)].copy()


def _resumo_recorte(d: pd.DataFrame) -> dict:
    """Linhas, nós e rotas distintas de um recorte."""
    pares = d.groupby([COL_ORIGEM, COL_DESTINO]).size()
    nos = set(d[COL_ORIGEM]) | set(d[COL_DESTINO])
    return {"linhas": len(d), "nos": len(nos), "rotas": len(pares)}


def tabela_decisoes_recorte(bruto: pd.DataFrame) -> pd.DataFrame:
    """Decisões do recorte e o efeito da alternativa descartada.

    A pergunta define o recorte; a coluna ``alternativa`` registra o caminho
    não escolhido e ``efeito`` mostra o tamanho da rede se ele fosse usado.
    Assim, a justificativa não é só conceitual: o custo de cada escolha fica
    medido no mesmo código que constrói a rede.
    """
    doméstico = _mascara_domestica(bruto)
    ativo_sem_self = (
        (bruto["ANO"] == 2025)
        & (bruto["DECOLAGENS"] > 0)
        & (bruto[COL_ORIGEM] != bruto[COL_DESTINO])
    )
    com_self = (
        (bruto["ANO"] == 2025)
        & (bruto["AEROPORTO DE ORIGEM (PAÍS)"] == "BRASIL")
        & (bruto["AEROPORTO DE DESTINO (PAÍS)"] == "BRASIL")
        & (bruto["DECOLAGENS"] > 0)
    )
    regulares = doméstico & (bruto["GRUPO DE VOO"] == "REGULAR")
    janeiro = doméstico & (bruto["MÊS"] == 1)
    natureza = (
        (bruto["ANO"] == 2025)
        & (bruto["DECOLAGENS"] > 0)
        & (bruto[COL_ORIGEM] != bruto[COL_DESTINO])
        & (bruto["NATUREZA"] == "DOMÉSTICA")
    )
    passageiros = (
        (bruto["ANO"] == 2025)
        & (bruto["AEROPORTO DE ORIGEM (PAÍS)"] == "BRASIL")
        & (bruto["AEROPORTO DE DESTINO (PAÍS)"] == "BRASIL")
        & (bruto["PASSAGEIROS PAGOS"] > 0)
        & (bruto[COL_ORIGEM] != bruto[COL_DESTINO])
    )

    def efeito(mascara: pd.Series) -> str:
        resumo = _resumo_recorte(bruto[mascara])
        rotas = f"{resumo['rotas']:,}".replace(",", ".")
        return f"{resumo['nos']} nós, {rotas} rotas"

    return pd.DataFrame([
        dict(decisao="Janela e agregação", escolha="ano de 2025, por par origem-destino",
             porque="reduz sazonalidade; par preserva conectividade",
             alternativa="só janeiro", efeito=efeito(janeiro)),
        dict(decisao="Malha doméstica", escolha="origem e destino no Brasil",
             porque="a pergunta é o isolamento nacional",
             alternativa="incluir internacional", efeito=efeito(ativo_sem_self)),
        dict(decisao="Campo de domesticidade", escolha="PAÍS das duas pontas",
             porque="critério direto; NATUREZA erra 671 linhas",
             alternativa="NATUREZA", efeito=efeito(natureza)),
        dict(decisao="Rota ativa", escolha="DECOLAGENS > 0",
             porque="operação efetiva, não venda de assento",
             alternativa="PASSAGEIROS > 0", efeito=efeito(passageiros)),
        dict(decisao="Self-loops", escolha="remover origem = destino",
             porque="self-loop não altera alcance nem caminho",
             alternativa="manter", efeito=efeito(com_self)),
        dict(decisao="Tipo de voo", escolha="todos os grupos",
             porque="malha operada, não só oferta regular",
             alternativa="só REGULAR", efeito=efeito(regulares)),
    ])


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
    (k-core e Jaccard). Limitação declarada: um ciclo dirigido 1->2->3->1
    vira triângulo na projeção.
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


# ---------------------------------------------------------------------------
# semana 3: travessia
# ---------------------------------------------------------------------------

def camadas_bfs(g: nx.Graph, semente: str) -> dict[str, int]:
    """Nível de cada nó alcançável a partir da semente, em número de arestas (BFS)."""
    return dict(nx.single_source_shortest_path_length(g, semente))


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
            if alvo != no:
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
        "n_scc": len(sccs),
        "maior_scc": len(grande),
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
        "comprimento_medio_scc": nx.average_shortest_path_length(sub),
        "diametro_scc": nx.diameter(sub),
        "raio_scc": nx.radius(sub),
        "centro_scc": sorted(nx.center(sub)),
        "periferia_scc": sorted(nx.periphery(sub)),
        "eficiencia_global": eficiencia_global(g),
    }


def tabela_centralidades(g: nx.DiGraph) -> pd.DataFrame:
    """As quatro centralidades do curso.

    - grau: contagem de conexões (entrada/saída);
    - proximidade: quão perto de todos. O networkx mede distância de ENTRADA
      em digrafo; a versão de saída é calculada no grafo transposto;
    - intermediação: passagem obrigatória nos caminhos mais curtos (sem peso).
      Peso é custo, não importância; a medida usa saltos;
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


# ---------------------------------------------------------------------------
# semana 6: Jaccard de vizinhança
# ---------------------------------------------------------------------------

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


def arestas_criticas(g: nx.DiGraph, k: int = 15) -> pd.DataFrame:
    """Intermediação de aresta: a rota que mais corta caminhos mais curtos.

    Para cada aresta, mede-se também o que acontece quando ela sai: os dois
    sentidos ainda se alcançam? em quantos saltos?
    """
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
