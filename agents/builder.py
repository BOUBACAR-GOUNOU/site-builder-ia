"""
agents/builder.py
Agent Builder — Génère les fichiers du projet via Ollama, fichier par fichier.

Approche en 2 phases :
  Phase 1 : détection du type de projet + récupération du plan de fichiers
  Phase 2 : génération du contenu de chaque fichier dans un appel LLM séparé
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ollama
from config import BUILDER_MODEL, FILE_GEN_TEMPERATURE
from tools.file_ops import write_file, ensure_workspace
from orchestrator.project_types import detect_project_type, get_file_plan, get_project_description
from orchestrator.prompts import FILE_GEN_SYSTEM, FILE_GEN_USER_TEMPLATE, PROJECT_CONTEXTS


def run(task: str) -> dict:
    """
    Exécute l'agent Builder en mode fichier par fichier.

    Args:
        task: Description du projet à créer

    Returns:
        {
            "ok": bool,
            "files_written": [liste de chemins],
            "files_failed": [liste de chemins en erreur],
            "project_type": str,
            "summary": str
        }
    """
    print(f"\n[Builder] Tache recue : {task}")
    print(f"[Builder] Modele : {BUILDER_MODEL}")

    ensure_workspace()

    # --- Phase 1 : Détection du type de projet ---
    project_type  = detect_project_type(task)
    project_desc  = get_project_description(project_type)
    file_plan     = get_file_plan(project_type)
    project_ctx   = PROJECT_CONTEXTS.get(project_type, "")

    print(f"[Builder] Type de projet : {project_type}")
    print(f"[Builder] Fichiers a generer : {len(file_plan)}")

    # --- Phase 2 : Génération fichier par fichier ---
    files_written  = []
    files_failed   = []

    for i, file_entry in enumerate(file_plan, 1):
        file_path = file_entry["path"]
        file_desc = file_entry["desc"]

        print(f"\n[Builder] ({i}/{len(file_plan)}) Generation de : {file_path}")

        content = _generate_file(
            file_path       = file_path,
            file_desc       = file_desc,
            user_request    = task,
            project_type    = project_type,
            project_desc    = project_desc + "\n" + project_ctx,
            already_created = files_written,
        )

        if content is None:
            print(f"[Builder] ERREUR : generation echouee pour {file_path}")
            files_failed.append(file_path)
            continue

        result = write_file(file_path, content)
        if result["ok"]:
            files_written.append(file_path)
            print(f"[Builder] OK - Fichier ecrit : {file_path} ({len(content)} caracteres)")
        else:
            print(f"[Builder] ERREUR ecriture {file_path} : {result['error']}")
            files_failed.append(file_path)

    # --- Résumé ---
    total   = len(file_plan)
    success = len(files_written)
    failed  = len(files_failed)

    summary = (
        f"Projet '{project_type}' : {success}/{total} fichiers generes"
        + (f" ({failed} echecs : {', '.join(files_failed)})" if failed else "")
    )

    print(f"\n[Builder] {summary}")

    return {
        "ok": success > 0,
        "files_written": files_written,
        "files_failed": files_failed,
        "project_type": project_type,
        "summary": summary,
    }


def _generate_file(
    file_path: str,
    file_desc: str,
    user_request: str,
    project_type: str,
    project_desc: str,
    already_created: list[str],
) -> str | None:
    """
    Génère le contenu d'un seul fichier via un appel Ollama dédié.

    Retourne le contenu du fichier sous forme de string, ou None en cas d'erreur.
    """
    # Liste des fichiers déjà créés (pour donner du contexte au LLM)
    if already_created:
        created_str = "\n".join(f"  - {f}" for f in already_created)
    else:
        created_str = "  (aucun encore)"

    user_message = FILE_GEN_USER_TEMPLATE.format(
        project_description = project_desc,
        user_request        = user_request,
        project_type        = project_type,
        already_created     = created_str,
        file_path           = file_path,
        file_desc           = file_desc,
    )

    try:
        response = ollama.chat(
            model    = BUILDER_MODEL,
            messages = [
                {"role": "system", "content": FILE_GEN_SYSTEM},
                {"role": "user",   "content": user_message},
            ],
            options = {"temperature": FILE_GEN_TEMPERATURE},
        )
        content = response["message"]["content"].strip()

        # Nettoyage : retirer les backticks markdown si le LLM les a ajoutés
        content = _strip_markdown_fences(content)

        return content if content else None

    except Exception as e:
        print(f"[Builder] ERREUR Ollama pour {file_path} : {e}")
        return None


def _strip_markdown_fences(text: str) -> str:
    """
    Retire les blocs ```...``` ou ```python...``` que le LLM peut ajouter
    malgré les instructions.
    """
    import re
    # Retire la clôture ouvrante avec langage optionnel
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text.strip())
    # Retire la clôture fermante
    text = re.sub(r"\n?```$", "", text.strip())
    return text.strip()
