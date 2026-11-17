# Bookly API

API REST de gestion de livres et d'avis, construite avec FastAPI. Le projet
propose l'authentification JWT, des rôles utilisateur, une base PostgreSQL, des
erreurs HTTP centralisées et l'envoi d'e-mails en arrière-plan avec Celery et
Redis.

## Fonctionnalités

- Création de comptes et connexion avec jetons JWT.
- Gestion des livres appartenant à l'utilisateur connecté.
- Création, consultation et suppression d'avis.
- Contrôle d'accès par rôle et par propriétaire.
- Documentation interactive OpenAPI générée par FastAPI.
- Envoi d'e-mails via un worker Celery.
- Gestion centralisée des erreurs et journalisation des requêtes.

## Technologies

- Python 3.14+
- FastAPI, Pydantic et SQLModel / SQLAlchemy
- PostgreSQL avec `asyncpg`
- Alembic pour les migrations
- Redis pour la révocation des jetons et le broker Celery
- Celery et FastAPI-Mail pour les e-mails asynchrones
- pytest, pytest-asyncio et HTTPX pour les tests
- uv pour gérer l'environnement et les dépendances

## Prérequis

Installer Python 3.14 ou plus récent et [uv](https://docs.astral.sh/uv/). Pour
l'exécution complète, il faut aussi disposer d'un serveur PostgreSQL, d'un serveur
Redis et d'un compte SMTP. Les tests automatisés simulent ces services et ne
nécessitent pas de connexion à des services externes.

## Installation

Depuis la racine du dépôt :

```powershell
uv sync
```

Le fichier `uv.lock` est versionné pour conserver les versions de dépendances
résolues. Pour le mettre à jour après un changement de dépendances, utiliser `uv
lock` plutôt que de le modifier manuellement.

## Configuration

Créer un fichier `.env` à la racine du projet. Exemple avec des valeurs fictives :

```env
DATABASE_URL=postgresql+asyncpg://bookly:change-me@localhost:5432/bookly
JWT_SECRET=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
REFRESH_TOKEN_EXPIRY_DAYS=7
REDIS_URL=redis://localhost:6379/0

MAIL_USERNAME=your-smtp-username
MAIL_PASSWORD=your-smtp-password
MAIL_FROM=no-reply@example.com
MAIL_PORT=587
MAIL_SERVER=smtp.example.com
MAIL_FROM_NAME=Bookly
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
USE_CREDENTIALS=true
VALIDATE_CERTS=true
DOMAIN=example.com

# Facultatif : par défaut, Celery utilise REDIS_URL.
# CELERY_BROKER_URL=redis://localhost:6379/1
```

Remplacer les exemples par les valeurs de votre environnement. `JWT_ALGORITHM`
est limité à `HS256` par la configuration actuelle. Ne publiez jamais `.env` ou
de véritables secrets. Le `.gitignore` du projet exclut `.env` et ses variantes.

## Base de données

Les scripts de migration sont dans `migrations/`. Avec une configuration valide
et une base PostgreSQL accessible, appliquer les migrations avec :

```powershell
uv run alembic upgrade head
```

L'application appelle également `SQLModel.metadata.create_all()` pendant son
démarrage. Pour le développement, cela permet de créer les tables absentes; pour
faire évoluer un schéma existant, utiliser et vérifier les migrations Alembic.

## Lancement en développement

Démarrer PostgreSQL et Redis, puis lancer l'API depuis la racine :

```powershell
uv run uvicorn main:app --reload
```

La documentation interactive est disponible à
[`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs), et la documentation
ReDoc à [`http://127.0.0.1:8000/redoc`](http://127.0.0.1:8000/redoc).

### Worker Celery

Pour traiter l'envoi d'e-mails, lancer le worker dans un autre terminal :

```powershell
uv run celery -A src.celery_app:celery_app worker --loglevel=INFO --pool=solo
```

Le pool `solo` convient au développement sous Windows. En production, exécuter
l'API et le worker comme services séparés et utiliser un déploiement adapté à
l'environnement cible.

## Routes principales

Toutes les routes sont préfixées par `/api/v1`.

| Méthode | Route | Description | Accès |
| --- | --- | --- | --- |
| `POST` | `/auth/signup` | Créer un compte | Public |
| `POST` | `/auth/login` | Se connecter et obtenir les jetons | Public |
| `POST` | `/auth/logout` | Révoquer le jeton d'accès | Authentifié |
| `GET` | `/auth/me` | Obtenir le profil de l'utilisateur | Authentifié |
| `POST` | `/auth/send_mail` | Mettre des e-mails dans la file Celery | Administrateur |
| `GET` | `/books/` | Lister les livres de l'utilisateur | Authentifié |
| `POST` | `/books/` | Créer un livre | Authentifié |
| `GET` | `/books/book/{book_uid}` | Consulter un livre | Authentifié |
| `PATCH` | `/books/{book_uid}` | Modifier un livre | Authentifié |
| `DELETE` | `/books/{book_uid}` | Supprimer un livre | Authentifié |
| `GET` | `/reviews/` | Lister tous les avis | Administrateur |
| `GET` | `/reviews/{review_uid}` | Consulter un avis | Utilisateur ou administrateur |
| `POST` | `/reviews/book/{book_uid}` | Ajouter un avis à un livre | Utilisateur ou administrateur |
| `DELETE` | `/reviews/{review_uid}` | Supprimer son avis | Auteur de l'avis |

Les routes authentifiées nécessitent un jeton Bearer. La route d'e-mail renvoie
`202 Accepted` avec un `task_id` lorsque la tâche a été mise en file; cela ne
signifie pas que le message a déjà été livré. La tâche peut être relancée par
Celery en cas d'erreur SMTP.

Exemple de corps pour `/api/v1/auth/send_mail` :

```json
{
  "addresses": ["destinataire@example.com"]
}
```

## Tests

Lancer la suite automatisée :

```powershell
uv run pytest -q
```

Les tests couvrent les routes d'authentification, les livres et avis, les erreurs,
le middleware et la tâche d'e-mail. Les dépendances externes sont remplacées par
des mocks; les tests n'envoient donc pas de vrais e-mails et ne nécessitent pas
PostgreSQL ou Redis en fonctionnement.

## Structure du projet

```text
.
├── main.py                 # point d'entrée ASGI
├── migrations/             # migrations Alembic
├── src/
│   ├── auth/               # authentification et comptes
│   ├── books/              # livres
│   ├── reviews/            # avis
│   ├── db/                 # base de données et Redis
│   ├── celery_app.py       # configuration du worker Celery
│   ├── celery_tasks.py     # tâches d'arrière-plan
│   ├── email.py            # configuration et messages SMTP
│   ├── errors.py           # exceptions et handlers HTTP
│   └── middleware.py       # journalisation HTTP
└── tests/
    ├── api/
    ├── tasks/
    └── unit/
```

## Licence

Aucune licence n'est spécifiée pour le moment. Ajouter un fichier `LICENSE`
approprié avant de distribuer ou de réutiliser publiquement ce projet.
