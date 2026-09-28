"""
tools/docker_ops.py
Opérations Docker via le SDK Python.
Whitelist des commandes autorisées pour sécuriser l'exécution.
"""

import docker
import os
from pathlib import Path
from config import WORKSPACE_DIR, COMPOSE_FILE, SITE_PORT

# Commandes Docker autorisées (whitelist)
ALLOWED_OPERATIONS = {
    "build_image",
    "compose_up",
    "compose_down",
    "get_logs",
}


def _get_client() -> docker.DockerClient:
    """Crée et retourne un client Docker."""
    try:
        client = docker.from_env()
        client.ping()
        return client
    except Exception as e:
        raise ConnectionError(f"Docker non disponible : {e}")


def build_image(tag: str = "site-builder:latest") -> dict:
    """
    Construit une image Docker à partir du Dockerfile dans le workspace.
    Retourne {"ok": True, "image": tag} ou {"ok": False, "error": message, "logs": logs}.
    """
    try:
        client = _get_client()
        workspace = str(Path(WORKSPACE_DIR).resolve())
        print(f"[Docker] Build image '{tag}' depuis {workspace}...")
        image, build_logs = client.images.build(
            path=workspace,
            tag=tag,
            rm=True,
            forcerm=True,
        )
        logs = "\n".join(
            line.get("stream", "") for line in build_logs if "stream" in line
        )
        return {"ok": True, "image": tag, "logs": logs}
    except docker.errors.BuildError as e:
        return {"ok": False, "error": str(e), "logs": str(e.build_log)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def compose_up() -> dict:
    """
    Lance les conteneurs via docker-compose (docker SDK + subprocess fallback).
    Retourne {"ok": True, "message": ...} ou {"ok": False, "error": ..., "logs": ...}.
    """
    import subprocess
    workspace = str(Path(WORKSPACE_DIR).resolve())
    compose_path = os.path.join(workspace, COMPOSE_FILE)

    if not os.path.exists(compose_path):
        return {"ok": False, "error": f"docker-compose.yml introuvable dans {workspace}"}

    try:
        print(f"[Docker] Compose up depuis {workspace}...")
        result = subprocess.run(
            ["docker", "compose", "up", "-d", "--build"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            return {"ok": False, "error": "compose up a échoué", "logs": result.stderr}
        return {"ok": True, "message": "Conteneurs démarrés", "logs": result.stdout}
    except FileNotFoundError:
        return {"ok": False, "error": "Commande 'docker' introuvable. Docker est-il installé ?"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Timeout : docker compose up a pris trop de temps"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def compose_down() -> dict:
    """
    Arrête et supprime les conteneurs du workspace.
    Retourne {"ok": True} ou {"ok": False, "error": message}.
    """
    import subprocess
    workspace = str(Path(WORKSPACE_DIR).resolve())

    try:
        print("[Docker] Compose down...")
        result = subprocess.run(
            ["docker", "compose", "down", "--remove-orphans"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return {"ok": False, "error": result.stderr}
        return {"ok": True, "message": "Conteneurs arrêtés"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_logs(service: str = "") -> dict:
    """
    Récupère les logs du service Docker Compose.
    Retourne {"ok": True, "logs": texte} ou {"ok": False, "error": message}.
    """
    import subprocess
    workspace = str(Path(WORKSPACE_DIR).resolve())

    try:
        cmd = ["docker", "compose", "logs", "--tail=50"]
        if service:
            cmd.append(service)

        result = subprocess.run(
            cmd,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {"ok": True, "logs": result.stdout + result.stderr}
    except Exception as e:
        return {"ok": False, "error": str(e)}
