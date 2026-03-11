import feedparser
import requests
import os
import re

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
RSS_URL = "https://news.google.com/rss/search?q=site:https://x.com/H4ckmanac+when:7d&hl=en-US&gl=US&ceid=US:en"
FILE_HISTORY = "history_5.txt"
LIMIT = 50 # Alziamo un po' il limite per sicurezza

def main():
    # 1. Caricamento Feed
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        return

    # 2. Caricamento History con pulizia
    history = []
    if os.path.exists(FILE_HISTORY):
        with open(FILE_HISTORY, "r", encoding="utf-8") as f:
            # strip() rimuove spazi e a capo, filter elimina righe vuote
            history = [line.strip() for line in f if line.strip()]

    nuovi_inviati = False
    nuovi_titoli = []
    
    # 3. Analisi post (dal più vecchio al più nuovo)
    for entry in reversed(feed.entries):
        # Puliamo il titolo per usarlo come chiave unica
        # Togliamo spazi extra e il suffisso " - x.com"
        raw_title = entry.title
        clean_title_key = re.sub(r' - (x\.com|Twitter)$', '', raw_title, flags=re.IGNORECASE).strip()
        
        if clean_title_key not in history:
            print(f"Nuova news trovata: {clean_title_key}")
            
            # Formattazione messaggio (Stile Cert-AGID)
            # < > attorno al link impedisce l'anteprima (embed) di Google News
            message = (
                f"🛡️ **Hackmanac Cyber News**\n\n"
                f"{clean_title_key}\n\n"
                f"🔗 [Read More](<{entry.link}>)"
            )
            
            # Invio a Discord
            response = requests.post(WEBHOOK_URL, json={"content": message})
            
            if response.status_code in [200, 204]:
                history.append(clean_title_key)
                nuovi_inviati = True
        else:
            print(f"News già presente in history: {clean_title_key[:30]}...")

    # 4. Salvataggio History (solo se ci sono novità)
    if nuovi_inviati:
        # Teniamo solo gli ultimi LIMIT titoli
        history = history[-LIMIT:]
        with open(FILE_HISTORY, "w", encoding="utf-8") as f:
            for item in history:
                f.write(f"{item}\n")
        print("History aggiornata correttamente.")
    else:
        print("Nessun nuovo post da inviare.")

if __name__ == "__main__":
    main()
