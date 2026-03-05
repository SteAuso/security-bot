import feedparser
import requests
import os

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_2")
RSS_URL = "https://www.acn.gov.it/portale/feedrss/-/journal/rss/20119/723192"
FILE_HISTORY = "history_2.txt"
LIMIT = 10

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
    
    for entry in reversed(feed.entries):
        link = entry.link
        
        if link not in history:
            print(f"Nuova news: {entry.title}")
            
            message = f"**{entry.title}**\n{entry.description}\n\\n\n{link}"
            requests.post(WEBHOOK_URL_2, json={"content": message})
            
            history.append(link)
            nuovi_inviati = True

    if nuovi_inviati:
        history = history[-LIMIT:]
        with open(FILE_HISTORY, "w") as f:
            for item in history:
                f.write(f"{item}\n")
    else:
        print("Nulla di nuovo da inviare.")

if __name__ == "__main__":
    main()
