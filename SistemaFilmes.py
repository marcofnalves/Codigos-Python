import pandas as pd
import os

# ===========================
# ESTRUTURAS DE DADOS
# ===========================

filmes_df = {}
coleccoes = {}
favoritos = {}
historico = []

# ===========================
# AUXILIARES
# ===========================

def limpar():
    os.system('cls' if os.name == 'nt' else 'clear')

def cores(texto, tipo):
    if tipo == "warning":
        print(f"\033[33m{texto}\033[0m")
    elif tipo == "error":
        print(f"\033[31m{texto}\033[0m")
    else:
        print(texto)

def mostrar_detalhes(filme):
    print(f"""
ID:            {filme['tconst']}
Título:        {filme['primaryTitle']}
Ano:           {int(filme['startYear']) if pd.notna(filme['startYear']) else 'N/A'}
Duração:       {int(filme['runtimeMinutes']) if pd.notna(filme['runtimeMinutes']) else 'N/A'} minutos
Tipo:          {filme['titleType']}
Géneros:       {', '.join(filme['genres']) if filme['genres'] else 'N/A'}
""")

# ===========================
# CARREGAMENTO DE DADOS
# ===========================

def carregar_filmes(caminho, max_linhas=200000):
    try:
        df = pd.read_csv(caminho, sep='\t', nrows=max_linhas, dtype=str)
        df = df[df['titleType'].notna() & df['primaryTitle'].notna()]
        df['startYear'] = pd.to_numeric(df['startYear'], errors='coerce')
        df['runtimeMinutes'] = pd.to_numeric(df['runtimeMinutes'], errors='coerce')
        df['genres'] = df['genres'].fillna('').apply(
            lambda g: g.split(',') if g != '\\N' and g.strip() != '' else []
        )
        amostra_df = df.sample(n=500, random_state=42).reset_index(drop=True)
        print(f"Carregados {len(amostra_df)} filmes (amostra de 500 a partir de {len(df)}).")
        return amostra_df
    except FileNotFoundError:
        cores(f"Ficheiro '{caminho}' não encontrado.", "error")
        return pd.DataFrame()

# ===========================
# FUNCIONALIDADES
# ===========================

def listar_generos_disponiveis():
    global filmes_df
    todos_generos = set()
    for generos in filmes_df['genres']:
        todos_generos.update(generos)
    todos_generos = sorted(g for g in todos_generos if g)
    print("\nGéneros disponíveis:")
    for genero in todos_generos:
        print(f" - {genero}")

def criar_colecao_por_genero(coleccoes, genero):
    global filmes_df
    genero_input = genero.strip().lower()
    
    tipo_input = input("Qual o tipo (movie, tvEpisode, short, tvMovie)? ").strip().lower()
    tipos_validos = {"movie", "tvepisode", "short", "tvmovie"}

    if tipo_input not in tipos_validos:
        print("Tipo inválido. Opções válidas: movie, tvEpisode, short, tvMovie.")
        return

    chave = (genero_input, tipo_input)

    coleccoes[chave] = filmes_df[
        (filmes_df['titleType'].str.lower() == tipo_input) &
        (filmes_df['genres'].apply(lambda gs: any(g.strip().lower() == genero_input for g in gs)))
    ].copy()

    quantidade = len(coleccoes[chave])
    print(f"\nColecção '{genero}' ({tipo_input}) criada com {quantidade} filme(s).")

    if quantidade == 0:
        print("(Nenhum filme corresponde ao género e tipo escolhidos na amostra.)")
        return

    for _, filme in coleccoes[chave].iterrows():
        mostrar_detalhes(filme)

def adicionar_favorito(id_filme):
    global favoritos
    global filmes_df
    filme = filmes_df[filmes_df['tconst'] == id_filme]
    if filme.empty:
        cores("Filme não encontrado.", "error")
        return
    tipo = filme.iloc[0]['titleType'] # serve para aceder à primeira linha de um DataFrame

    if tipo not in favoritos or favoritos[tipo].empty:
        favoritos[tipo] = pd.DataFrame(columns=filmes_df.columns).astype(filmes_df.dtypes.to_dict())

    if id_filme in favoritos[tipo]['tconst'].values:
        cores("Já está nos favoritos.", "warning")
    else:
        favoritos[tipo] = pd.concat([favoritos[tipo], filme])
        print(f"\nAdicionado aos favoritos:")
        mostrar_detalhes(filme.iloc[0])

def listar_favoritos():
    global favoritos
    if not favoritos:
        print("\nNenhum favorito.")
        return
    for tipo, df in favoritos.items():
        print(f"\n{tipo.upper()} ({len(df)} filmes):")
        for _, filme in df.iterrows():
            print("\n---")
            mostrar_detalhes(filme)

def adicionar_ao_historico(filme_row):
    global historico
    historico.insert(0, filme_row)
    if len(historico) > 1000:
        historico.pop()

