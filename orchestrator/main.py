"""
orchestrator/main.py
Point d'entrée principal — Boucle orchestrateur du projet site-builder-ia.

Usage :
    python orchestrator/main.py "crée un site web pour un restaurant italien"
    python orchestrator/main.py --teardown   (pour arrêter les conteneurs)
"""

import sys
import os
import argparse

# Permet d'importer depuis la racine du projet
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MAX_ITERATIONS
from orchestrator.planner import generate_plan

import agents.builder  as builder_agent
import agents.deployer as deployer_agent


# =============================================================================
# Dispatching des tâches
# =============================================================================

AGENT_REGISTRY = {
    "builder":  builder_agent.run,
    "deployer": deployer_agent.run,
}


def dispatch(agent_name: str, task: str) -> dict:
    """Appelle le bon agent pour la tâche donnée."""
    agent_fn = AGENT_REGISTRY.get(agent_name)
    if not agent_fn:
        return {"ok": False, "error": f"Agent inconnu : '{agent_name}'"}
    return agent_fn(task)


# =============================================================================
# Boucle principale de l'orchestrateur
# =============================================================================

def run_pipeline(user_request: str) -> dict:
    """
    Orchestre la construction et le déploiement d'un site web.

    1. Génère un plan via le Planner
    2. Exécute chaque étape du plan
    3. Boucle en cas d'erreur (jusqu'à MAX_ITERATIONS)
    4. Retourne le résultat final

    Returns:
        {"ok": bool, "url": str, "message": str, ...}
    """
    print("\n" + "=" * 60)
    print(" SITE-BUILDER-IA - Orchestrateur")
    print("=" * 60)
    print(f" Demande : {user_request}")
    print("=" * 60)

    # --- Génération du plan ---
    plan = generate_plan(user_request)
    if not plan["ok"]:
        return {"ok": False, "error": f"Planification échouée : {plan.get('error')}"}

    goal  = plan["goal"]
    steps = plan["steps"]

    print(f"\n[Orchestrateur] Objectif : {goal}")
    print(f"[Orchestrateur] {len(steps)} etape(s) planifiee(s)\n")

    # --- Boucle d'exécution avec retry ---
    iteration    = 0
    last_results = {}

    while iteration < MAX_ITERATIONS:
        iteration += 1
        print(f"\n{'─' * 60}")
        print(f" Itération {iteration}/{MAX_ITERATIONS}")
        print(f"{'─' * 60}")

        all_ok        = True
        last_results  = {}
        failed_step   = None

        for step_num, step in enumerate(steps, 1):
            agent_name = step.get("agent", "")
            task       = step.get("task", "")

            print(f"\n[Orchestrateur] Étape {step_num}/{len(steps)} → Agent '{agent_name}'")
            print(f"[Orchestrateur] Tâche : {task[:100]}{'...' if len(task) > 100 else ''}")

            result = dispatch(agent_name, task)
            last_results[agent_name] = result

            if not result.get("ok"):
                all_ok      = False
                failed_step = step
                print(f"\n[Orchestrateur] ECHEC de l'etape '{agent_name}'")
                print(f"[Orchestrateur] Erreur : {result.get('error', 'Inconnue')}")

                if result.get("fix"):
                    print(f"[Orchestrateur] Correction suggeree : {result['fix']}")

                # Modifier la tâche du builder pour corriger si on re-boucle
                if agent_name == "deployer" and iteration < MAX_ITERATIONS:
                    error_info = result.get("error", "")
                    fix_info   = result.get("fix", "")
                    for s in steps:
                        if s["agent"] == "builder":
                            s["task"] = (
                                f"[CORRECTION — Tentative {iteration + 1}] "
                                f"La tâche précédente a échoué : {error_info}. "
                                f"Correction suggérée : {fix_info}. "
                                f"Tâche originale : {task}"
                            )
                break  # On arrête les étapes de cette itération

        if all_ok:
            break

    # --- Résultat final ---
    print(f"\n{'=' * 60}")

    deployer_result = last_results.get("deployer", {})

    if all_ok and deployer_result.get("ok"):
        url = deployer_result.get("url", "http://localhost:8080")
        msg = deployer_result.get("message", "Site déployé avec succès !")
        print(f" OK - SUCCES : {msg}")
        print(f" URL   : {url}")
        print("=" * 60)
        return {"ok": True, "url": url, "message": msg}

    else:
        error = deployer_result.get("error") or last_results.get(
            failed_step["agent"] if failed_step else "", {}
        ).get("error", "Échec après toutes les tentatives")

        print(f" ECHEC apres {iteration} iteration(s)")
        print(f" Erreur : {error}")
        print("=" * 60)
        return {
            "ok": False,
            "error": error,
            "iterations": iteration,
            "results": last_results,
        }


# =============================================================================
# Entrée CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="site-builder-ia — Construit et déploie un site web via des agents IA"
    )
    parser.add_argument(
        "request",
        nargs="?",
        help='Demande en langage naturel, ex: "crée un site pour un restaurant"',
    )
    parser.add_argument(
        "--teardown",
        action="store_true",
        help="Arrête les conteneurs Docker en cours d'exécution",
    )

    args = parser.parse_args()

    if args.teardown:
        print("[Main] Arret des conteneurs...")
        result = deployer_agent.teardown()
        print(f"[Main] {'OK - Conteneurs arretes' if result['ok'] else 'ERREUR - ' + result.get('error', '')}")
        sys.exit(0 if result["ok"] else 1)

    if not args.request:
        parser.print_help()
        print("\nExemple : python orchestrator/main.py \"crée un site web pour un cabinet médical\"")
        sys.exit(1)

    result = run_pipeline(args.request)
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
