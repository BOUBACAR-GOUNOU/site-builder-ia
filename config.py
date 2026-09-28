# =============================================================================
# Configuration centrale du projet site-builder-ia
# =============================================================================

# --- Ollama ---
OLLAMA_BASE_URL = "http://localhost:11434"

# --- Modèles ---
BUILDER_MODEL  = "qwen2.5-coder:0.5b"   # Agent Builder : génère les fichiers
DEPLOYER_MODEL = "qwen2.5:1.5b"          # Agent Deployer : raisonne sur Docker/logs
PLANNER_MODEL  = "qwen2.5:1.5b"          # Orchestrateur  : planifie les tâches

# --- Génération de fichiers ---
FILE_GEN_TEMPERATURE = 0.15              # Température basse pour du code cohérent
MAX_FILES_PER_BUILD  = 30               # Limite de sécurité : max fichiers par build


# --- Workspace ---
WORKSPACE_DIR  = "workspace"             # Dossier de travail des agents (relatif au projet)

# --- Déploiement Docker ---
COMPOSE_FILE   = "docker-compose.yml"    # Nom du fichier compose généré dans workspace/
SITE_PORT      = 8080                    # Port exposé par le conteneur du site
SITE_URL       = f"http://localhost:{SITE_PORT}"

# --- HTTP Check ---
HTTP_TIMEOUT   = 10                      # Secondes avant timeout lors de la vérification HTTP
HTTP_RETRIES   = 5                       # Nombre de tentatives avant d'abandonner
HTTP_WAIT      = 3                       # Secondes entre chaque tentative

# --- Orchestrateur ---
MAX_ITERATIONS = 3                       # Nombre max de boucles correction avant abandon