def listar_historico():
    global historico
    print("\n\033[33mHistórico:\033[0m")
    print("\033[33m=\033[0m"*50)
    print("\n\033[33mFilmes Assistidos\033[0m")
    print("\033[33m=\033[0m"*50)
    if not historico:
        print(" (Histórico vazio.)")
        return
    for i, filme in enumerate(historico[:10]):
        print(f"\n#{i+1}")
        mostrar_detalhes(filme)

def pesquisa_por_titulo(termo):
    global filmes_df
    return filmes_df[filmes_df['primaryTitle'].str.lower().str.contains(termo.lower(), na=False)]

def pesquisa_por_genero(nome_genero):
    global filmes_df
    print(f"Pesquisando filmes do género: '{nome_genero}'")
    resultados = []
    for _, filme in filmes_df.iterrows():
        if nome_genero in filme['genres']:
            resultados.append(filme)
    print(f"Encontrados {len(resultados)} filmes")
    return resultados

def pesquisaFilmes(result):
    for data in result:
        print(f"\033[33mID:\033[0m {data['tconst']} | \033[33mTítulo:\033[0m {data['primaryTitle']}")

def remover_favorito(id_filme):
    global historico
    filme_removido = None
    tipo_removido = None
    for tipo, df in favoritos.items():
        if id_filme in df['tconst'].values:
            filme_removido = df[df['tconst'] == id_filme].iloc[0]
            favoritos[tipo] = df[df['tconst'] != id_filme]
            tipo_removido = tipo
            break
    if filme_removido is not None:
        print(f"\nFilme removido dos favoritos ({tipo_removido}):")
        mostrar_detalhes(filme_removido)
        adicionar_ao_historico(filme_removido)
        cores("O filme foi adicionado ao histórico como assistido.", "warning")
    else:
        cores("Filme não encontrado nos favoritos.", 'error')

def limpar_historico():
    global historico
    historico.clear()
    cores("\nHistórico limpo com sucesso!", "warning")

# ===========================
# MENU
# ===========================

def mostrar_menu():
    print("""
=== GESTÃO DE FILMES ===
1. Criar colecção por género
2. Pesquisar por Genero
3. Adicionar aos favoritos
4. Ver favoritos
5. Assistir filme dos favoritos
6. Ver histórico
7. Pesquisar por Titulo  
8. Assistir filme de colecção
9. Limpar Histórico

0. Sair
""")

# ===========================
# MAIN
# ===========================

def main():
    limpar()
    global filmes_df
    global coleccoes
    global favoritos
    global historico

    caminho = 'title.basics.tsv'
    filmes_df = carregar_filmes(caminho)
    if filmes_df.empty:
        return

    while True:
        mostrar_menu()
        op = input("Opção: ").strip()

        if op == '1':
            listar_generos_disponiveis()
            genero = input("Género: ").strip()
            criar_colecao_por_genero(coleccoes, genero)

        elif op == '2':
            genero = input("Género a pesquisar: ").strip()
            resultados = pesquisa_por_genero(genero)    
            pesquisaFilmes(resultados)

        elif op == '3':
            genero = input("Género para adicionar ao favoritos: ").strip()
            resultados = pesquisa_por_genero(genero)
            pesquisaFilmes(resultados)
            id_filme = input("ID do filme: ").strip()
            adicionar_favorito(id_filme)

        elif op == '4':
            listar_favoritos()

        elif op == '5':
            listar_favoritos()
            if favoritos:
                id_filme = input("ID do filme a remover: ").strip()
                remover_favorito(id_filme)

        elif op == '6':
            listar_historico()

        elif op == '7':
            termo = input("Título: ").strip()
            resultados = pesquisa_por_titulo(termo)
            if resultados.empty:
                cores("Nenhum resultado encontrado.", "error")
            else:
                for _, filme in resultados.head(10).iterrows():
                    mostrar_detalhes(filme)

        elif op == '8':
            genero = input("Género da colecção: ").strip()
            tipo = input("Tipo da colecção (movie, tvEpisode, short, tvMovie): ").strip().lower()
            resultados = pesquisa_por_genero(genero)
            pesquisaFilmes(resultados)
            chave = (genero.lower(), tipo)
            if chave in coleccoes:
                coleccao = coleccoes[chave]
                id_filme = input("ID do filme a assistir: ").strip()
                match = coleccao[coleccao['tconst'] == id_filme]
                if not match.empty:
                    coleccoes[chave] = coleccao[coleccao['tconst'] != id_filme]
                    adicionar_ao_historico(match.iloc[0])
                    cores(f"Removido e adicionado ao histórico:", "warning")
                    mostrar_detalhes(match.iloc[0])
                else:
                    cores("Filme não encontrado na colecção.", "error")
            else:
                cores("Colecção inexistente.", "error")

        elif op == '9':
            confirmacao = input("Tem certeza que deseja limpar o histórico? (s/n): ").strip().lower()
            if confirmacao == 's':
                limpar_historico()
            else:
                cores("Operação cancelada.", "warning")

        elif op == '0':
            print("Até breve!")
            break
        else:
            cores("Opção inválida.", "error")

if __name__ == '__main__':
    main()
