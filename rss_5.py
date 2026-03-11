import feedparser
import requests
import os
import re

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
RSS_URL = "https://news.google.com/rss/search?q=site:https://x.com/H4ckmanac+when:7d&hl=en-US&gl=US&ceid=US:en"
FILE_HISTORY = "history_5.txt"
LIMIT = 30

def main():
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        return

    if os.path.exists(FILE_HISTORY):
        with open(FILE_HISTORY, "r") as f:
            history = [line.strip() for line in f.readlines()]
    else:
        history = []

    nuovi_inviati = False
    
    # Analizziamo i post
    for entry in reversed(feed.entries):
        # Usiamo l'ID del post per la cronologia (più stabile del link)
        post_id = entry.id
        
        if post_id not in history:
            print(f"Nuova news: {entry.title}")
            
            # Puliamo il titolo (togliamo il suffisso di Google News)
            clean_title = re.sub(r' - (x\.com|Twitter)$', '', entry.title, flags=re.IGNORECASE)
            
            # Formattazione stile Cert-AGID:
            # Il link è dentro < > per evitare che Discord generi l'anteprima grigia di Google
            message = (
                f"🛡️ **Hackmanac Cyber News**\n\n"
                f"{clean_title}\n\n"
                f"🔗 [Read More](<{entry.link}>)"
            )
            
            # Invio al Webhook
            requests.post(WEBHOOK_URL, json={"content": message})
            
            history.append(post_id)
            nuovi_inviati = True

    # Aggiornamento file history
    if nuovi_inviati:
        history = history[-LIMIT:]
        with open(FILE_HISTORY, "w") as f:
            for item in history:
                f.write(f"{item}\n")
    else:
        print("Nessun nuovo aggiornamento.")

if __name__ == "__main__":
    main()
