import argparse
import socket
import requests
import threading
import signal
from concurrent.futures import ThreadPoolExecutor

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

exit_flag = threading.Event()  # Evento para indicar a saída

def on_ctrl_c(signum, frame):
    print("\nSaindo...")
    exit_flag.set()  # Define o evento para indicar a saída
    raise KeyboardInterrupt  # Levanta uma exceção para interromper a execução

def check_subdomain(subdomain, domain, verbose, selected_status_code):
    try:
        full_domain = f"{subdomain}.{domain}"
        if full_domain.endswith('.localhost'):
            return None
        ip = socket.gethostbyname(full_domain)
        if ip.startswith('127.') or ip == '0.0.0.0':
            return None
        try:
            host = socket.gethostbyaddr(ip)[0]
        except socket.herror:
            host = None
        status_code = get_status_code(f"http://{full_domain}")
        result = (full_domain, host, ip, status_code)
        if verbose and (selected_status_code is None or status_code == selected_status_code):
            print_result(result)
        if selected_status_code is None or status_code == selected_status_code:
            return result
        return None
    except socket.gaierror:
        return None

def get_status_code(url):
    try:
        response = requests.get(url, timeout=5)
        return response.status_code
    except requests.RequestException:
        return None

def print_result(result):
    subdomain, host, ip, status_code = result
    if host:
        print(GREEN + f"Host: {host}" + RESET + BLUE + f" | Subdomínio: {subdomain} " + RESET + YELLOW + f" | IP: {ip} " + RESET + BOLD + f" | Status Code: {status_code}" + RESET)
    else:
        print(BLUE + f"Subdomínio: {subdomain}" + RESET + YELLOW + f" | IP: {ip} " + RESET + BOLD + f"| Status Code: {status_code}" + RESET)

def search_subdomains(domain, wordlist_path, num_threads, verbose, selected_status_code):
    subdomains = []
    try:
        with open(wordlist_path, 'r') as f:
            wordlist = f.read().splitlines()

        executor = ThreadPoolExecutor(max_workers=num_threads)

        results = []
        for subdomain in wordlist:
            if exit_flag.is_set():
                break
            future = executor.submit(check_subdomain, subdomain, domain, verbose, selected_status_code)
            results.append((subdomain, future))

        for subdomain, future in results:
            if exit_flag.is_set():
                break
            result = future.result()
            if result is not None:
                _, _, _, status_code = result
                if selected_status_code is None or status_code == selected_status_code:
                    subdomains.append(result)

        executor.shutdown(wait=True)

    except FileNotFoundError:
        print("Erro: Arquivo da wordlist não encontrado.")
        return None
    except socket.gaierror:
        print("Erro: Domínio não encontrado.")
        return None

    return subdomains

def save_to_file(subdomains, output_file):
    try:
        with open(output_file, 'w') as f:
            for subdomain, host, ip, status_code in subdomains:
                if host:
                    f.write(f"Host: {host} | Subdomínio: {subdomain} | IP: {ip} | Status Code: {status_code}\n")
                else:
                    f.write(f"Subdomínio: {subdomain} | IP: {ip} | Status Code: {status_code}\n")
        print(f"Dados salvos em {output_file}")
    except IOError:
        print("Erro: Não foi possível salvar o arquivo.")
        return None

def print_banner():

    print(RED + """
     _____ _               _              ______                      _       
    /  ___| |             | |             |  _  \                    (_)      
    \ `--.| |__   __ _  __| | _____      _| | | |___  _ __ ___   __ _ _ _ __  
     `--. \ '_ \ / _` |/ _` |/ _ \ \ /\ / / | | / _ \| '_ ` _ \ / _` | | '_ \ 
    /\__/ / | | | (_| | (_| | (_) \ V  V /| |/ / (_) | | | | | | (_| | | | | |
    \____/|_| |_|\__,_|\__,_|\___/ \_/\_/ |___/ \___/|_| |_| |_|\__,_|_|_| |_|
        by Anderson Ribeiro                                           V.1.0            
       """ + RESET)                                                                       

if __name__ == "__main__":
    print_banner()

    # Parse dos argumentos de linha de comando
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description="Busca de Subdomínios")
    parser.add_argument("-d", "--domain", required=True, help="Domínio alvo")
    parser.add_argument("-w", "--wordlist", required=True, help="Caminho para o arquivo de wordlist")
    parser.add_argument("-o", "--output", help="Caminho para o arquivo de saída")
    parser.add_argument("-t", "--threads", type=int, choices=range(1, 11), default=1, help="Número de threads (1-10)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Ativa o modo verboso")
    parser.add_argument("-s", "--status-code", type=int, help="Filtra subdomínios com o status code especificado")
    parser.add_argument("-send", action="store_true", help="Enviar resultados automaticamente após a busca")
    args = parser.parse_args()

    domain = args.domain
    wordlist_path = args.wordlist
    output_file = args.output
    num_threads = args.threads
    verbose = args.verbose
    selected_status_code = args.status_code

    # Configura o manipulador de sinal para Ctrl + C
    signal.signal(signal.SIGINT, on_ctrl_c)

    subdomains = search_subdomains(domain, wordlist_path, num_threads, verbose, selected_status_code)

    if subdomains:
        for subdomain, host, ip, status_code in subdomains:
            pass  

        if output_file:
            save_to_file(subdomains, output_file)

        if args.send:
            # Se o argumento -send for fornecido, execute o segundo script automaticamente
            import subprocess
            subprocess.run(["python3", "telegram.py", "-d", domain, "-send"] + [f"{host} {subdomain}  {ip} {status_code}" for subdomain, host, ip, status_code in subdomains])

    else:
        print(f"\nNenhum subdomínio ativo encontrado com Status Code {selected_status_code}.")

    print("\nOperação concluída.")