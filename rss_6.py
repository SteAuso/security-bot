import feedparser
import requests
import os
import re

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
# URL aggiornato a FalconFeedsIo via Google News
RSS_URL = "https://news.google.com/rss/search?q=site:https://x.com/FalconFeedsio+when:7d&hl=en-US&gl=US&ceid=US:en"
FILE_HISTORY = "history_6.txt"
LIMIT = 200

def main():
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        return

    # Lettura history
    if os.path.exists(FILE_HISTORY):
        with open(FILE_HISTORY, "r") as f:
            history = [line.strip() for line in f.readlines()]
    else:
        history = []

    nuovi_inviati = False
    
    #reversed serve per inviare prima i post più vecchi e finire con i più recenti
    for entry in reversed(feed.entries):
        link = entry.link
        
        if link not in history:
            # Pulizia del titolo dal suffisso di Google
            clean_title = re.sub(r' - (x\.com|Twitter)$', '', entry.title, flags=re.IGNORECASE).strip()
            
            print(f"Nuova news: {clean_title}")
            
            # Costruzione messaggio: Titolo + [Read More](<Link>)
            # Le parentesi < > attorno al link servono a NON far vedere l'anteprima di Google
            message = (
                f"🛡️ **FalconFeedsIo Cyber News**\n\n"
                f"{clean_title}\n\n"
                f"🔗 [Read More](<{link}>)"
            )
            
            requests.post(WEBHOOK_URL, json={"content": message})
            
            history.append(link)
            nuovi_inviati = True

    # Scrittura history (Sovrascrive il file con la lista aggiornata)
    if nuovi_inviati:
        history = history[-LIMIT:]
        with open(FILE_HISTORY, "w") as f:
            for item in history:
                f.write(f"{item}\n")
    else:
        print("Nulla di nuovo da inviare.")

if __name__ == "__main__":
    main()
