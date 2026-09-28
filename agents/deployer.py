"""
agents/deployer.py
Agent Deployer — Lance Docker Compose et vérifie le site via HTTP.
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ollama
from config import DEPLOYER_MODEL, SITE_URL
from tools.docker_ops import compose_up, compose_down, get_logs
from tools.http_check import check_url
from orchestrator.prompts import DEPLOYER_SYSTEM, DEPLOYER_USER_TEMPLATE


def run(task: str) -> dict:
    """
    Exécute l'agent Deployer.

    Args:
        task: Description de la tâche de déploiement

    Returns:
        {
            "ok": bool,
            "url": str (si succès),
            "status": "success" | "error",
            "message": str,
            "error": str (si erreur),
            "logs": str (si erreur)
        }
    """
    print(f"\n[Deployer] Tache recue : {task}")
    print(f"[Deployer] Modele : {DEPLOYER_MODEL}")

    # --- 1. Lancer Docker Compose ---
    print("[Deployer] Lancement de docker compose up...")
    compose_result = compose_up()
    print(f"[Deployer] Compose result : ok={compose_result['ok']}")

    # --- 2. Vérifier HTTP ---
    print(f"[Deployer] Verification HTTP sur {SITE_URL}...")
    http_result = check_url(SITE_URL)
    print(f"[Deployer] HTTP result : ok={http_result['ok']}")

    # --- 3. Récupérer les logs ---
    logs_result = get_logs()
    docker_logs = logs_result.get("logs", "Logs indisponibles")

    # Résultat rapide si tout va bien (pas besoin d'appeler le LLM)
    if compose_result["ok"] and http_result["ok"]:
        print(f"[Deployer] OK - Site deploye avec succes sur {SITE_URL}")
        return {
            "ok": True,
            "url": SITE_URL,
            "status": "success",
            "message": f"Site déployé et accessible sur {SITE_URL}",
        }

    # --- 4. Analyse via LLM en cas d'erreur ---
    print("[Deployer] Analyse des erreurs via Ollama...")
    user_message = DEPLOYER_USER_TEMPLATE.format(
        compose_result=json.dumps(compose_result, ensure_ascii=False),
        http_result=json.dumps(http_result, ensure_ascii=False),
        docker_logs=docker_logs[:2000],  # Limiter la taille
    )

    try:
        response = ollama.chat(
            model=DEPLOYER_MODEL,
            messages=[
                {"role": "system", "content": DEPLOYER_SYSTEM},
                {"role": "user",   "content": user_message},
            ],
            options={"temperature": 0.1},
        )
        raw_content = response["message"]["content"]
        analysis    = _extract_json(raw_content) or {}

    except Exception as e:
        analysis = {"error": f"Erreur Ollama (Deployer) : {e}"}

    # Construire le résultat d'erreur enrichi
    error_msg  = analysis.get("error", compose_result.get("error", "Erreur inconnue"))
    cause      = analysis.get("cause", "")
    fix        = analysis.get("fix", "")

    print(f"[Deployer] ERREUR : {error_msg}")
    if cause:
        print(f"[Deployer] Cause probable : {cause}")
    if fix:
        print(f"[Deployer] Correction suggeree : {fix}")

    return {
        "ok": False,
        "status": "error",
        "error": error_msg,
        "cause": cause,
        "fix": fix,
        "logs": docker_logs[:3000],
        "compose_result": compose_result,
        "http_result": http_result,
    }


def teardown() -> dict:
    """Arrête proprement les conteneurs Docker."""
    print("[Deployer] Arret des conteneurs...")
    return compose_down()


def _extract_json(text: str) -> dict | None:
    """Extrait le premier objet JSON valide d'un texte."""
    import re
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)

    start = text.find("{")
    end   = text.rfind("}")
    if start == -1 or end == -1:
        return None

    json_str = text[start:end + 1]
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        try:
            clean = re.sub(r",\s*([}\]])", r"\1", json_str)
            return json.loads(clean)
        except Exception:
            return None
