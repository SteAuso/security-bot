import requests
from bs4 import BeautifulSoup
import os
import re

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
CHANNEL_URL = "https://t.me/s/certagid"
HISTORY_FILE = "history_3.txt"

def clean_text_strict(text):
    # Rimuove spazi multipli orizzontali
    text = re.sub(r'[ \t]+', ' ', text)
    # Normalizza i ritorni a capo: massimo due consecutivi
    text = re.sub(r'\n\s*\n', '\n\n', text)
    # Pulisce l'inizio e la fine di ogni riga
    lines = [line.strip() for line in text.split('\n')]
    return '\n'.join(lines).strip()

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

        # 1. Trova il link AgID
        agid_link = ""
        for a in text_area.find_all('a'):
            href = a.get('href', '')
            if "cert-agid.gov.it" in href:
                agid_link = href
                break

        # 2. Logica Titolo: prendiamo tutti i grassetti
        bold_tags = text_area.find_all('b')
        if len(bold_tags) >= 2:
            # Se ci sono almeno due grassetti, il titolo vero è spesso il secondo
            # (il primo di solito è la categoria o la data)
            titolo = bold_tags[1].get_text(strip=True)
            # Rimuoviamo entrambi per pulire il corpo
            bold_tags[0].extract()
            bold_tags[1].extract()
        elif len(bold_tags) == 1:
            titolo = bold_tags[0].get_text(strip=True)
            bold_tags[0].extract()
        else:
            titolo = "AVVISO DI SICUREZZA"

        # 3. Formattazione Markdown per i tag rimasti
        for b in text_area.find_all('b'): b.replace_with(f"**{b.get_text()}**")
        for i in text_area.find_all('i'): i.replace_with(f"*{i.get_text()}*")

        # 4. Estrazione corpo con separatore controllato
        # Usiamo uno spazio per evitare che BeautifulSoup aggiunga \n dove ci sono già div
        corpo_testo = text_area.get_text(separator="\n")
        corpo_testo = clean_text_strict(corpo_testo)

        post_link_tag = last_msg.find('a', class_='tgme_widget_message_date')
        post_id = post_link_tag['href'] if post_link_tag else titolo
        
        return {
            "titolo": titolo.upper(),
            "corpo": corpo_testo,
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
        header = f"🛡️ **{data['titolo']}**\n\n"
        footer = f"\n\n🔗 [Leggi su AgID]({data['agid_url']})" if data['agid_url'] else ""

        full_message = f"{header}{data['corpo']}{footer}"

        # Invio (troncato a 2000 per sicurezza)
        requests.post(WEBHOOK_URL, json={"content": full_message[:2000]})
        
        with open(HISTORY_FILE, "a") as f: f.write(data['id'] + "\n")
        print(f"Inviato: {data['titolo']}")

if __name__ == "__main__":
    main()
