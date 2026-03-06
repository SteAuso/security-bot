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

        # 1. Recupero link AgID e lo DECOMPOSTO dall'HTML
        agid_link = ""
        for a in text_area.find_all('a'):
            href = a.get('href', '')
            if "cert-agid.gov.it" in href:
                agid_link = href
                a.decompose() # Rimuove il tag <a> fisicamente

        # 2. Gestione tag <br> per i paragrafi
        for br in text_area.find_all("br"):
            br.replace_with("\n")

        # 3. Estrazione testo pulito (senza link <a>)
        testo_raw = text_area.get_text().strip()

        # 4. RIMOZIONE EMOJI 🔗 E LINK TESTUALI RESIDUI
        # Rimuove l'emoji del link se è rimasta isolata
        testo_raw = testo_raw.replace("🔗", "")
        # Rimuove eventuali URL scritti come testo piano
        testo_raw = re.sub(r'https?://cert-agid\.gov\.it/\S*', '', testo_raw).strip()

        # 5. Logica Grassetto sul primo paragrafo
        parti = testo_raw.split('\n\n', 1)
        if len(parti) > 1:
            # Titolo in grassetto + corpo
            testo_finale = f"**{parti[0].strip()}**\n\n{parti[1].strip()}"
        else:
            # Se non ci sono paragrafi, tutto in grassetto
            testo_finale = f"**{testo_raw}**"

        # 6. ID per cronologia
        post_link_tag = last_msg.find('a', class_='tgme_widget_message_date')
        post_id = post_link_tag['href'] if post_link_tag else testo_raw[:50]
        
        return {
            "testo": testo_finale,
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
        with open(HISTORY_FILE, "r") as f: history = f.read().splitlines()

    data = get_latest_post()
    
    if data and data['id'] not in history:
        # Messaggio finale pulito
        invio = data['testo']
        if data['agid_url']:
            # Aggiungiamo noi il link pulito in fondo
            invio += f"\n\n🔗 [Leggi l'avviso completo sul sito AgID]({data['agid_url']})"

        requests.post(WEBHOOK_URL, json={"content": invio[:2000]})
        
        with open(HISTORY_FILE, "a") as f: f.write(data['id'] + "\n")
        print("Inviato con successo, pulizia emoji completata!")

if __name__ == "__main__":
    main()
