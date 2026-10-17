# Goal — pontuação máxima no Projeto Avaliação 1 (AEDII/U1)

Meta deste trabalho: fechar o projeto da Unidade 01 (malha aérea brasileira) com o **máximo
de pontos nos cinco critérios avaliáveis pelo material entregue**, deixando o vídeo para o
Felipe gravar. O barema e as rubricas vêm de `Avaliacao_1_Projeto.pdf`.

## Alvo por critério

| # | critério | pontos | definição de "pronto" (rubrica Excelente) | status |
|---|---|---|---|---|
| 1 | Problema e pergunta | 15 | Problema delimitado, pergunta clara, motivação (quem se beneficia) e explicação de **por que a estrutura da rede importa** | feito — `README_proposto.md` (Problema e pergunta) |
| 2 | Dados e modelagem | 20 | Fonte, obtenção e limpeza documentadas; nó, aresta, peso e direção justificados; **alternativas de modelagem discutidas com o efeito das escolhas (janela, filtros) nos resultados** | feito — notebook 01 + `DOCUMENTACAO.md` §2–4 |
| 3 | Uso do conteúdo do curso | 25 | Conceitos das semanas 2–6 combinados para responder à pergunta; cada medida **traduzida para o domínio**; escolhas justificadas; tabela conceito/semana/onde/para quê preenchida | feito — tabela de 25 linhas no `README_proposto.md`, com célula real |
| 4 | Análise e interpretação | 20 | Conclusões calibradas; **artefatos reconhecidos** (amostragem, projeção, dados faltantes); limitações identificadas; próximos passos concretos | feito — notebook 03 (resposta, limitações, artefatos) + `DOCUMENTACAO.md` §7 |
| 5 | Repositório e reprodutibilidade | 10 | README completo; reprodução em um comando; dependências fixadas; figuras geradas pelo código | feito — `scripts/reproduzir.sh`, `requirements.txt` (intacto), 19 figuras versionadas |
| — | Vídeo | 10 | **Fora do escopo desta execução** (Felipe grava; condição anuladora: link no README) | pendente do Felipe |

Meta desta execução: **90/100** (tudo menos vídeo).

## Entregáveis desta execução

1. `notebooks/01_dados.ipynb` — leitura, recorte e efeito das escolhas de modelagem.
2. `notebooks/02_rede.ipynb` — construção da rede, fundamentos e travessia (semanas 2–3).
3. `notebooks/03_analise.ipynb` — análise, resposta à pergunta e limitações (semanas 4–6).
4. `src/malha.py` — funções reutilizadas pelos notebooks.
5. `scripts/gerar_coordenadas.py` — obtenção reprodutível das coordenadas dos aeródromos.
6. `figuras/` — figuras numeradas, geradas pelo código.
7. `resultados/` — tabelas CSV com colunas nomeadas.
8. `README_proposto.md` — README completo proposto (o vigente não é alterado).
9. `DOCUMENTACAO.md` — cada escolha explicada e o porquê.
10. `scripts/reproduzir.sh` — reprodução em um comando.

## Restrições combinadas

- Não editar arquivos existentes (`README.md`, `AGENTS.md`, `data/README.md`,
  `notebooks/Air_traffic_Brazil.ipynb`, `.gitignore`, `requirements.txt`).
- Não subir nada para o remoto; o Felipe revisa antes.
- Todo número citado nos textos deve ser reproduzível pelo código do repositório.
- Teoria: `../Prova1/teoria/resumo_teorico.tex`/`.pdf` e, quando necessário, o livro
  `The Atlas for the Aspiring Network Scientist` (Coscia, 2ª ed.).

## Checklist de encerramento

- [x] Os três notebooks executam de ponta a ponta sem erro (kernel `python3`, via `nbconvert`).
- [x] Figuras salvas em `figuras/` com nome `NN_descricao.png`, `dpi >= 200`, títulos e eixos rotulados.
- [x] CSVs em `resultados/` com colunas nomeadas e rankings ordenados.
- [x] Tabela de conceitos (conceito · semana · onde aparece · para que serviu) preenchida com célula/função reais.
- [x] `DOCUMENTACAO.md` cobre cada decisão: recorte, pesos, filtros, algoritmos, limiares, limitações.
- [x] "Como executar" do `README_proposto.md` testado no fluxo real do repositório (nbconvert com kernel do venv).
- [x] Limitações e artefatos listados (amostragem, projeção, dados faltantes).
- [ ] (Felipe) revisar `README_proposto.md` e copiar para `README.md`; gravar o vídeo e pôr o link; commit/push; convidar Kaiky.
