import requests
from bs4 import BeautifulSoup
import os
import re

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
CHANNEL_URL = "https://t.me/s/certagid"
HISTORY_FILE = "history_telegram.txt"

def clean_extra_newlines(text):
    # Sostituisce 3 o più a capo con al massimo due
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Rimuove spazi bianchi a inizio e fine di ogni riga
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

        # 1. ESTRAZIONE TITOLO (Primo grassetto)
        bold_tag = text_area.find('b')
        if bold_tag:
            titolo = bold_tag.get_text(strip=True)
            bold_tag.extract() # Rimosso fisicamente per evitare duplicati
        else:
            titolo = "NUOVO AGGIORNAMENTO"

        # 2. CONVERSIONE FORMATTAZIONE HTML -> MARKDOWN
        for b in text_area.find_all('b'): b.replace_with(f"**{b.get_text()}**")
        for i in text_area.find_all('i'): i.replace_with(f"*{i.get_text()}*")
        for code in text_area.find_all('code'): code.replace_with(f"`{code.get_text()}`")

        # 3. ESTRAZIONE E PULIZIA CORPO DEL TESTO
        corpo_testo = text_area.get_text(separator="\n").strip()
        corpo_testo = clean_extra_newlines(corpo_testo)

        # 4. LINK DEL POST ORIGINALE
        post_link_tag = last_msg.find('a', class_='tgme_widget_message_date')
        post_link = post_link_tag['href'] if post_link_tag else
