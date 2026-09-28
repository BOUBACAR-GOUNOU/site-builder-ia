# site-builder-ia

Un projet personnel que j'ai construit pour explorer les systèmes multi-agents appliqués au développement web.

L'idée : décrire un site en langage naturel, et laisser un pipeline d'agents IA tout gérer —
planifier la structure, générer les fichiers, et déployer le résultat localement via Docker.

---

## Ce que j'ai construit

J'ai conçu un orchestrateur qui coordonne deux agents spécialisés :

- **Builder** — prend une tâche en langage naturel et génère l'ensemble du site
- **Deployer** — prend ces fichiers, écrit un `docker-compose.yml` et lance le conteneur

Un **Planner** intervient en amont : il utilise un LLM local pour décomposer la demande de l'utilisateur
en étapes structurées avant de les transmettre aux agents.

Si un déploiement échoue, l'orchestrateur renvoie automatiquement l'erreur au Builder
et recommence — jusqu'à 3 tentatives.

Tout fonctionne en local avec [Ollama](https://ollama.ai) pour l'inférence et Docker pour le déploiement.
Pas de cloud, pas de clé API.

---

## Structure du projet

```
site-builder-ia/
├── orchestrator/
│   ├── main.py           # Point d'entrée & boucle de retry
│   ├── planner.py        # Planification des tâches via LLM
│   ├── project_types.py  # Types de sites supportés
│   └── prompts.py        # Prompts système
├── agents/
│   ├── builder.py        # Génère les fichiers du site
│   └── deployer.py       # Gère le déploiement Docker
├── tools/
│   ├── docker_ops.py     # Utilitaires Docker
│   ├── file_ops.py       # Lecture/écriture de fichiers
│   └── http_check.py     # Vérifie que le site est accessible
├── workspace/            # Dossier de travail des agents
├── config.py             # Toute la configuration au même endroit
└── requirements.txt
```

---

## Prérequis

- Python 3.10+
- [Ollama](https://ollama.ai) en cours d'exécution en local
- [Docker](https://www.docker.com) installé

---

## Installation

```bash
git clone https://github.com/votre-username/site-builder-ia.git
cd site-builder-ia

python -m venv venv
source venv/bin/activate  # Windows : venv\Scripts\activate
pip install -r requirements.txt

ollama pull qwen2.5-coder:0.5b
ollama pull qwen2.5:1.5b
```

---

## Utilisation

```bash
python orchestrator/main.py "crée un site web pour un restaurant italien"
python orchestrator/main.py "site portfolio pour un développeur web"
```


Pour arrêter les conteneurs :

```bash
python orchestrator/main.py --teardown
```

---

## Configuration

Définie dans `config.py` :

| Paramètre | Valeur par défaut | Description |
|---|---|---|
| `BUILDER_MODEL` | `qwen2.5-coder:0.5b` | Modèle pour la génération de fichiers |
| `DEPLOYER_MODEL` | `qwen2.5:1.5b` | Modèle pour le raisonnement Docker |
| `PLANNER_MODEL` | `qwen2.5:1.5b` | Modèle pour la planification |
| `SITE_PORT` | `8080` | Port exposé |
| `MAX_ITERATIONS` | `3` | Tentatives max en cas d'échec |
| `MAX_FILES_PER_BUILD` | `30` | Nombre max de fichiers générés par build |

---
