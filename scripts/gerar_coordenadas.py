"""Obtém as coordenadas dos aeródromos usados na análise.

Fonte: OurAirports (dados de domínio público, compilados a partir de bases
oficiais), arquivo ``airports.csv`` distribuído em
https://davidmegginson.github.io/ourairports-data/airports.csv

O script baixa o arquivo, filtra os aeródromos brasileiros e grava o subconjunto
usado pelos notebooks em ``data/aerodromos_coordenadas.csv`` (pequeno, versionado).
O restante dos dados do projeto é o ``data/2025.csv`` da ANAC.

Uso:
    python scripts/gerar_coordenadas.py

Saída:
    data/aerodromos_coordenadas.csv
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from urllib.request import urlopen

import pandas as pd

URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"
SAIDA = Path(__file__).resolve().parent.parent / "data" / "aerodromos_coordenadas.csv"


def siglas_usadas() -> set[str]:
    """Siglas ICAO que aparecem no recorte canônico do data/2025.csv."""
    raiz = SAIDA.parent.parent
    bruto = pd.read_csv(raiz / "data" / "2025.csv", sep=";", encoding="latin1", low_memory=False)
    origem = "AEROPORTO DE ORIGEM (SIGLA)"
    destino = "AEROPORTO DE DESTINO (SIGLA)"
    domestico = (
        (bruto["AEROPORTO DE ORIGEM (PAÍS)"] == "BRASIL")
        & (bruto["AEROPORTO DE DESTINO (PAÍS)"] == "BRASIL")
        & (bruto["DECOLAGENS"] > 0)
        & (bruto[origem] != bruto[destino])
    )
    recorte = bruto[domestico]
    return set(recorte[origem]) | set(recorte[destino])


def main() -> None:
    siglas = siglas_usadas()
    print(f"aeródromos no recorte canônico: {len(siglas)}")

    with urlopen(URL, timeout=120) as resposta:
        import io

        bruto = pd.read_csv(io.BytesIO(resposta.read()), low_memory=False)

    brasileiros = bruto[bruto["iso_country"] == "BR"].copy()

    # um aeródromo pode ter a sigla em colunas diferentes (icao_code, gps_code, ident)
    registros = {}
    for _, linha in brasileiros.iterrows():
        for coluna in ("icao_code", "gps_code", "ident", "local_code"):
            codigo = linha.get(coluna)
            if isinstance(codigo, str) and codigo in siglas and codigo not in registros:
                registros[codigo] = {
                    "icao": codigo,
                    "nome": linha["name"],
                    "municipio": linha["municipality"],
                    "tipo": linha["type"],
                    "latitude": linha["latitude_deg"],
                    "longitude": linha["longitude_deg"],
                }

    tabela = pd.DataFrame(registros.values(), columns=["icao", "nome", "municipio", "tipo", "latitude", "longitude"])
    tabela = tabela.sort_values("icao").reset_index(drop=True)
    faltando = sorted(siglas - set(tabela["icao"]))
    print(f"coordenadas encontradas: {len(tabela)} | faltando: {len(faltando)} {faltando}")

    tabela["fonte"] = f"OurAirports airports.csv, acesso em {date.today().isoformat()}"
    tabela.to_csv(SAIDA, index=False)
    print(f"gravado: {SAIDA}")


if __name__ == "__main__":
    main()
