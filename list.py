import requests  
import json  
import time  
import threading  
import itertools  
from datetime import datetime  
from zoneinfo import ZoneInfo  
from urllib.parse import urlparse, parse_qs  
from colorama import Fore, init  

# Inițializează Colorama pentru a funcționa pe diferite platforme  
init(autoreset=True)  

# Variabile globale  
done = threading.Event()  
timezone = ZoneInfo("Europe/Bucharest")  
default_expiration_date = "Data nu este disponibilă"  

# Funcții utilizate în procesare  
def load_cache():  
    """Încărcați datele din cache dintr-un fișier."""  
    try:  
        with open("cache.json", "r") as cache_file:  
            return json.load(cache_file)  
    except FileNotFoundError:  
        return {}  

def save_cache(cache):  
    """Salvați datele în cache într-un fișier."""  
    with open("cache.json", "w") as cache_file:  
        json.dump(cache, cache_file)  

def verificar_status_m3u(link_m3u):  
    """Verifică starea unui link M3U și returnează informațiile relevante."""  
    cache = load_cache()  

    # Verificăm dacă URL-ul există deja în cache  
    if link_m3u in cache:  
        return cache[link_m3u]['status'], cache[link_m3u]['usuario'], cache[link_m3u]['senha'], cache[link_m3u].get('exp_date', default_expiration_date)  

    try:  
        parsed_url = urlparse(link_m3u)  
        query_params = parse_qs(parsed_url.query)  
        usuario, senha = query_params.get('username', [None])[0], query_params.get('password', [None])[0]  
        if not usuario or not senha:  
            return "Invalid URL: Missing username or password", None, None, None  

        link = f"{parsed_url.scheme}://{parsed_url.netloc}/player_api.php?username={usuario}&password={senha}&type=m3u"  
        response = requests.get(link, headers={"User-Agent": "Mozilla/5.0"}, timeout=5, verify=False)  

        # Verifică dacă răspunsul este valid  
        if response.status_code != 200:  
            return f"Error: Server returned status code {response.status_code}", None, None, "Indisponibil"  

        try:  
            data = response.json()  
        except json.JSONDecodeError:  
            return "Error: Invalid JSON response", None, None, "Indisponibil"  
        
        # Asigură-te că 'status' și 'exp_date' sunt în răspuns  
        if 'status' not in data or 'exp_date' not in data:  
            return "Error: Response does not contain expected fields", None, None, "Indisponibil"  
        
        status_text = "activ" if data['status'].lower() == 'active' else "inactiv"  
        exp_date = time.strftime('%d.%m.%Y', time.localtime(int(data['exp_date']))) if 'exp_date' in data else default_expiration_date  

        # Salvează doar dacă statusul este „activ”  
        if status_text == "activ":  
            cache[link_m3u] = {'status': status_text, 'usuario': usuario, 'senha': senha, 'exp_date': exp_date}  
            save_cache(cache)  

        return status_text, usuario, senha, exp_date  
    except requests.RequestException as e:  
        return f"Error: {str(e)}", None, None, "Indisponibil"  

def calcular_dias_ate_data_futura(exp_date):  
    """Calculează numărul de zile până la data de expirare."""  
    if exp_date == default_expiration_date:  
        return "N/A"  
    
    try:  
        exp_date_dt = datetime.strptime(exp_date, '%d.%m.%Y')  
        days_remaining = (exp_date_dt - datetime.now(timezone)).days  
        return days_remaining  
    except ValueError:  
        return "Invalid date"  

def processar_arquivo_entradas(arquivo_entradas, arquivo_saidas):  
    """Procesează fișierul de intrare și scrie rezultatele în fișierul de ieșire."""  
    try:  
        with open(arquivo_entradas, 'r', encoding='utf-8', errors='replace') as f:  
            links = f.readlines()  

        with open(arquivo_saidas, 'w', encoding='utf-8') as f:  
            ora_curenta = datetime.now(timezone).strftime('%H:%M:%S, %d.%m.%Y')  
            fusul_orar = timezone.zone  
            tara = "România"  
            f.write(f"Procesare realizată la: {ora_curenta} ({fusul_orar}, {tara})\n\n")  

            for link in links:  
                link = link.strip()  
                if link:  
                    status, usuario, senha, exp_date = verificar_status_m3u(link)  
                    dias_faltando = calcular_dias_ate_data_futura(exp_date)  
                    result = (  
                        f"Link: {link}\n"  
                        f"User: {usuario}\n"  
                        f"Pass: {senha}\n"  
                        f"Status: {status}\n"  
                        f"Expire Date: {exp_date} (Zile rămase: {dias_faltando})\n\n"  
                    )  
                    f.write(result)  
                    print(Fore.GREEN + result if status == "activ" else Fore.RED + f"Link: {link} - Status: {status}")  
    except FileNotFoundError:  
        print(Fore.RED + f"Eroare: Fișierul {arquivo_entradas} nu a fost găsit.")  
    except Exception as e:  
        print(Fore.RED + f"A apărut o eroare: {str(e)}")  

def animar_progresso():  
    """Afișează o animație de progres în consolă."""  
    for simbol in itertools.cycle(['|', '/', '-', '\\']):  
        if done.is_set():  
            break  
        print(Fore.YELLOW + f'\rProcesare... {simbol}', end='', flush=True)  
        time.sleep(0.1)  

def imprimir_banner():  
    """Afișează banner-ul de început."""  
    print(Fore.BLUE + "=" * 50)  
    print(Fore.GREEN + " Script de Verificare M3U - V1.0")  
    print(Fore.BLUE + "=" * 50)  

if __name__ == "__main__":  
    arquivo_entradas = "/storage/emulated/0/qpython/net.txt"  
    arquivo_saidas = "/storage/emulated/0/qpython/results.txt"  

    imprimir_banner()  
    t = threading.Thread(target=animar_progresso)  
    t.start()  

    processar_arquivo_entradas(arquivo_entradas, arquivo_saidas)  

    done.set()  
    t.join()  
    print(Fore.CYAN + "\nProcesare completă!")
