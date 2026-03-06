import requests
from bs4 import BeautifulSoup
import os
import re

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
CHANNEL_URL = "https://t.me/s/certagid"
HISTORY_FILE = "history_3.txt"

def fix_telegram_spacing(text):
    # 1. Rimuove gli spazi bianchi multipli orizzontali
    text = re.sub(r'[ \t]+', ' ', text)
    # 2. Rimuove i singoli "a capo" che spezzano le frasi (spesso dopo le emoji)
    # Se un 'a capo' è seguito da una lettera minuscola o non è preceduto da punteggiatura forte, lo togliamo
    text = re.sub(r'(?<![.!?])\n(?=[a-z])', ' ', text)
    # 3. Normalizza i doppi "a capo" per i paragrafi veri
    text = re.sub(r'\n{2,}', '\n\n', text)
    return text.strip()

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

        # Recupero link AgID
        agid_link = ""
        for a in text_area.find_all('a'):
            href = a.get('href', '')
            if "cert-agid.gov.it" in href:
                agid_link = href
                break

        # Trasformazione grassetti e corsivi
        for b in text_area.find_all('b'): b.replace_with(f"**{b.get_text()}**")
        for i in text_area.find_all('i'): i.replace_with(f"*{i.get_text()}*")

        # Estrazione testo: usiamo un separatore neutro per poi pulirlo
        raw_text = text_area.get_text(separator="\n")
        
        # Pulizia specifica per i glitch delle emoji e i doppi invii
        clean_text = fix_telegram_spacing(raw_text)
        
        lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
        if not lines: return None

        # Titolo: prima riga (pulita da asterischi)
        titolo_raw = lines[0].replace('**', '').replace('*', '')
        # Corpo: tutto il resto
        corpo_final = '\n'.join(lines[1:])

        post_link_tag = last_msg.find('a', class_='tgme_widget_message_date')
        post_id = post_link_tag['href'] if post_link_tag else titolo_raw
        
        return {
            "titolo": titolo_raw,
            "corpo": corpo_final,
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
        # Messaggio finale
        full_message = f"🛡️ **{data['titolo'].upper()}**\n\n{data['corpo']}"
        
        if data['agid_url']:
            full_message += f"\n\n🔗 [Leggi l'avviso completo]({data['agid_url']})"

        requests.post(WEBHOOK_URL, json={"content": full_message[:2000]})
        
        with open(HISTORY_FILE, "a") as f: 
            f.write(data['id'] + "\n")
        print(f"Inviato: {data['titolo']}")

if __name__ == "__main__":
    main()
