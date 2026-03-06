import requests
from bs4 import BeautifulSoup
import os
import re

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
CHANNEL_URL = "https://t.me/s/certagid"
HISTORY_FILE = "history_3.txt"

def get_latest_post():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        response = requests.get(CHANNEL_URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        messages = soup.find_all('div', class_='tgme_widget_message_wrap')
        if not messages: return None

        last_msg = messages[-1]
        text_area = last_msg.find('div', class_='tgme_widget_message_text')
        if not text_area: return None

        # 1. Recupero link AgID
        agid_link = ""
        for a in text_area.find_all('a'):
            href = a.get('href', '')
            if "cert-agid.gov.it" in href:
                agid_link = href
                break

        # 2. ESTRAZIONE TESTO CON SEPARATORE "CHIRURGICO"
        # Usiamo un carattere speciale come separatore per identificare i tag HTML
        raw_text = text_area.get_text(separator="\n")

        # 3. PULIZIA DEGLI A CAPO DOPPI O INUTILI
        # Sostituisce 3 o più invii con solo 2 (paragrafi puliti)
        clean_text = re.sub(r'\n{3,}', '\n\n', raw_text)
        
        # Rimuove gli spazi vuoti all'inizio e alla fine di ogni riga 
        # e filtra le righe che sono rimaste totalmente vuote per errore
        lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
        
        # Ricostruiamo il messaggio unendo le linee con un singolo a capo
        # Questo "stira" il testo eliminando i buchi dopo le emoji
        final_text = '\n'.join(lines)

        # 4. ID per la cronologia
        post_link_tag = last_msg.find('a', class_='tgme_widget_message_date')
        post_id = post_link_tag['href'] if post_link_tag else final_text[:50]
        
        return {
            "testo": final_text,
            "id": post_id,
            "agid_url": agid_link
        }
    except Exception as e:
        print(f"Errore: {e}")
        return None

def main():
    if not WEBHOOK_URL: return
    
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f: 
            history = f.read().splitlines()

    data = get_latest_post()
    
    if data and data['id'] not in history:
        invio = data['testo']
        if data['agid_url']:
            invio += f"\n\n🔗 [Leggi su AgID]({data['agid_url']})"

        requests.post(WEBHOOK_URL, json={"content": invio[:2000]})
        
        with open(HISTORY_FILE, "a") as f: 
            f.write(data['id'] + "\n")
        print("Inviato con successo!")
    else:
        print("Già presente o nessun post.")

if __name__ == "__main__":
    main()
