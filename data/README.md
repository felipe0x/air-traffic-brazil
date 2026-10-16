# Dados

## Fonte

ANAC — Dados Estatísticos do Transporte Aéreo (dados abertos).

- Origem do `2025.csv`: página "Dados e Estatísticas" da ANAC —
  https://www.gov.br/anac/pt-br/assuntos/dados-e-estatisticas/dados-estatisticos
- Página temática de dados abertos:
  https://www.gov.br/anac/pt-br/acesso-a-informacao/dados-abertos/areas-de-atuacao/voos-e-operacoes-aereas/dados-estatisticos-do-transporte-aereo
- Arquivo histórico completo (CSV, separador `;`, encoding latin1), desde 2000:
  https://sistemas.anac.gov.br/dadosabertos/Voos%20e%20opera%C3%A7%C3%B5es%20a%C3%A9reas/Dados%20Estat%C3%ADsticos%20do%20Transporte%20A%C3%A9reo/Dados_Estatisticos.csv

## O que há aqui

- `2025.csv` — arquivo baixado da ANAC, **versionado no repositório** (9,7 MB, 37.988 linhas,
  38 colunas, separador `;`, encoding latin1). Contém voos domésticos **e** internacionais
  de 2025.

> Como o arquivo está no repositório, não há script de obtenção: o enunciado aceita
> "dados, ou o script que os obtém".

> A preencher: link exato do arquivo baixado e data de acesso.

## Estrutura do arquivo

Colunas usadas na análise:

| coluna | uso |
|---|---|
| `ANO`, `MÊS` | janela temporal (o arquivo inteiro é 2025) |
| `AEROPORTO DE {ORIGEM,DESTINO} (SIGLA)` | identidade do nó (sigla ICAO) |
| `AEROPORTO DE {ORIGEM,DESTINO} (NOME/UF/REGIÃO)` | atributos de nó |
| `AEROPORTO DE {ORIGEM,DESTINO} (PAÍS)` | filtro de voo doméstico |
| `NATUREZA` | classificação ANAC de doméstico/internacional — **não confiável**, ver abaixo |
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
`SBBP` (Araxá) é o único aeródromo sem rota de saída.

## Pendências

- Registrar o link exato do arquivo baixado e a data de acesso.
- Coordenadas dos aeródromos: hoje vêm de um dicionário manual dentro do notebook.
  Falta uma fonte oficial e versionada.
