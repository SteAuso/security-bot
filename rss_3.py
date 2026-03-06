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

        # 1. RIMOZIONE TAG VUOTI (Inclusi quelli con solo spazi)
        # Questo pulisce i vari <b> </b> o <i>  </i> prima di processarli
        for tag in text_area.find_all(['b', 'i', 'code', 'span']):
            if not tag.get_text(strip=True):
                tag.decompose()

        # 2. Recupero link AgID e rimozione
        agid_link = ""
        for a in text_area.find_all('a'):
            href = a.get('href', '')
            if "cert-agid.gov.it" in href:
                agid_link = href
                a.decompose() 

        # 3. Mantenimento formattazione originale
        # Convertiamo i tag in Markdown SOLO se hanno senso
        for tag_name in ["b", "i", "code"]:
            for tag in text_area.find_all(tag_name):
                content = tag.get_text()
                # Se c'è un hashtag, non mettiamo i ** (come chiesto prima)
                if "#" in content:
                    tag.replace_with(content)
                else:
                    prefix = "**" if tag_name == "b" else "*" if tag_name == "i" else "`"
                    tag.replace_with(f"{prefix}{content}{prefix}")

        # 4. Gestione a capo
        for br in text_area.find_all("br"):
            br.replace_with("\n")

        testo_raw = text_area.get_text().strip()

        # 5. Pulizia link e emoji 🔗
        testo_raw = testo_raw.replace("🔗", "")
        testo_raw = re.sub(r'https?://cert-agid\.gov\.it/\S*', '', testo_raw).strip()

        # 6. Logica Titolo in grassetto (senza rompere il resto)
        parti = testo_raw.split('\n\n', 1)
        if len(parti) > 1:
            # Puliamo solo la prima riga per il titolo
            titolo_pulito = parti[0].replace('**', '').strip()
            testo_finale = f"**{titolo_pulito}**\n\n{parti[1].strip()}"
        else:
            testo_finale = f"**{testo_raw.replace('**', '').strip()}**"

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
        invio = data['testo']
        if data['agid_url']:
            invio += f"\n\n🔗 [Leggi su AgID]({data['agid_url']})"

        requests.post(WEBHOOK_URL, json={"content": invio[:2000]})
        with open(HISTORY_FILE, "a") as f: f.write(data['id'] + "\n")

if __name__ == "__main__":
    main()
