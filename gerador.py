import sqlite3
from cryptography.fernet import Fernet

RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"
UNDERLINE = "\033[4m"
MAGENTA = "\033[095m"
WHITE = "\033[97"

def generate_encrypted_token(api_token):
    # gera uma chave criptografada
    key = Fernet.generate_key()
    cipher_suite = Fernet(key)

    # criptografa o token
    encrypted_token = cipher_suite.encrypt(api_token.encode())

    return key, encrypted_token

def save_to_database(encrypted_key, encrypted_token):
    try:
        # conecta ao banco de dados SQLite || com tratamento de erro
        connection = sqlite3.connect('api_tokens.db')
        cursor = connection.cursor()

        # cria a tabela se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                encrypted_key TEXT,
                encrypted_token TEXT
            )
        ''')

        # insere dados criptografados na tabela
        cursor.execute('INSERT INTO tokens (encrypted_key, encrypted_token) VALUES (?, ?)', (encrypted_key, encrypted_token))

        # Commit e fechar a conexão
        connection.commit()
    except Exception as erro:
        print(RED + f"Erro ao se salvar chaves no banco de dados: {erro}" + RESET)
    finally:
        connection.close()

if __name__ == "__main__":
    # Substitua 'sua_chave_aqui' pela sua API token
    api_token = 'sua_chave_aqui'

    # gera a chave e token criptografados
    key, encrypted_token = generate_encrypted_token(api_token)

    # salva na base de dados
    save_to_database(key, encrypted_token)

    print(GREEN + "Chave criptografada e token criptografado foram salvos na base de dados." + RESET)