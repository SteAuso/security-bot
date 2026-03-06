import requests
from bs4 import BeautifulSoup
import os
import re

# Configurazione
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
CHANNEL_URL = "https://t.me/s/certagid"
HISTORY_FILE = "history_3.txt"

def get_latest_post():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(CHANNEL_URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Recupero l'ultimo post
        messages = soup.find_all('div', class_='tgme_widget_message_wrap')
        if not messages:
            return None

        last_msg = messages[-1]
        text_area = last_msg.find('div', class_='tgme_widget_message_text')
        if not text_area:
            return None

        # --- STEP 1: BONIFICA PREVENTIVA TAG VUOTI ---
        # Rimuove tag come <b> </b> o <i></i> che contengono solo spazi o nulla
        for tag in text_area.find_all(['b', 'i', 'code', 'span']):
            if not tag.get_text(strip=True):
                tag.decompose()

        # --- STEP 2: ESTRAZIONE LINK AgID ---
        agid_link = ""
        for a in text_area.find_all('a'):
            href = a.get('href', '')
            if "cert-agid.gov.it" in href:
                agid_link = href
                # Lo rimuoviamo dal corpo per evitare doppioni
                a.decompose() 

        # --- STEP 3: CONVERSIONE MARKDOWN SELETTIVA ---
        for tag_name in ["b", "i", "code"]:
            for tag in text_area.find_all(tag_name):
                content = tag.get_text()
                # Salta se contiene hashtag o se non ha caratteri alfanumerici (es. solo emoji)
                if "#" in content or not re.search(r'[a-zA-Z0-9]', content):
                    tag.replace_with(content)
                else:
                    prefix = "**" if tag_name == "b" else "*" if tag_name == "i" else "`"
                    tag.replace_with(f"{prefix}{content}{prefix}")

        # --- STEP 4: GESTIONE A CAPO (<br>) ---
        for br in text_area.find_all("br"):
            br.replace_with("\n")

        # --- STEP 5: PULIZIA TESTO GREZZO ---
        testo_raw = text_area.get_text().strip()
        
        # Rimuove emoji 🔗 orfana e link testuali residui
        testo_raw = testo_raw.replace("🔗", "")
        testo_raw = re.sub(r'https?://cert-agid\.gov\.it/\S*', '', testo_raw).strip()

        # --- STEP 6: FORMATTAZIONE TITOLO (GRASSETTO PULITO) ---
        # Dividiamo il testo al primo doppio "a capo"
        parti = testo_raw.split('\n\n', 1)
        
        if len(parti) > 1:
            # Pialliamo ogni asterisco pre-esistente nella prima riga
            titolo_pulito = parti[0].replace('*', '').strip()
            corpo = parti[1].strip()
            testo_finale = f"**{titolo_pulito}**\n\n{corpo}" if titolo_pulito else corpo
        else:
            titolo_pulito = testo_raw.replace('*', '').strip()
            testo_finale = f"**{titolo_pulito}**"

        # --- STEP 7: PULIZIA FINALE "GHOST ASTERISKS" ---
        # Rimuove glitch come ** ** o **** derivanti da pulizie precedenti
        testo_finale = re.sub(r'\*+\s*\*+', '', testo_finale)
        testo_finale = re.sub(r'\*{4,}', '', testo_finale)

        # ID univoco per la cronologia
        post_link_tag = last_msg.find('a', class_='tgme_widget_message_date')
        post_id = post_link_tag['href'] if post_link_tag else testo_finale[:50]
        
        return {
            "testo": testo_finale,
            "id": post_id,
            "agid_url": agid_link
        }
    except Exception as e:
        print(f"Errore durante lo scraping: {e}")
        return None

def main():
    if not WEBHOOK_URL:
        print("Errore: La variabile DISCORD_WEBHOOK non è configurata.")
        return
    
    # Carico cronologia
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            history = f.read().splitlines()

    data = get_latest_post()
    
    if data and data['id'] not in history:
        # Messaggio finale
        messaggio_discord = data['testo']
        
        # Aggiungo il link AgID in fondo se trovato
        if data['agid_url']:
            messaggio_discord += f"\n\n🔗 [Leggi l'avviso completo su AgID]({data['agid_url']})"

        # Invio a Discord
        payload = {"content": messaggio_discord[:2000]} # Limite caratteri Discord
        response = requests.post(WEBHOOK_URL, json=payload)
        
        if response.status_code == 204:
            # Salvo in cronologia solo se l'invio ha avuto successo
            with open(HISTORY_FILE, "a") as f:
                f.write(data['id'] + "\n")
            print(f"Post inviato con successo: {data['id']}")
        else:
            print(f"Errore invio Discord: {response.status_code}")
    else:
        print("Nessun nuovo post da inviare.")

if __name__ == "__main__":
    main()
