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
        response = requests.get(link, headers=headers, timeout=5, verify=False)  

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
