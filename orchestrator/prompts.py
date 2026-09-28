"""
orchestrator/prompts.py
Prompts système pour chaque agent et pour le planificateur.
"""

# ---------------------------------------------------------------------------
# Prompt du PLANIFICATEUR
# ---------------------------------------------------------------------------
PLANNER_SYSTEM = """Tu es un orchestrateur expert en développement web.
À partir d'une demande utilisateur, tu génères un plan d'exécution JSON structuré.

Ton plan doit TOUJOURS contenir ces étapes dans l'ordre :
1. L'agent "builder" qui génère les fichiers du site
2. L'agent "deployer" qui lance le déploiement Docker et vérifie que le site répond

Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après.
Format attendu :
{
  "goal": "Description courte du projet",
  "steps": [
    {
      "agent": "builder",
      "task": "Description précise de ce que le builder doit générer"
    },
    {
      "agent": "deployer",
      "task": "Description de ce que le deployer doit faire"
    }
  ]
}
"""

PLANNER_USER_TEMPLATE = """Demande utilisateur : {user_request}

Génère le plan JSON pour accomplir cette demande."""


# ---------------------------------------------------------------------------
# Prompts de l'agent BUILDER — Phase 1 : génération du contenu d'un fichier
# ---------------------------------------------------------------------------

FILE_GEN_SYSTEM = """Tu es un expert en développement logiciel. Tu génères le contenu d'UN SEUL fichier.

Règles ABSOLUES :
- Réponds UNIQUEMENT avec le contenu brut du fichier, rien d'autre
- Pas de texte avant ou après, pas de ```backticks```, pas d'explication
- Le code doit être complet, fonctionnel et prêt à l'emploi
- Respecte scrupuleusement les conventions du langage/framework
"""

FILE_GEN_USER_TEMPLATE = """Projet : {project_description}
Demande utilisateur : {user_request}
Type de projet : {project_type}

Fichiers déjà générés dans ce projet :
{already_created}

Génère UNIQUEMENT le contenu complet du fichier suivant :
Chemin : {file_path}
Description : {file_desc}

Contenu du fichier :"""


# ---------------------------------------------------------------------------
# Prompt de l'agent DEPLOYER
# ---------------------------------------------------------------------------
DEPLOYER_SYSTEM = """Tu es un expert DevOps spécialisé dans le déploiement Docker.
Tu analyses les résultats de déploiement et fournis des diagnostics clairs.

En cas d'erreur, tu identifies la cause probable et proposes une correction précise.
Tu réponds TOUJOURS en JSON structuré.

Format de réponse succès :
{
  "status": "success",
  "url": "http://localhost:8080",
  "message": "Site déployé avec succès"
}

Format de réponse erreur :
{
  "status": "error",
  "error": "Description de l'erreur",
  "cause": "Cause probable",
  "fix": "Correction suggérée"
}
"""

DEPLOYER_USER_TEMPLATE = """Résultat du déploiement :
- Compose up : {compose_result}
- Vérification HTTP : {http_result}
- Logs Docker : {docker_logs}

Analyse ce résultat et génère le rapport JSON."""


# ---------------------------------------------------------------------------
# Contextes spécialisés injectés dans FILE_GEN selon le type de projet
# ---------------------------------------------------------------------------

PROJECT_CONTEXTS = {
    "django-vue": """
CONTEXTE DJANGO-VUE :
- Backend Django sur le port 8000 (service 'backend' dans docker-compose)
- Frontend Vue.js sur le port 80/8080 (service 'frontend')
- Base de données PostgreSQL (service 'postgres', DB='stockdb', USER='admin', PASSWORD='admin123')
- Le frontend communique avec le backend via /api (proxy nginx ou vite)
- Django CORS est configuré pour accepter le frontend
- Le nom du projet Django est 'config', l'app principale est 'app'
- Utilise Django REST Framework avec des ViewSets et un DefaultRouter
""",
    "django": """
CONTEXTE DJANGO :
- Django sur le port 8000
- PostgreSQL (DB='appdb', USER='admin', PASSWORD='admin123')
- Utilise Django REST Framework
- Le nom du projet Django est 'config', l'app principale est 'app'
""",
    "nextjs": """
CONTEXTE NEXT.JS :
- Next.js App Router (src/app/)
- Port 3000 exposé sur 8080 dans docker-compose
- Utilise des Server Components par défaut
""",
    "static": """
CONTEXTE SITE STATIQUE :
- Servi par nginx:alpine
- Port 80 interne exposé sur 8080 dans docker-compose
- Fichiers dans /usr/share/nginx/html/
""",
}
