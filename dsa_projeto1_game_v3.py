# Projeto 1 - Desenvolvimento de Game em Linguagem Python - Versão 2

# Import
import random
import pandas as pd
import random
from os import system, name

#Carrega Base de Palavras gerada pelo GPT-4o e processa dados
df_palavras=pd.read_csv('Base_Palavras.csv')
df_palavras.drop_duplicates(['Dica'],inplace=True)
dificuldade={5:'Dificil',10:'Medio',15:'Facil'}
df_palavras['Dificuldade']=df_palavras['Dificuldade'].map(dificuldade)



# Função para limar a tela a cada execução
def limpa_tela():
 
    # Windows
    if name == 'nt':
        _ = system('cls')
 
    # Mac ou Linux
    else:
        _ = system('clear')

# Função que desenha a forca na tela
def display_hangman(chances):

    # Lista de estágios da forca
    stages = [  # estágio 6 (final)
                """
                   --------
                   |      |
                   |      O
                   |     \\|/
                   |      |
                   |     / \\
                   -
                """,
                # estágio 5
                """
                   --------
                   |      |
                   |      O
                   |     \\|/
                   |      |
                   |     / 
                   -
                """,
                # estágio 4
                """
                   --------
                   |      |
                   |      O
                   |     \\|/
                   |      |
                   |      
                   -
                """,
                # estágio 3
                """
                   --------
                   |      |
                   |      O
                   |     \\|
                   |      |
                   |     
                   -
                """,
                # estágio 2
                """
                   --------
                   |      |
                   |      O
                   |      |
                   |      |
                   |     
                   -
                """,
                # estágio 1
                """
                   --------
                   |      |
                   |      O
                   |    
                   |      
                   |     
                   -
                """,
                # estágio 0
                """
                   --------
                   |      |
                   |      
                   |    
                   |      
                   |     
                   -
                """
    ]
    return stages[chances]

# Função do jogo
def game(dificuldade="Facil"):

    def nova_partida():
        repetir=str(input("Quer jogar novamente(s/n): "))
        if repetir=='s':
            dificuldade=str(input("Digite o grau de dificuldade (Facil/Medio/Dificil): "))
            game(dificuldade)
        else:
            pass
    
    
    limpa_tela()
    print("\nBem vindo ao jogo da forca!")
    print("Adivinhe a palavra abaixo:\n")
    
     
    # Escolhe randomicamente uma palavra, busca o tema e as dicas
    sorteio=random.choice(range(len(df_palavras)))
    palavra=df_palavras.Palavra[sorteio]
    tema=df_palavras.Tema[sorteio]
    
    #Busca uma dica do grau de dificuldade escolhido, se existir 
    try:
        dica=df_palavras.Dica[(df_palavras['Palavra']==palavra) & (df_palavras["Dificuldade"]==dificuldade)].item()
    except:
        game()
    

    # Lista  de letras  da palavra
    lista_letras_palavras = [letra for letra in palavra.lower()]
    
     # List comprehension
    tabuleiro = ['_' for letra in palavra]
    
    chances=6

   
    # Lista para as letras erradas
    letras_erradas = []
    
    # Lista para as letras digitadas
    letras_tentativas = []
    
    # Loop enquanto número de chances for maior do que zero
    while chances > 0:
        
        limpa_tela()
        print(display_hangman(chances))
        print("Palavra: ",(" ".join(tabuleiro)))
        print("\nChances restantes:", chances)
        print("Letras erradas:", " ".join(letras_erradas))
        print("\n")
        if chances==5:        
                print("Dica: O tema é ",tema)
        elif chances==1:
            print('Dica: ',dica)
       
        
        # Tentativa
        tentativa = input("\nDigite uma letra: ")
        
        # Condicional
        if tentativa in letras_tentativas:
            print("Você já tentou essa letra. Escolha outra!")
            continue
        
        # Lista de tentativas (letras)
        letras_tentativas.append(tentativa)
        
        # Condicional
        if tentativa in lista_letras_palavras:
            
            print("Você acertou a letra!")
            
            # Loop
            for indice in range(len(lista_letras_palavras)):

                # Condicional
                if lista_letras_palavras[indice] == tentativa:
                    tabuleiro[indice] = tentativa.upper()
            
            # Se todos os espaços foram preenchidos, o jogo acabou
            if "_" not in tabuleiro:
                limpa_tela()
                print("Palavra: ",(" ".join(tabuleiro)))
                print("\nVocê venceu! A palavra era: {}".format(palavra))
                nova_partida()
                break
        else:
            print("Ops. Essa letra não está na palavra!")
            # Decremento
            chances -= 1
            letras_erradas.append(tentativa)
            
    
    # Condicional
    if "_" in tabuleiro:
        print("\nVocê perdeu! A palavra era: {}.".format(palavra))
        nova_partida()


# Bloco main
if __name__ == "__main__":
    game()
    print("\nParabéns. Você está aprendendo programação em Python com a DSA. :)\n")

