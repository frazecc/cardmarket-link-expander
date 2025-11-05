#!/usr/bin/env python3
import time
import argparse
import json
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
import gspread
from google.oauth2.service_account import Credentials

# --- Configurazione: foglio e colonne ---
SPREADSHEET_NAME = "NOME_DEL_TUO_FOGLIO"   # <-- modifica qui con il nome del foglio Google (esatto)
SHEET_NAME = "Foglio1"                     # <-- nome del tab (modifica se serve)
LINK_COL = 7   # colonna G -> indice 7 (1-based per gspread? useremo A1 range)
RESULT_OFFSET = 1  # scrive nella colonna a destra (H)

# --- Helper ---
def get_gspread_client_from_file(creds_file):
    creds_dict = json.load(open(creds_file, 'r'))
    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(credentials)

def expand_links_and_update(sheet):
    # Legge tutte le righe che contengono qualcosa nella colonna G
    all_values = sheet.get_all_values()
    # gspread usa lista di liste; indice colonna = LINK_COL - 1
    for row_idx, row in enumerate(all_values, start=1):
        try:
            # Se la riga è più corta, gestiamo
            link = row[LINK_COL-1].strip() if len(row) >= LINK_COL else ""
            if not link:
                continue
            # Salta se già presente URL finale nella colonna H (opzionale)
            already = row[LINK_COL-1 + RESULT_OFFSET] if len(row) >= LINK_COL + RESULT_OFFSET else ""
            if already:
                # puoi commentare questa riga per forzare la riscrittura
                continue

            # Apri con Selenium
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

            try:
                driver.get(link)
                # attendi qualche secondo per consentire redirect lato client
                time.sleep(3)
                final = driver.current_url
            finally:
                driver.quit()

            # Scrivi nella cella H della stessa riga
            target_col = LINK_COL + RESULT_OFFSET
            cell_label = gspread.utils.rowcol_to_a1(row_idx, target_col)
            sheet.update_acell(cell_label, final)
            print(f"Riga {row_idx}: scritto {final}")

            # attesa prudente per non sovraccaricare il sito
            time.sleep(2)
        except Exception as ex:
            print(f"Errore riga {row_idx}: {ex}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--payload', help='File JSON con payload opzionale', default=None)
    args = parser.parse_args()

    creds_file = "/tmp/creds.json"
    # in GitHub Actions scriviamo il file in /tmp/creds.json
    # se vuoi testare in locale, cambia il path o imposta env var

    client = get_gspread_client_from_file(creds_file)
    ss = client.open(SPREADSHEET_NAME)
    sheet = ss.worksheet(SHEET_NAME)

    expand_links_and_update(sheet)

if __name__ == "__main__":
    main()
