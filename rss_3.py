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

        text_area = messages[-1].find('div', class_='tgme_widget_message_text')
        if not text_area: return None

        # 1. ELIMINA TAG VUOTI (Inclusi quelli con solo spazio)
        for tag in text_area.find_all(['b', 'i', 'span']):
            if not tag.get_text(strip=True):
                tag.decompose()

        # 2. ESTRAZIONE LINK AGID
        agid_url = ""
        for a in text_area.find_all('a'):
            if "cert-agid.gov.it" in a.get('href', ''):
                agid_url = a.get('href')
                a.decompose()

        # 3. CONVERSIONE FORMATTAZIONE (Solo se non contiene hashtag)
        for tag in text_area.find_all(['b', 'i']):
            content = tag.get_text()
            if "#" not in content:
                prefix = "**" if tag.name == 'b' else "*"
                tag.replace_with(f"{prefix}{content}{prefix}")
            else:
                tag.replace_with(content)

        # 4. A CAPO
        for br in text_area.find_all("br"):
            br.replace_with("\n")

        # 5. ESTRAZIONE TESTO E PULIZIA EMOJI/LINK
        testo = text_area.get_text().strip()
        testo = testo.replace("🔗", "")
        testo = re.sub(r'https?://cert-agid\.gov\.it/\S*', '', testo).strip()

        # 6. TITOLO IN GRASSETTO (Solo prima riga)
        parti = testo.split('\n\n', 1)
        if len(parti) > 1:
            titolo = parti[0].replace('**', '').strip()
            testo_finale = f"**{titolo}**\n\n{parti[1].strip()}"
        else:
            testo_finale = f"**{testo.replace('**', '').strip()}**"

        # 7. PULIZIA GLOBALE "FANTASMI" (Rimuove ** ** o ****** ovunque nel testo)
        # Questa regex trova sequenze di asterischi che hanno solo spazi o nulla in mezzo
        testo_finale = re.sub(r'\*+\s*\*+', '', testo_finale)

        post_link = messages[-1].find('a', class_='tgme_widget_message_date')
        post_id = post_link['href'] if post_link else testo_finale[:50]

        return {"testo": testo_finale, "id": post_id, "url": agid_url}
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
        msg = data['testo']
        if data['url']:
            msg += f"\n\n🔗 [Leggi su AgID]({data['url']})"

        requests.post(WEBHOOK_URL, json={"content": msg[:2000]})
        with open(HISTORY_FILE, "a") as f: f.write(data['id'] + "\n")

if __name__ == "__main__":
    main()
