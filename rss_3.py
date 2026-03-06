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

        # 1. Recupero il link AgID se presente (cercandolo tra i tag <a>)
        agid_link = ""
        for a in text_area.find_all('a'):
            href = a.get('href', '')
            if "cert-agid.gov.it" in href:
                agid_link = href
                break

        # 2. ESTRAZIONE TESTO (Il Segreto è qui: niente separator)
        # Togliendo separator="\n", BeautifulSoup non forza l'a capo dopo le emoji.
        #strip=True pulisce solo l'inizio e la fine del messaggio totale.
        messaggio_puro = text_area.get_text().strip()

        # 3. ID per la cronologia (basato sul link del post)
        post_link_tag = last_msg.find('a', class_='tgme_widget_message_date')
        post_id = post_link_tag['href'] if post_link_tag else messaggio_puro[:50]
        
        return {
            "testo": messaggio_puro,
            "id": post_id,
            "agid_url": agid_link
        }
    except Exception as e:
        print(f"Errore: {e}")
        return None

def main():
    if not WEBHOOK_URL:
        print("Manca il Webhook!")
        return
    
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f: 
            history = f.read().splitlines()

    data = get_latest_post()
    
    if data and data['id'] not in history:
        # Costruzione messaggio: Testo + Link AgID (se esiste)
        invio = data['testo']
        if data['agid_url']:
            invio += f"\n\n🔗 [Leggi su AgID]({data['agid_url']})"

        # Invio a Discord
        requests.post(WEBHOOK_URL, json={"content": invio[:2000]})
        
        # Salvataggio in cronologia
        with open(HISTORY_FILE, "a") as f: 
            f.write(data['id'] + "\n")
        print("Messaggio inviato correttamente!")
    else:
        print("Nessuna novità da pubblicare.")

if __name__ == "__main__":
    main()
