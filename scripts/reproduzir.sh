#!/usr/bin/env bash
# Reprodução completa do projeto em um comando (a partir da raiz do repositório):
#
#     bash scripts/reproduzir.sh
#
# O que faz:
#   1. cria o ambiente virtual local (.venv) e instala as dependências fixadas
#      em requirements.txt;
#   2. regenera os auxiliares de dados se estiverem faltando
#      (coordenadas dos aeródromos e contorno dos estados; requer internet);
#   3. executa o notebook de análise, sobrescrevendo figuras/ e resultados/
#      com as saídas geradas.
#
# Requisitos: Python 3.12 e internet apenas para instalar dependências e
# (se faltarem) regenerar os auxiliares. O dado principal, data/2025.csv,
# já está versionado no repositório.

set -euo pipefail
cd "$(dirname "$0")/.."

PY=${PYTHON:-python3}

echo "== ambiente =="
if [ ! -d .venv ]; then
  "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo "== dados auxiliares =="
if [ ! -f data/aerodromos_coordenadas.csv ]; then
  python scripts/gerar_coordenadas.py
fi
if [ ! -f data/brasil_estados.geojson ]; then
  python scripts/gerar_mapa_base.py
fi

echo "== notebook =="
jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.kernel_name=python3 \
  --ExecutePreprocessor.timeout=1800 notebooks/apresentacao.ipynb

echo "== pronto =="
echo "figuras em figuras/ | tabelas em resultados/ | notebook executado em notebooks/"
