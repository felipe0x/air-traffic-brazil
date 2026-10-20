# Dados

## Fonte

ANAC, Dados Estatísticos do Transporte Aéreo (dados abertos).

- Origem do `2025.csv`: página "Dados e Estatísticas" da ANAC:
  https://www.gov.br/anac/pt-br/assuntos/dados-e-estatisticas/dados-estatisticos
  (arquivo baixado manualmente em 16/10/2026)
- Página temática de dados abertos:
  https://www.gov.br/anac/pt-br/acesso-a-informacao/dados-abertos/areas-de-atuacao/voos-e-operacoes-aereas/dados-estatisticos-do-transporte-aereo
- Arquivo histórico completo (CSV, separador `;`, encoding latin1), desde 2000:
  https://sistemas.anac.gov.br/dadosabertos/Voos%20e%20opera%C3%A7%C3%B5es%20a%C3%A9reas/Dados%20Estat%C3%ADsticos%20do%20Transporte%20A%C3%A9reo/Dados_Estatisticos.csv

Coordenadas dos aeródromos: [OurAirports](https://davidmegginson.github.io/ourairports-data/)
(dados de domínio público), obtidas por `scripts/gerar_coordenadas.py`.

Contorno dos estados: *click_that_hood* (derivado do IBGE, simplificado), obtido por
`scripts/gerar_mapa_base.py`.

## O que há aqui

| arquivo | o que é | como é obtido |
|---|---|---|
| `2025.csv` | dado bruto da ANAC, **versionado** (9,7 MB, 37.988 linhas, 38 colunas, separador `;`, encoding latin1); voos domésticos **e** internacionais de 2025 | download manual da página acima |
| `aerodromos_coordenadas.csv` | latitude e longitude dos 176 aeródromos do recorte | `python scripts/gerar_coordenadas.py` |
| `brasil_estados.geojson` | contorno dos estados, usado como fundo dos mapas | `python scripts/gerar_mapa_base.py` |

> Como o `2025.csv` está no repositório, não há script de download: o enunciado aceita
> "dados, ou o script que os obtém".

## Estrutura do arquivo

Colunas usadas na análise:

| coluna | uso |
|---|---|
| `ANO`, `MÊS` | janela temporal (o arquivo inteiro é 2025) |
| `AEROPORTO DE {ORIGEM,DESTINO} (SIGLA)` | identidade do nó (sigla ICAO) |
| `AEROPORTO DE {ORIGEM,DESTINO} (NOME/UF/REGIÃO)` | atributos de nó |
| `AEROPORTO DE {ORIGEM,DESTINO} (PAÍS)` | filtro de voo doméstico |
| `NATUREZA` | classificação ANAC de doméstico/internacional. **Não confiável**, ver abaixo |
| `DECOLAGENS` | peso de oferta |
| `PASSAGEIROS PAGOS` | peso de demanda |

## Limpeza aplicada

1. **Janela:** `ANO == 2025` (o arquivo já é só 2025).
2. **Doméstico:** `AEROPORTO DE ORIGEM (PAÍS) == 'BRASIL'` **e**
   `AEROPORTO DE DESTINO (PAÍS) == 'BRASIL'`.
   O campo oficial `NATUREZA` **não** foi usado: a ANAC classifica como
   `INTERNACIONAL` 671 linhas que são voos internos (Curitiba→Campinas,
   Manaus→Belém, Galeão→Guarulhos, entre outras).
3. **Rota ativa:** `DECOLAGENS > 0`.
4. **Sem self-loop:** descarta origem == destino (84 rotas, 963 linhas, ex.
   `SBBR→SBBR`, `SBGR→SBGR`, `SBGL→SBGL`).
5. **Agregação:** agrupado por par (origem, destino), somando `DECOLAGENS` e
   `PASSAGEIROS PAGOS`, preservando nome, UF e região dos dois aeródromos.

Resultado do recorte: **176 nós, 1660 arestas dirigidas, densidade 0,0539**.
`SBBP` (Araxá) é o único aeródromo **sem rota de entrada** (`in_degree == 0`, por isso é o
único fora do componente fortemente conexo); nenhum aeródromo fica sem rota de saída.
