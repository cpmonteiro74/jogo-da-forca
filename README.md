# Jogo da Forca

Jogo da Forca em português com interface visual, em duas versões:

- **`forca.html`**: versão web autocontida, sem dependências. Basta abrir no navegador. Funciona offline, no computador e no celular, e tem efeitos sonoros.
- **`forca_gui.py`**: versão desktop em Python, feita com tkinter.

Os dois jogos usam a base de palavras [`Base_Palavras.csv`](Base_Palavras.csv), que tem 5 temas: frutas, plantas, animais, aves e lugar.

## Como jogar

| Versão | Como abrir |
|---|---|
| Web | Abra `forca.html` em qualquer navegador moderno |
| Python | `python forca_gui.py` (precisa de `pandas` e `tkinter`) |

> **Linux + Anaconda:** o `tk` do canal `defaults` não suaviza as fontes. Use o Python do sistema (`/usr/bin/python3 forca_gui.py`) ou instale o `tk` do conda-forge.

## Regras

- Você tem **6 chances**.
- O **tema** aparece no 1º erro. A **dica** aparece quando sobra 1 chance, ou antes disso se você pagar 1 chance por ela.
- A **dificuldade** define o tamanho da dica:

  | Nível | Dica | Pontos |
  |---|---|---|
  | Fácil | 15 palavras | 10 + 5 por chance restante |
  | Médio | 10 palavras | 20 + 5 por chance restante |
  | Difícil | 5 palavras | 30 + 5 por chance restante |

- Uma letra sem acento revela as variações dela: **A** revela Á/Ã/Â e **C** revela Ç.
- O placar mostra pontos, vitórias, derrotas e a sequência de vitórias.

Atalhos: **Enter** inicia ou reinicia a partida e **Esc** volta ao menu. Também dá para jogar só com o teclado da tela, pelo mouse ou toque.

## Base de palavras

`Base_Palavras.csv` tem as colunas `Tema, Palavra, Dificuldade, Dica`. A coluna `Dificuldade` guarda o número de palavras da dica (5, 10 ou 15). Ao carregar, os jogos:

- juntam as palavras repetidas por tema + palavra, mantendo uma dica por nível;
- descartam palavras iguais ao nome do tema.

O `forca.html` traz uma cópia da base dentro do arquivo. Depois de editar o CSV, gere o HTML outra vez para atualizar essa cópia.

## Origem

Este projeto partiu do `dsa_projeto1_game_v3.py`, um jogo da forca em modo texto do curso da Data Science Academy, mantido aqui como referência.
