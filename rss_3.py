import requests
from bs4 import BeautifulSoup
import os

# Configurazione recuperata dai Secret/Ambiente
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
        
        # Trova tutti i messaggi nella pagina
        messages = soup.find_all('div', class_='tgme_widget_message_wrap')
        if not messages:
            return None

        # Prendiamo l'ultimo
        last_msg = messages[-1]
        
        # Estrazione ID/Link del post per la cronologia
        post_link_tag = last_msg.find('a', class_='tgme_widget_message_date')
        post_link = post_link_tag['href'] if post_link_tag else ""
        
        # Estrazione Testo
        text_area = last_msg.find('div', class_='tgme_widget_message_text')
        text = text_area.get_text(separator="\n") if text_area else "Nessun testo"

        # Estrazione link esterni (quelli cliccabili nel post)
        ext_links = []
        if text_area:
            for a in text_area.find_all('a'):
                href = a.get('href', '')
                if href and "t.me" not in href:
                    ext_links.append(href)
        
        return {
            "link": post_link,
            "text": text,
            "external_links": list(set(ext_links))
        }
    except Exception as e:
        print(f"Errore durante lo scraping: {e}")
        return None

def main():
    if not WEBHOOK_URL:
        print("ERRORE: Variabile DISCORD_WEBHOOK non trovata!")
        return

    # Carica cronologia
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            history = f.read().splitlines()

    data = get_latest_post()
    
    if data and data['link'] not in history:
        # Costruisci il contenuto del messaggio
        # Limitiamo il testo per evitare di superare i limiti di Discord (2000 car)
        clean_text = data['text'][:1500] + ("..." if len(data['text']) > 1500 else "")
        
        message = f"📢 **NUOVO POST TELEGRAM: @certagid**\n\n{clean_text}\n"
        
        if data['external_links']:
            message += "\n🔗 **Link nel post:**\n" + "\n".join(data['external_links'])
        
        message += f"\n\n[Apri su Telegram]({data['link']})"

        # Invia a Discord
        resp = requests.post(WEBHOOK_URL, json={"content": message})
        
        if resp.status_code in [200, 204]:
            print("Messaggio inviato con successo!")
            # Salva in cronologia
            with open(HISTORY_FILE, "a") as f:
                f.write(data['link'] + "\n")
        else:
            print(f"Errore Discord: {resp.status_code} - {resp.text}")
    else:
        print("Nessun nuovo post da inviare.")

if __name__ == "__main__":
    main()
