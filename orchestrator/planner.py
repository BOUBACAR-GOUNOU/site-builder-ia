"""
orchestrator/planner.py
Planificateur — Utilise Ollama (qwen2.5:1.5b) pour générer un plan d'exécution JSON.
"""

import json
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ollama
from config import PLANNER_MODEL
from orchestrator.prompts import PLANNER_SYSTEM, PLANNER_USER_TEMPLATE


def generate_plan(user_request: str) -> dict:
    """
    Génère un plan d'exécution structuré à partir de la demande utilisateur.

    Args:
        user_request: La demande de l'utilisateur en langage naturel.

    Returns:
        {
            "ok": bool,
            "goal": str,
            "steps": [{"agent": str, "task": str}, ...],
            "error": str (si ok=False)
        }
    """
    print(f"\n[Planner] Generation du plan pour : {user_request}")
    print(f"[Planner] Modele : {PLANNER_MODEL}")

    user_message = PLANNER_USER_TEMPLATE.format(user_request=user_request)

    try:
        response = ollama.chat(
            model=PLANNER_MODEL,
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM},
                {"role": "user",   "content": user_message},
            ],
            options={"temperature": 0.1},
        )
        raw_content = response["message"]["content"]
        print(f"[Planner] Reponse recue ({len(raw_content)} caracteres)")

    except Exception as e:
        # Si Ollama échoue, on utilise un plan par défaut
        print(f"[Planner] WARN - Ollama indisponible, plan par defaut utilise. Erreur : {e}")
        return _default_plan(user_request)

    # Parsing du JSON
    parsed = _extract_json(raw_content)
    if not parsed or "steps" not in parsed:
        print("[Planner] WARN - JSON invalide, plan par defaut utilise.")
        print(f"[Planner] Réponse brute : {raw_content[:500]}")
        return _default_plan(user_request)

    steps = parsed.get("steps", [])
    goal  = parsed.get("goal", user_request)

    print(f"[Planner] Plan genere : {goal}")
    for i, step in enumerate(steps, 1):
        print(f"[Planner]   Étape {i}: [{step.get('agent', '?')}] {step.get('task', '?')}")

    return {
        "ok": True,
        "goal": goal,
        "steps": steps,
    }


def _default_plan(user_request: str) -> dict:
    """Plan par défaut si le LLM ne répond pas correctement."""
    return {
        "ok": True,
        "goal": user_request,
        "steps": [
            {
                "agent": "builder",
                "task": f"Crée un site web complet pour : {user_request}. "
                        f"Génère index.html, style.css, Dockerfile et docker-compose.yml.",
            },
            {
                "agent": "deployer",
                "task": "Build l'image Docker, lance docker-compose et vérifie que le site répond sur http://localhost:8080.",
            },
        ],
    }


def _extract_json(text: str) -> dict | None:
    """Extrait le premier objet JSON valide d'un texte."""
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
