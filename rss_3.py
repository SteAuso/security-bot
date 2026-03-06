import requests
from bs4 import BeautifulSoup
import os
import re # Usiamo le Regular Expressions per pulire i testi

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
CHANNEL_URL = "https://t.me/s/certagid"
HISTORY_FILE = "history_3.txt"

def clean_extra_newlines(text):
    # Sostituisce 3 o più a capo con solo 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Rimuove spazi bianchi a fine riga
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

        # 1. ESTRAZIONE TITOLO
        bold_tag = text_area.find('b')
        if bold_tag:
            titolo = bold_tag.get_text(strip=True)
            bold_tag.extract() # Rimuove il tag per non averlo nel corpo
        else:
            titolo = "NUOVO AGGIORNAMENTO"

        # 2. CONVERSIONE FORMATTAZIONE (senza aggiungere a capo extra)
        for b in text_area.find_all('b'): b.replace_with(f"**{b.get_text()}**")
        for i in text_area.find_all('i'): i.replace_with(f"*{i.get_text()}*")
        for code in text_area.find_all('code'): code.replace_with(f"`{code.get_text()}`")

        # 3. ESTRAZIONE CORPO (Usiamo uno spazio come separatore temporaneo per evitare i doppi \n)
        corpo_testo = text_area.get_text(separator="\n").strip()
        
        # 4. PULIZIA FINALE DEGLI "A CAPO"
        corpo_testo = clean_extra_newlines(corpo_testo)

        post_link_tag = last_msg.find('a', class_='tgme_widget_message_date')
        post_link = post_link_tag['href'] if post_link_tag else ""

        ext_links = []
        for a in text_area.find_all('a'):
            href = a.get('href', '')
            if href and "t.me" not in href: ext_links.append(href)
        
        return {
            "titolo": titolo.upper(),
            "corpo": corpo_testo,
            "link": post_link,
            "external_links": list(set(ext_links))
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
    
    if data and data['link'] not in history:
        header = f"🛡️ **{data['titolo']}**\n\n"
        footer = f"\n\n🔗 [Post Originale]({data['link']})"
        
        links_section = ""
        if data['external_links']:
            links_section = "\n\n**Approfondimenti:**\n" + "\n".join(data['external_links'])

        full_message = f"{header}{data['corpo']}{links_section}{footer}"

        # Invio a Discord (limitato a 2000 caratteri)
        requests.post(WEBHOOK_URL, json={"content": full_message[:2000]})
        
        with open(HISTORY_FILE, "a") as f: f.write(data['link'] + "\n")
        print(f"Inviato: {data['titolo']}")

if __name__ == "__main__":
    main()
