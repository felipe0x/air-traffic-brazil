# Malha aérea brasileira: aeroportos e rotas críticos e alternativas de contorno

Projeto da Unidade 01 de Algoritmos e Estrutura de Dados II (Grafos) — UFRN.

## Integrantes

Felipe Rocha Silva · Kaiky Hanry Alencar Fernandes

## Vídeo

**A preencher** — vídeo no YouTube, até 15 minutos no total, todos os integrantes com câmera aberta e rosto visível.

> Requisito do enunciado: sem o link explícito aqui, a nota do projeto é zero.

## Problema e pergunta

A malha aérea doméstica brasileira é concentrada: poucos aeródromos respondem pela maior parte dos voos e ligam regiões que, sem eles, deixariam de ter ligação direta. Uma indisponibilidade (interdição de pista, evento climático, atraso sistêmico) em um ponto desses não afeta apenas quem passa por ele, mas a possibilidade de chegar a outros aeroportos.

**Pergunta:** quais aeroportos e quais rotas são críticos para a conectividade da malha aérea doméstica brasileira e, quando um deles fica indisponível, quais rotas alternativas restam?

Quem se beneficia da resposta: quem precisa decidir contingência na malha (operador, regulador, gestor aeroportuário).

> Rascunho — revisar redação e fechar a motivação.

## Dados (fonte, como obter, limpeza)

- **Fonte:** ANAC — Dados Estatísticos do Transporte Aéreo (dados abertos).
  Origem do recorte usado: https://www.gov.br/anac/pt-br/assuntos/dados-e-estatisticas/dados-estatisticos
- **Como obter:** `python scripts/baixar_dados.py` (a implementar). Nenhum CSV bruto é versionado; a obtenção é reproduzível pelo script.
- **Formato:** CSV, separador `;`, encoding latin1.
- **Limpeza:** seleção da janela anual; filtro `DECOLAGENS > 0` para rotas ativas; agregação por par origem–destino somando `DECOLAGENS` e `PASSAGEIROS PAGOS`; preservação de sigla, nome, UF e região do aeródromo.

> A preencher: link do arquivo exato baixado e data de acesso.

## Modelagem (nó, aresta, peso, direção, o que ficou de fora)

- **Nó:** aeródromo, identificado pela sigla ICAO (ex. `SBGR`).
- **Aresta:** rota doméstica origem → destino observada na janela.
- **Direção:** dirigido — os volumes de ida e volta diferem.
- **Peso:** `DECOLAGENS` (oferta) e `PASSAGEIROS PAGOS` (demanda) como atributos distintos; cada cálculo declara qual usa.
- **Fica de fora:** malha internacional, voos com escala (o dado é ponto a ponto), frequência por dia/hora, tipo de aeronave, preço, carga e capacidade operacional do aeroporto.
- **Hipóteses:** janela anual agregada; ausência de aresta = rota inexistente na janela.

## Conteúdo do curso utilizado

| conceito | semana | onde aparece | para que serviu |
|---|---|---|---|
| digrafo, atributos de nó e aresta | 2 | | |
| densidade | 2 | | |
| distribuição de grau | 2 | | |
| BFS/DFS | 3 | | |
| grau de entrada e de saída | 3 | | |
| caminhos e distâncias | 4 | | |
| componentes (WCC/SCC) | 4 | | |
| diâmetro e eficiência | 4 | | |
| centralidades (grau, closeness, betweenness, eigenvector) | 4 | | |
| triângulos e clustering | 4 | | |
| k-core, k-shell, core number, degeneracy | 5 | | |
| esqueleto por limiar e Jaccard | 6 | | |

> A preencher: localizar cada conceito (notebook + célula/função) e o que ele respondeu no problema.

## Como executar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/baixar_dados.py
jupyter lab
```

> A preencher: ordem dos notebooks e o comando de reprodução completa. Testar em máquina limpa antes de entregar.

## Resultados

> A preencher.

## Limitações e próximos passos

> A preencher.

## Referências

- ANAC. Dados Estatísticos do Transporte Aéreo. https://www.gov.br/anac/pt-br/assuntos/dados-e-estatisticas/dados-estatisticos
