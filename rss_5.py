import requests
from bs4 import BeautifulSoup
import os

# Configurazione
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
CHANNEL_URL = "https://news.google.com/rss/search?q=site:https://x.com/H4ckmanac+when:7d&hl=en-US&gl=US&ceid=US:en"
HISTORY_FILE = "history_5.txt"
LIMIT = 5 # Controlla gli ultimi 5 messaggi per ogni esecuzione

def get_latest_posts():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(CHANNEL_URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Recupera tutti i blocchi messaggio
        messages = soup.find_all('div', class_='tgme_widget_message_wrap')
        if not messages:
            return []
        
        posts_data = []
        for msg in messages[-LIMIT:]:
            # 1. Estrazione ID Post (URL univoco)
            post_link_tag = msg.find('a', class_='tgme_widget_message_date')
            post_id = post_link_tag['href'] if post_link_tag else None
            
            # 2. Estrazione Testo
            text_area = msg.find('div', class_='tgme_widget_message_text')
            if not text_area or not post_id:
                continue

            # Recupero testo mantenendo i ritorni a capo originali
            testo_raw = text_area.get_text(separator='\n').strip()

            posts_data.append({
                "id": post_id,
                "testo": testo_raw
            })
            
        return posts_data

    except Exception as e:
        print(f"Errore durante il recupero da Telegram: {e}")
        return []

def main():
    if not WEBHOOK_URL:
        print("Errore: DISCORD_WEBHOOK non configurato.")
        return
    
    # Caricamento cronologia
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            history = f.read().splitlines()

    # Recupero post recenti
    posts = get_latest_posts()
    
    nuovi_inviati = False
    for post in posts:
        if post['id'] not in history:
            # Invio il testo così come viene estratto (neutro)
            # Taglio a 2000 caratteri per limiti Discord
            payload = {"content": post['testo'][:2000]}
            
            response = requests.post(WEBHOOK_URL, json=payload)
            
            if response.status_code in [200, 204]:
                print(f"Inviato post: {post['id']}")
                history.append(post['id'])
                nuovi_inviati = True
            else:
                print(f"Errore invio Webhook ({post['id']}): {response.status_code}")

    # Salvataggio cronologia se ci sono aggiornamenti
    if nuovi_inviati:
        with open(HISTORY_FILE, "w") as f:
            # Mantieni solo gli ultimi 50 per pulizia
            f.write("\n".join(history[-50:]))
    else:
        print("Nessun nuovo post da Hackmanac.")

if __name__ == "__main__":
    main()
