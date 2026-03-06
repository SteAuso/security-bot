import requests
from bs4 import BeautifulSoup
import os

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

        # 2. LOGICA ANTI-SPAZIO EMOJI + PARAGRAFI
        # Sostituiamo i doppi tag <br> o le chiusure di div con un segnaposto temporaneo
        # per preservare i paragrafi veri prima di estrarre il testo "piatto"
        for br in text_area.find_all("br"):
            br.replace_with("\n")

        # Estraiamo il testo SENZA separatore (così le emoji non vanno a capo)
        testo_pulito = text_area.get_text().strip()

        # 3. ID per la cronologia
        post_link_tag = last_msg.find('a', class_='tgme_widget_message_date')
        post_id = post_link_tag['href'] if post_link_tag else testo_pulito[:50]
        
        return {
            "testo": testo_pulito,
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
        # Costruzione messaggio
        invio = data['testo']
        if data['agid_url']:
            invio += f"\n\n🔗 [Leggi su AgID]({data['agid_url']})"

        # Invio a Discord
        requests.post(WEBHOOK_URL, json={"content": invio[:2000]})
        
        with open(HISTORY_FILE, "a") as f: 
            f.write(data['id'] + "\n")
        print("Inviato con successo!")
    else:
        print("Nessuna novità.")

if __name__ == "__main__":
    main()
