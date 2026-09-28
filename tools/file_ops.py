"""
tools/file_ops.py
Opérations sur le système de fichiers dans le workspace.
"""

import os
from pathlib import Path
from config import WORKSPACE_DIR


def _workspace_path(relative_path: str) -> Path:
    """Retourne le chemin absolu dans le workspace, en sécurisant le chemin."""
    base = Path(WORKSPACE_DIR).resolve()
    target = (base / relative_path).resolve()
    # Sécurité : on s'assure que le chemin reste dans le workspace
    if not str(target).startswith(str(base)):
        raise PermissionError(f"Accès refusé hors du workspace : {relative_path}")
    return target


def write_file(relative_path: str, content: str) -> dict:
    """
    Écrit un fichier dans le workspace.
    Crée les répertoires parents si nécessaire.
    Retourne {"ok": True, "path": chemin absolu} ou {"ok": False, "error": message}.
    """
    try:
        path = _workspace_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"ok": True, "path": str(path)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def read_file(relative_path: str) -> dict:
    """
    Lit un fichier dans le workspace.
    Retourne {"ok": True, "content": texte} ou {"ok": False, "error": message}.
    """
    try:
        path = _workspace_path(relative_path)
        content = path.read_text(encoding="utf-8")
        return {"ok": True, "content": content}
    except FileNotFoundError:
        return {"ok": False, "error": f"Fichier introuvable : {relative_path}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def list_files(relative_dir: str = "") -> dict:
    """
    Liste les fichiers d'un répertoire du workspace (récursif).
    Retourne {"ok": True, "files": [liste de chemins relatifs]} ou {"ok": False, "error": message}.
    """
    try:
        base = _workspace_path(relative_dir)
        if not base.exists():
            return {"ok": True, "files": []}
        files = [
            str(p.relative_to(Path(WORKSPACE_DIR).resolve()))
            for p in base.rglob("*")
            if p.is_file()
        ]
        return {"ok": True, "files": files}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def ensure_workspace() -> None:
    """Crée le dossier workspace s'il n'existe pas."""
    Path(WORKSPACE_DIR).mkdir(parents=True, exist_ok=True)
