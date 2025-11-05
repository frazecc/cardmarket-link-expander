import gspread
import requests
import json
import os
from google.oauth2.service_account import Credentials

# === 1. Carica credenziali dal secret GitHub ===
creds_json = os.environ["GOOGLE_CREDENTIALS"]
creds_data = json.loads(creds_json)

scopes = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(creds_data, scopes=scopes)

# === 2. Connessione al Google Sheet ===
gc = gspread.authorize(creds)

# ⚠️ INSERISCI QUI L'ID DEL TUO FOGLIO GOOGLE
SHEET_ID = "1f23II9ZqArltE_QXQ9o-Ai57iPgBhkyKsDsvSfe5caA"
worksheet = gc.open_by_key(SHEET_ID).sheet1

# === 3. Leggi i link dalla colonna G ===
links = worksheet.col_values(7)  # colonna G
for i, url in enumerate(links[1:], start=2):  # salta intestazione
    if not url:
        continue
    try:
        # === 4. Segui redirect fino al link finale ===
        response = requests.get(url, allow_redirects=True)
        final_url = response.url

        # === 5. Scrivi nella colonna H ===
        worksheet.update_cell(i, 8, final_url)
        print(f"✅ Riga {i}: {final_url}")
    except Exception as e:
        print(f"❌ Errore alla riga {i}: {e}")
