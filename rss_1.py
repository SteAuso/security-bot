import feedparser
import requests
import os

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
RSS_URL = "https://www.ransomware.live/rss.xml"
FILE_HISTORY = "history.txt"
LIMIT = 50

def main():
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        return

    # Carica la cronologia esistente
    if os.path.exists(FILE_HISTORY):
        with open(FILE_HISTORY, "r") as f:
            history = [line.strip() for line in f.readlines()]
    else:
        history = []

    nuovi_inviati = False
    
    # 2. Esamina le news (dalla più vecchia alla più recente per l'ordine cronologico su Discord)
    # feed.entries è solitamente ordinato dal più nuovo al più vecchio, quindi lo invertiamo
    for entry in reversed(feed.entries):
        link = entry.link
        
        if link not in history:
            print(f"Nuova news: {entry.title}")
            
            # Invia a Discord
            message = f"**{entry.title}**\n\n{link}"
            requests.post(WEBHOOK_URL, json={"content": message})
            
            # Aggiungi alla cronologia
            history.append(link)
            nuovi_inviati = True

    # 3. Mantieni solo gli ultimi 50 link e salva
    if nuovi_inviati:
        history = history[-LIMIT:] # Prende gli ultimi 50
        with open(FILE_HISTORY, "w") as f:
            for item in history:
                f.write(f"{item}\n")
    else:
        print("Nulla di nuovo da inviare.")

if __name__ == "__main__":
    main()
