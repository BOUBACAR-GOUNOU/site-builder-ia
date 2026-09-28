"""
tools/http_check.py
Vérifie qu'un site web est accessible et répond HTTP 200.
"""

import time
import requests
from config import HTTP_TIMEOUT, HTTP_RETRIES, HTTP_WAIT


def check_url(url: str) -> dict:
    """
    Vérifie qu'une URL répond avec HTTP 200.
    Effectue plusieurs tentatives avec délai entre chacune.

    Retourne :
        {"ok": True,  "url": url, "status_code": 200}
        {"ok": False, "url": url, "error": message, "last_status": code ou None}
    """
    last_status = None
    last_error = None

    for attempt in range(1, HTTP_RETRIES + 1):
        try:
            print(f"[HTTP] Tentative {attempt}/{HTTP_RETRIES} → {url}")
            response = requests.get(url, timeout=HTTP_TIMEOUT, allow_redirects=True)
            last_status = response.status_code

            if response.status_code == 200:
                print(f"[HTTP] OK - Site accessible : {url} (HTTP {response.status_code})")
                return {"ok": True, "url": url, "status_code": response.status_code}
            else:
                last_error = f"HTTP {response.status_code}"
                print(f"[HTTP] WARN - Reponse inattendue : HTTP {response.status_code}")

        except requests.exceptions.ConnectionError as e:
            last_error = "Connexion refusée (conteneur pas encore prêt ?)"
            print(f"[HTTP] ERREUR - Connexion echouee : {e}")
        except requests.exceptions.Timeout:
            last_error = f"Timeout après {HTTP_TIMEOUT}s"
            print(f"[HTTP] ERREUR - Timeout sur {url}")
        except Exception as e:
            last_error = str(e)
            print(f"[HTTP] ERREUR : {e}")

        if attempt < HTTP_RETRIES:
            print(f"[HTTP] Attente {HTTP_WAIT}s avant nouvelle tentative...")
            time.sleep(HTTP_WAIT)

    return {
        "ok": False,
        "url": url,
        "error": last_error or "Site inaccessible après toutes les tentatives",
        "last_status": last_status,
    }
