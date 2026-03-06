import requests
from bs4 import BeautifulSoup
import os

# Configurazione recuperata dai Secret di GitHub
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
CHANNEL_URL = "https://t.me/s/certagid"
HISTORY_FILE = "history_3.txt"

def get_latest_post():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(CHANNEL_URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Trova i messaggi
        messages = soup.find_all('div', class_='tgme_widget_message_wrap')
        if not messages:
            return None

        # Prendiamo l'ultimo messaggio (il più recente)
        last_msg = messages[-1]
        text_area = last_msg.find('div', class_='tgme_widget_message_text')
        
        if not text_area:
            return None

        # --- ESTRAZIONE TITOLO (Primo grassetto) ---
        bold_tag = text_area.find('b')
        if bold_tag:
            titolo = bold_tag.get_text().strip()
            # Lo rimuoviamo dal corpo per non ripeterlo
            bold_tag.decompose()
        else:
            titolo = "NUOVO AGGIORNAMENTO"

        # --- CONVERSIONE HTML -> MARKDOWN ---
        # Convertiamo i tag rimanenti in simboli Discord
        for b in text_area.find_all('b'):
            b.replace_with(f"**{b.get_text()}**")
        for i in text_area.find_all('i'):
            i.replace_with(f"*{i.get_text()}*")
        for code in text_area.find_all('code'):
            code.replace_with(f"`{code.get_text()}`")

        # Recuperiamo il corpo del testo pulito
        corpo_testo = text_area.get_text(separator="\n").strip()

        # Link del post Telegram
        post_link_tag = last_msg.find('a', class_='tgme_widget_message_date')
        post_link = post_link_tag['href'] if post_link_tag else ""

        # Estrazione link esterni (es. link al sito del CERT)
        ext_links = []
        for a in text_area.find_all('a'):
            href = a.get('href', '')
            if href and "t.me" not in href:
                ext_links.append(href)
        
        return {
            "titolo": titolo.upper(),
            "corpo": corpo_testo,
            "link": post_link,
            "external_links": list(set(ext_links))
        }
    except Exception as e:
        print(f"Errore durante lo scraping: {e}")
        return None

def main():
    if not WEBHOOK_URL:
        print("ERRORE: Variabile DISCORD_WEBHOOK non impostata!")
        return

    # 1. Leggi cronologia
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            history = f.read().splitlines()

    # 2. Ottieni dati
    data = get_latest_post()
    
    if data and data['link'] not in history:
        # 3. Costruisci il messaggio
        header = f"🛡️ **{data['titolo']}**\n\n"
        footer = f"\n\n🔗 [Post Originale]({data['link']})"
        
        links_section = ""
        if data['external_links']:
            links_section = "\n\n**Approfondimenti:**\n" + "\n".join(data['external_links'])

        # Calcola spazio rimanente per il corpo (limite Discord 2000 car totali)
        max_body_len = 1900 - len(header) - len(footer) - len(links_section)
        corpo = data['corpo']
        if len(corpo) > max_body_len:
            corpo = corpo[:max_body_len] + "..."

        full_message = f"{header}{corpo}{links_section}{footer}"

        # 4. Invia a Discord
        resp = requests.post(WEBHOOK_URL, json={"content": full_message})
        
        if resp.status_code in [200, 204]:
            print(f"Inviato: {data['titolo']}")
            # Salva in cronologia
            with open(HISTORY_FILE, "a") as f:
                f.write(data['link'] + "\n")
        else:
            print(f"Errore Discord: {resp.status_code}")
    else:
        print("Nessuna nuova notizia o post già inviato.")

if __name__ == "__main__":
    main()
