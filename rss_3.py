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

        # 1. Recupero link AgID e lo elimino subito
        agid_link = ""
        for a in text_area.find_all('a'):
            href = a.get('href', '')
            if "cert-agid.gov.it" in href:
                agid_link = href
                a.decompose() 

        # 2. Conversione selettiva tag (MOLTO più rigorosa)
        for tag_name in ["b", "i", "code"]:
            for tag in text_area.find_all(tag_name):
                content = tag.get_text()
                # Se contiene hashtag, solo spazi, o è vuoto: DECOMPOSTO (sparisce il tag, resta il testo)
                if "#" in content or not content.strip():
                    tag.replace_with(content) 
                else:
                    prefix = "**" if tag_name == "b" else "*" if tag_name == "i" else "`"
                    # Applichiamo la formattazione solo se non è un'emoji isolata (almeno un carattere alfanumerico)
                    if re.search(r'[a-zA-Z0-9]', content):
                        tag.replace_with(f"{prefix}{content}{prefix}")
                    else:
                        tag.replace_with(content)

        # 3. Trasformiamo i <br> in \n
        for br in text_area.find_all("br"):
            br.replace_with("\n")

        # 4. Estrazione testo grezzo
        testo_raw = text_area.get_text().strip()

        # 5. Pulizia link residui ed emoji 🔗
        testo_raw = testo_raw.replace("🔗", "")
        testo_raw = re.sub(r'https?://cert-agid\.gov\.it/\S*', '', testo_raw).strip()

        # 6. LOGICA TITOLO (PULIZIA TOTALE)
        parti = testo_raw.split('\n\n', 1)
        if len(parti) > 1:
            # Puliamo la prima riga da OGNI asterisco esistente per evitare i "6 asterischi"
            titolo_pulito = parti[0].replace('*', '').strip()
            # Se dopo la pulizia il titolo è vuoto, non mettiamo nulla
            testo_finale = f"**{titolo_pulito}**\n\n{parti[1].strip()}" if titolo_pulito else parti[1].strip()
        else:
            titolo_pulito = testo_raw.replace('*', '').strip()
            testo_finale = f"**{titolo_pulito}**"

        # 7. PULIZIA FINALE: Rimuove eventuali asterischi rimasti vuoti (es. ** ** o ****)
        testo_finale = re.sub(r'\*+\s*\*+', '', testo_finale)
        testo_finale = re.sub(r'\*{4,}', '', testo_finale) # Rimuove catene di 4+ asterischi

        # 8. ID per cronologia
        post_link_tag = last_msg.find('a', class_='tgme_widget_message_date')
        post_id = post_link_tag['href'] if post_link_tag else testo_finale[:50]
        
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
        invio = data['testo']
        if data['agid_url']:
            invio += f"\n\n🔗 [Leggi su AgID]({data['agid_url']})"

        requests.post(WEBHOOK_URL, json={"content": invio[:2000]})
        with open(HISTORY_FILE, "a") as f: f.write(data['id'] + "\n")
        print("Inviato: Finalmente senza glitch!")

if __name__ == "__main__":
    main()
