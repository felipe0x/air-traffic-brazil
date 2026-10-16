# Dados

## Fonte

ANAC — Dados Estatísticos do Transporte Aéreo (dados abertos).

- Origem usada para o `2025.csv`: página "Dados e Estatísticas" da ANAC —
  https://www.gov.br/anac/pt-br/assuntos/dados-e-estatisticas/dados-estatisticos
  (opções "Dados Estatísticos completos", "Dados dos últimos 10 anos" e ferramenta de consulta).
- Página temática de dados abertos:
  https://www.gov.br/anac/pt-br/acesso-a-informacao/dados-abertos/areas-de-atuacao/voos-e-operacoes-aereas/dados-estatisticos-do-transporte-aereo
- Arquivo histórico completo (CSV, separador `;`, encoding latin1):
  https://sistemas.anac.gov.br/dadosabertos/Voos%20e%20opera%C3%A7%C3%B5es%20a%C3%A9reas/Dados%20Estat%C3%ADsticos%20do%20Transporte%20A%C3%A9reo/Dados_Estatisticos.csv
  (≈360 MB, registros desde 2000)

## Como obter

```bash
python scripts/baixar_dados.py
```

O script baixa o arquivo oficial, seleciona a janela de interesse e grava o recorte em
`data/raw/` (não versionado). `scripts/baixar_dados.py` é a única forma de obter os dados
usada no projeto — nenhum CSV bruto é versionado no repositório.

## Estrutura esperada

- `data/raw/` — dado bruto da ANAC, como baixado (ignorado pelo git).
- `data/processed/` — tabelas derivadas (rotas agregadas, métricas por nó), geradas pelos notebooks.
- `data/externo/` — arquivos auxiliares não obtidos por script (ex. GeoJSON de estados); versionados por serem pequenos.

## Limpeza aplicada

1. Seleção da janela: ano de 2025 (coluna `ANO`).
2. Filtro de rotas ativas: `DECOLAGENS > 0`.
3. Agregação por par origem–destino, somando `DECOLAGENS` e `PASSAGEIROS PAGOS`.
4. Preservação de atributos de nó: sigla, nome, UF e região do aeródromo.

## Pendência de verificação

O arquivo `2025.csv` usado no notebook original (`Air_traffic_Brazil.ipynb`) não está no
repositório e sua origem exata precisa ser confirmada com o Felipe (presume-se recorte anual do
`Dados_Estatisticos.csv`). Enquanto isso não for confirmado, o recorte oficial é o do script acima.
