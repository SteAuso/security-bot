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

    # 1. LEGGIAMO LA HISTORY ESISTENTE
    if os.path.exists(FILE_HISTORY):
        with open(FILE_HISTORY, "r", encoding="utf-8") as f:
            # Creiamo un set per una ricerca velocissima e pulita
            history = {line.strip() for line in f if line.strip()}
    else:
        history = set()

    # Usiamo una lista per mantenere l'ordine dei nuovi titoli da aggiungere
    new_titles_added = []
    
    # 2. CICLO SUI POST (dal più vecchio al più nuovo)
    for entry in reversed(feed.entries):
        # Pulizia titolo
        clean_title = re.sub(r' - (x\.com|Twitter)$', '', entry.title, flags=re.IGNORECASE).strip()
        
        if clean_title not in history:
            print(f"Nuova news: {clean_title}")
            
            # Formattazione stile Cert-AGID
            message = (
                f"🛡️ **Hackmanac Cyber News**\n\n"
                f"{clean_title}\n\n"
                f"🔗 [Read More](<{entry.link}>)"
            )
            
            # Invio a Discord
            try:
                res = requests.post(WEBHOOK_URL, json={"content": message})
                if res.status_code in [200, 204]:
                    # Aggiungiamo alla history solo se l'invio è riuscito
                    history.add(clean_title)
                    new_titles_added.append(clean_title)
            except Exception as e:
                print(f"Errore invio: {e}")

    # 3. RISCRIVIAMO IL FILE DA ZERO
    # Convertiamo il set in lista per poter prendere gli ultimi LIMIT
    # Ordiniamo o semplicemente limitiamo la dimensione
    updated_history = list(history)
    
    # Teniamo solo gli ultimi LIMIT elementi
    updated_history = updated_history[-LIMIT:]

    # Il modo "w" (write) sovrascrive completamente il file esistente
    with open(FILE_HISTORY, "w", encoding="utf-8") as f:
        for title in updated_history:
            f.write(f"{title}\n")
    
    if new_titles_added:
        print(f"Fatto! Inviati {len(new_titles_added)} nuovi post.")
    else:
        print("Nulla di nuovo.")

if __name__ == "__main__":
    main()
