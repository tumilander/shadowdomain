import argparse
from urllib.parse import quote
from urllib.request import urlopen
import sqlite3
from cryptography.fernet import Fernet, InvalidToken

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

def load_from_database():
    try:
        # conecta ao banco de dados SQLite || com tratamento de erro
        connection = sqlite3.connect('api_tokens.db')
        cursor = connection.cursor()

        # recupera a chave e token criptografados da tabela
        cursor.execute('SELECT encrypted_key, encrypted_token FROM tokens ORDER BY id DESC LIMIT 1')
        result = cursor.fetchone()
    except Exception as erro:
        print(RED + f"Erro ao se conectar ao banco de dados: {erro}" + RESET)
    finally:
        connection.close()

    return result

def decrypt_token(encrypted_key, encrypted_token):
    try:
        # Cria um objeto Fernet com a chave original
        cipher_suite = Fernet(encrypted_key)

        # Descriptografar o token
        decrypted_token = cipher_suite.decrypt(encrypted_token).decode()

        return decrypted_token
    except InvalidToken as e:
        print(RED + f"Erro ao descriptografar o token: {e}" + RESET)
        return None

def send_to_telegram(api_token, chat_id, subdomain_data):
    # divide a mensagem em partes menores (por exemplo, de dois em dois)
    message_parts = [subdomain_data[i:i+2] for i in range(0, len(subdomain_data), 2)]

    for part in message_parts:
        message = '\n'.join(part)
        url = f'https://api.telegram.org/bot{api_token}/sendMessage?chat_id={chat_id}&text={quote(message)}'

        try:
            response = urlopen(url)
            print(GREEN + "\nResultado enviado com sucesso para o Telegram." + RESET)
        except Exception as e:
            print(RED + f"\nErro ao enviar resultado para o Telegram: {e}" + RESET)

if __name__ == "__main__":
    # carrega a chave e token criptografados da base de dados
    encrypted_key, encrypted_token = load_from_database()

    if encrypted_key and encrypted_token:
        # Descriptografar o token
        api_token = decrypt_token(encrypted_key, encrypted_token)

        if api_token:
            TELEGRAM_CHAT_ID = 'SEU_CHAT_OU_GRUPO_ID'

            parser = argparse.ArgumentParser(description="Envia resultados para o Telegram")
            parser.add_argument("-d", "--domain", required=True, help="Domínio alvo")
            parser.add_argument("-send", action="store_true", help="Enviar resultados automaticamente")
            parser.add_argument("subdomain_data", nargs="*", help="Dados do subdomínio (subdomain host ip status_code)")
            args = parser.parse_args()

            domain = args.domain
            subdomain_data = args.subdomain_data

            if args.send:
                send_to_telegram(api_token, TELEGRAM_CHAT_ID, subdomain_data)
    else:
        print(RED + "Chave ou token não encontrados na base de dados." + RESET)