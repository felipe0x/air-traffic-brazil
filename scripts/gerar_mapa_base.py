"""Baixa e simplifica o contorno dos estados brasileiros para os mapas.

Fonte: GitHub ``codeforamerica/click_that_hood``, arquivo ``brazil-states.geojson``
(derivado de dados públicos do IBGE). O arquivo é simplificado (tolerância 0,05°)
para ficar leve e é gravado em ``data/brasil_estados.geojson``; os notebooks usam
a cópia local, sem depender de rede na hora da execução.

Uso:
    python scripts/gerar_mapa_base.py

Saída:
    data/brasil_estados.geojson
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd

URL = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
SAIDA = Path(__file__).resolve().parent.parent / "data" / "brasil_estados.geojson"


def main() -> None:
    estados = gpd.read_file(URL)
    print(f"estados: {len(estados)} | colunas: {list(estados.columns)}")
    estados = estados[["name", "geometry"]].to_crs(4326)
    simplificado = estados.copy()
    simplificado["geometry"] = estados.geometry.simplify(0.05)
    simplificado.to_file(SAIDA, driver="GeoJSON")
    print(f"gravado: {SAIDA} ({SAIDA.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
