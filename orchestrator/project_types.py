"""
orchestrator/project_types.py
Détecte le type de projet à partir de la demande utilisateur
et fournit la structure de fichiers + le contexte adapté.
"""

import re

# =============================================================================
# Définition des types de projets
# =============================================================================

PROJECT_TYPES = {

    "django-vue": {
        "keywords": ["django", "vue", "vuejs", "vue.js", "django rest", "drf"],
        "description": "Application Django REST Framework + Vue.js + base de données",
        "file_plan": [
            {"path": "docker-compose.yml",              "desc": "3 services : backend Django, frontend Vue, postgres"},
            {"path": "backend/requirements.txt",         "desc": "Django, djangorestframework, psycopg2, django-cors-headers"},
            {"path": "backend/Dockerfile",               "desc": "Image Python 3.11, installe requirements, lance gunicorn"},
            {"path": "backend/manage.py",                "desc": "Script de gestion Django standard"},
            {"path": "backend/config/settings.py",       "desc": "Settings Django : DB postgres, CORS, REST_FRAMEWORK, INSTALLED_APPS"},
            {"path": "backend/config/urls.py",           "desc": "URLs racine : inclut les urls de l'app"},
            {"path": "backend/config/wsgi.py",           "desc": "WSGI standard pour Django"},
            {"path": "backend/config/__init__.py",       "desc": "Fichier vide"},
            {"path": "backend/app/__init__.py",          "desc": "Fichier vide"},
            {"path": "backend/app/models.py",            "desc": "Modèles Django selon la demande utilisateur"},
            {"path": "backend/app/serializers.py",       "desc": "Serializers DRF pour chaque modèle"},
            {"path": "backend/app/views.py",             "desc": "ViewSets DRF avec CRUD complet"},
            {"path": "backend/app/urls.py",              "desc": "Router DRF enregistrant tous les ViewSets"},
            {"path": "backend/app/admin.py",             "desc": "Enregistre les modèles dans l'admin Django"},
            {"path": "frontend/Dockerfile",              "desc": "Image node:20-alpine, npm install, npm run build, nginx"},
            {"path": "frontend/package.json",            "desc": "Vue 3 + vite + axios + vue-router"},
            {"path": "frontend/vite.config.js",          "desc": "Vite config avec proxy /api vers backend:8000"},
            {"path": "frontend/index.html",              "desc": "HTML racine qui charge main.js"},
            {"path": "frontend/src/main.js",             "desc": "Point d'entrée Vue : createApp, router, mount"},
            {"path": "frontend/src/App.vue",             "desc": "Composant racine avec nav et router-view"},
            {"path": "frontend/src/router/index.js",     "desc": "Vue Router avec les routes de l'application"},
            {"path": "frontend/src/api/index.js",        "desc": "Client axios configuré avec baseURL /api"},
            {"path": "frontend/src/views/HomeView.vue",  "desc": "Vue liste principale avec tableau des données"},
            {"path": "frontend/src/views/FormView.vue",  "desc": "Formulaire création/édition"},
            {"path": "frontend/nginx.conf",              "desc": "Config nginx pour servir le build Vue et proxy /api"},
        ],
    },

    "django": {
        "keywords": ["django", "python web", "django rest"],
        "description": "Application Django REST Framework",
        "file_plan": [
            {"path": "docker-compose.yml",          "desc": "2 services : backend Django, postgres"},
            {"path": "requirements.txt",             "desc": "Django, djangorestframework, psycopg2"},
            {"path": "Dockerfile",                   "desc": "Image Python 3.11, requirements, gunicorn"},
            {"path": "manage.py",                    "desc": "Script de gestion Django standard"},
            {"path": "config/settings.py",           "desc": "Settings Django avec PostgreSQL"},
            {"path": "config/urls.py",               "desc": "URLs racine Django"},
            {"path": "config/wsgi.py",               "desc": "WSGI standard"},
            {"path": "config/__init__.py",           "desc": "Fichier vide"},
            {"path": "app/__init__.py",              "desc": "Fichier vide"},
            {"path": "app/models.py",                "desc": "Modèles selon la demande"},
            {"path": "app/serializers.py",           "desc": "Serializers DRF"},
            {"path": "app/views.py",                 "desc": "ViewSets DRF"},
            {"path": "app/urls.py",                  "desc": "Router DRF"},
            {"path": "app/admin.py",                 "desc": "Admin Django"},
        ],
    },

    "nextjs": {
        "keywords": ["next", "nextjs", "next.js", "react", "ssr"],
        "description": "Application Next.js",
        "file_plan": [
            {"path": "docker-compose.yml",           "desc": "Service Next.js"},
            {"path": "Dockerfile",                   "desc": "Image node:20-alpine, build Next.js"},
            {"path": "package.json",                 "desc": "Next.js, react, react-dom"},
            {"path": "next.config.js",               "desc": "Config Next.js"},
            {"path": "src/app/layout.js",            "desc": "Layout racine Next.js"},
            {"path": "src/app/page.js",              "desc": "Page d'accueil"},
            {"path": "src/app/globals.css",          "desc": "Styles globaux"},
        ],
    },

    "static": {
        "keywords": [],  # fallback par défaut
        "description": "Site web statique HTML/CSS/JS",
        "file_plan": [
            {"path": "Dockerfile",          "desc": "nginx:alpine servant les fichiers statiques"},
            {"path": "docker-compose.yml",  "desc": "Service nginx sur le port 8080"},
            {"path": "index.html",          "desc": "Page principale complète et moderne"},
            {"path": "style.css",           "desc": "Styles CSS modernes et responsives"},
        ],
    },
}

# =============================================================================
# Détection du type
# =============================================================================

def detect_project_type(user_request: str) -> str:
    """
    Détecte le type de projet à partir de la demande utilisateur.
    Retourne une clé de PROJECT_TYPES.
    """
    request_lower = user_request.lower()

    # Ordre de priorité : du plus spécifique au plus générique
    priority = ["django-vue", "django", "nextjs", "static"]

    for ptype in priority:
        keywords = PROJECT_TYPES[ptype]["keywords"]
        if any(kw in request_lower for kw in keywords):
            print(f"[ProjectTypes] Type detecte : '{ptype}'")
            return ptype

    print("[ProjectTypes] Type detecte : 'static' (defaut)")
    return "static"


def get_file_plan(project_type: str) -> list[dict]:
    """Retourne la liste de fichiers à générer pour ce type de projet."""
    return PROJECT_TYPES.get(project_type, PROJECT_TYPES["static"])["file_plan"]


def get_project_description(project_type: str) -> str:
    """Retourne la description du type de projet."""
    return PROJECT_TYPES.get(project_type, PROJECT_TYPES["static"])["description"]
