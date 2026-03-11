import feedparser
import requests
import os

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
RSS_URL = "https://news.google.com/rss/search?q=site:https://x.com/H4ckmanac+when:7d&hl=en-US&gl=US&ceid=US:en"
FILE_HISTORY = "history_5.txt"
LIMIT = 30

def get_final_url(google_link):
    """Segue il redirect di Google News per ottenere il link reale di X"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        # Usiamo una GET ma ci fermiamo appena riceviamo l'URL finale
        # Il timeout evita che lo script si blocchi se Google è lento
        r = requests.get(google_link, headers=headers, timeout=10, allow_redirects=True)
        final_url = r.url
        
        # Opzionale: Trasforma x.com in fxtwitter.com per anteprime Discord migliori
        if "x.com" in final_url:
            final_url = final_url.replace("x.com", "fxtwitter.com")
            
        return final_url
    except Exception as e:
        print(f"Errore nel recupero URL finale: {e}")
        return google_link

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
    
    # Prendiamo solo gli ultimi 5 post per non saturare i redirect se lo script è fermo da tempo
    for entry in reversed(feed.entries[:5]):
        google_link = entry.link
        
        # Usiamo il titolo per la history invece del link di Google (che cambia spesso parametri)
        if entry.title not in history:
            print(f"Nuova news: {entry.title}")
            
            # Recuperiamo il link reale con requests
            real_link = get_final_url(google_link)
            
            message = f"🛡️ **{entry.title}**\n\n🔗 {real_link}"
            requests.post(WEBHOOK_URL, json={"content": message})
            
            history.append(entry.title)
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
