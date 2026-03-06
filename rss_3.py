import requests
from bs4 import BeautifulSoup
import os
import re

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
CHANNEL_URL = "https://t.me/s/certagid"
HISTORY_FILE = "history_3.txt"

def clean_extra_newlines(text):
    text = re.sub(r'\n{3,}', '\n\n', text)
    lines = [line.strip() for line in text.split('\n')]
    return '\n'.join(lines)

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

        # 1. CERCA IL LINK AD AGID PRIMA DI COMINCIARE A MODIFICARE L'HTML
        agid_link = ""
        for a in text_area.find_all('a'):
            href = a.get('href', '')
            if "cert-agid.gov.it" in href:
                agid_link = href
                break # Prendiamo il primo link istituzionale che troviamo

        # 2. ESTRAZIONE TITOLO (Primo grassetto)
        bold_tag = text_area.find('b')
        if bold_tag:
            titolo = bold_tag.get_text(strip=True)
            bold_tag.extract() 
        else:
            titolo = "NUOVO AGGIORNAMENTO"

        # 3. CONVERSIONE FORMATTAZIONE
        for b in text_area.find_all('b'): b.replace_with(f"**{b.get_text()}**")
        for i in text_area.find_all('i'): i.replace_with(f"*{i.get_text()}*")
        for code in text_area.find_all('code'): code.replace_with(f"`{code.get_text()}`")

        # 4. PULIZIA CORPO
        corpo_testo = text_area.get_text(separator="\n").strip()
        corpo_testo = clean_extra_newlines(corpo_testo)

        # 5. ID PER CRONOLOGIA (usiamo il link del post Telegram solo come ID interno)
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
        
        # Aggiunge il link AgID solo se è stato trovato nel post
        footer = ""
        if data['agid_url']:
            footer = f"\n\n🔗 [Leggi l'avviso completo sul sito AgID]({data['agid_url']})"

        full_message = f"{header}{data['corpo']}{footer}"

        requests.post(WEBHOOK_URL, json={"content": full_message[:2000]})
        
        with open(HISTORY_FILE, "a") as f: f.write(data['id'] + "\n")
        print(f"Inviato: {data['titolo']}")

if __name__ == "__main__":
    main()
